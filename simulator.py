"""
Monte Carlo simulation engine for Monopoly
Runs multiple game simulations and tracks property-specific outcomes
"""
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from properties import load_board
from game_state import create_game, GameState, Player
from mechanics import GameMechanics
from strategies import get_strategy
import copy

@dataclass
class PropertyTracker:
    """Tracks cash flows for a specific property"""
    position: int
    property_name: str
    purchase_turn: int = -1  # Turn when property was purchased
    purchase_price: float = 0
    total_rent_collected: float = 0
    total_rent_paid: float = 0
    rent_events: List[Tuple[int, float]] = field(default_factory=list)  # (turn, amount)
    was_purchased: bool = False
    owner_name: str = ""


@dataclass
class SimulationResult:
    """Results from a single simulation"""
    turns_played: int
    property_purchased: bool
    purchase_turn: int
    purchase_price: float
    total_rent_collected: float
    total_rent_paid: float
    rent_by_turn: Dict[int, float]  # turn -> cumulative rent
    break_even_turn: int  # -1 if never broke even
    final_player_cash: float
    player_won: bool
    player_bankrupt: bool


class MonopolySimulator:
    """Run Monte Carlo simulations of Monopoly games"""
    
    def __init__(self, board=None):
        self.board = board or load_board()
    
    def run_single_simulation(self,
                             target_player_idx: int,
                             target_property_position: int,
                             player_configs: List[Dict],
                             max_turns: int = 100,
                             purchase_target: bool = True,
                             enable_house_building: bool = False) -> SimulationResult:
        """
        Run a single game simulation
        
        Args:
            target_player_idx: Index of the player we're analyzing
            target_property_position: Property position to track
            player_configs: Initial player configurations
            max_turns: Maximum turns to simulate
            purchase_target: If True, force target player to buy target property when landing
        
        Returns:
            SimulationResult with tracked metrics
        """
        # Create game
        game = create_game(self.board, player_configs)
        mechanics = GameMechanics(game, enable_house_building=enable_house_building)
        
        # Property tracker
        tracker = PropertyTracker(
            position=target_property_position,
            property_name=self.board.get_property(target_property_position).name
        )
        
        # Track rent by turn
        rent_by_turn = {}
        cumulative_rent = 0
        
        # Run simulation
        turn = 0
        while turn < max_turns and not game.is_game_over():
            current_player = game.get_current_player()
            player_idx = game.current_player_idx
            
            # Get strategy for this player
            base_strategy = get_strategy(current_player.risk_tolerance)
            
            # Override strategy if this is target player landing on target property
            if player_idx == target_player_idx and purchase_target:
                def target_strategy(game, player, position):
                    if position == target_property_position:
                        return True  # Always buy target property
                    return base_strategy(game, player, position)
                strategy_func = target_strategy
            else:
                strategy_func = base_strategy
            
            # Take turn
            events = mechanics.take_turn(current_player, strategy_func)
            
            # Track events
            for event in events:
                if event['event'] == 'purchase' and event.get('success'):
                    if event['position'] == target_property_position:
                        tracker.was_purchased = True
                        tracker.purchase_turn = turn
                        tracker.purchase_price = -event['amount']
                        tracker.owner_name = current_player.name
                
                elif event['event'] == 'landing' and event['action'] == 'pay_rent':
                    if event['position'] == target_property_position:
                        rent_amount = -event['amount']
                        
                        # Check who paid/received
                        if player_idx == target_player_idx:
                            # Target player paid rent
                            tracker.total_rent_paid += rent_amount
                        else:
                            # Someone else paid rent to target property owner
                            owner = game.get_property_owner(target_property_position)
                            if owner and game.players.index(owner) == target_player_idx:
                                # Target player collected rent
                                tracker.total_rent_collected += rent_amount
                                tracker.rent_events.append((turn, rent_amount))
                                cumulative_rent += rent_amount
            
            # Track cumulative rent by turn
            rent_by_turn[turn] = cumulative_rent - tracker.purchase_price if tracker.was_purchased else 0
            
            game.next_player()
            turn += 1
        
        # Calculate break-even turn
        break_even_turn = -1
        if tracker.was_purchased:
            for t, cum_rent in rent_by_turn.items():
                if t > tracker.purchase_turn and cum_rent >= 0:
                    break_even_turn = t
                    break
        
        # Get final state
        target_player = game.players[target_player_idx]
        winner = game.get_winner()
        
        return SimulationResult(
            turns_played=turn,
            property_purchased=tracker.was_purchased,
            purchase_turn=tracker.purchase_turn,
            purchase_price=tracker.purchase_price,
            total_rent_collected=tracker.total_rent_collected,
            total_rent_paid=tracker.total_rent_paid,
            rent_by_turn=rent_by_turn,
            break_even_turn=break_even_turn,
            final_player_cash=target_player.cash,
            player_won=(winner == target_player) if winner else False,
            player_bankrupt=target_player.is_bankrupt
        )
    
    def run_monte_carlo(self,
                       target_player_idx: int,
                       target_property_position: int,
                       player_configs: List[Dict],
                       num_simulations: int = 1000,
                       max_turns: int = 100,
                       enable_house_building: bool = False) -> Dict:
        """
        Run Monte Carlo simulations
        
        Returns aggregated statistics
        """
        results = []
        
        print(f"Running {num_simulations} simulations...")
        
        for i in range(num_simulations):
            if (i + 1) % 100 == 0:
                print(f"  Completed {i + 1}/{num_simulations}")
            
            result = self.run_single_simulation(
                target_player_idx,
                target_property_position,
                player_configs,
                max_turns,
                purchase_target=True,
                enable_house_building=enable_house_building
            )
            results.append(result)
        
        # Aggregate results
        return self._aggregate_results(results, target_property_position)
    
    def _aggregate_results(self, results: List[SimulationResult], position: int) -> Dict:
        """Aggregate simulation results into statistics"""
        prop = self.board.get_property(position)
        
        # Filter to games where property was purchased
        purchased_results = [r for r in results if r.property_purchased]
        
        if not purchased_results:
            return {
                'property_name': prop.name,
                'property_price': prop.purchase_price,
                'purchase_rate': 0,
                'error': 'Property never purchased in simulations'
            }
        
        # Break-even analysis
        break_even_turns = [r.break_even_turn for r in purchased_results 
                           if r.break_even_turn > 0]
        
        # Rent collection by turn
        max_turn = max(r.turns_played for r in purchased_results)
        rent_by_turn_matrix = []
        
        for r in purchased_results:
            turn_rents = []
            for t in range(max_turn + 1):
                turn_rents.append(r.rent_by_turn.get(t, 0))
            rent_by_turn_matrix.append(turn_rents)
        
        rent_by_turn_array = np.array(rent_by_turn_matrix)
        
        # Calculate statistics
        stats = {
            'property_name': prop.name,
            'property_position': position,
            'property_price': prop.purchase_price,
            'num_simulations': len(results),
            'purchase_rate': len(purchased_results) / len(results),
            
            # Break-even statistics
            'break_even_mean': np.mean(break_even_turns) if break_even_turns else -1,
            'break_even_median': np.median(break_even_turns) if break_even_turns else -1,
            'break_even_std': np.std(break_even_turns) if break_even_turns else 0,
            'break_even_distribution': break_even_turns,
            'break_even_rate': len(break_even_turns) / len(purchased_results),
            
            # Rent statistics
            'total_rent_mean': np.mean([r.total_rent_collected for r in purchased_results]),
            'total_rent_median': np.median([r.total_rent_collected for r in purchased_results]),
            'total_rent_std': np.std([r.total_rent_collected for r in purchased_results]),
            
            # Cash flow by turn (mean and confidence intervals)
            'rent_by_turn_mean': np.mean(rent_by_turn_array, axis=0),
            'rent_by_turn_std': np.std(rent_by_turn_array, axis=0),
            'rent_by_turn_p25': np.percentile(rent_by_turn_array, 25, axis=0),
            'rent_by_turn_p75': np.percentile(rent_by_turn_array, 75, axis=0),
            
            # Win rate
            'win_rate': np.mean([r.player_won for r in purchased_results]),
            'bankruptcy_rate': np.mean([r.player_bankrupt for r in purchased_results]),
            
            # Final cash
            'final_cash_mean': np.mean([r.final_player_cash for r in purchased_results]),
        }
        
        return stats


# Test the simulator
if __name__ == '__main__':
    print("Testing Monopoly Simulator\n")
    print("="*60)
    
    # Define test scenario
    player_configs = [
        {
            'name': 'You',
            'cash': 3500,
            'position': 20,  # Start at Free Parking, will land on NC Ave soon
            'owned_properties': [31],  # Own Pacific Avenue
            'risk_tolerance': 0.6
        },
        {
            'name': 'Player 2',
            'cash': 1800,
            'position': 5,
            'owned_properties': [1, 3],
            'risk_tolerance': 0.3
        },
        {
            'name': 'Player 3',
            'cash': 2200,
            'position': 10,
            'owned_properties': [5, 15],
            'risk_tolerance': 0.5
        }
    ]
    
    simulator = MonopolySimulator()
    
    # Run a few simulations to test
    print("\nRunning test simulation (100 games)...")
    results = simulator.run_monte_carlo(
        target_player_idx=0,
        target_property_position=32,  # North Carolina Avenue
        player_configs=player_configs,
        num_simulations=100,
        max_turns=80
    )
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\nProperty: {results['property_name']}")
    print(f"Purchase Price: ${results['property_price']:.0f}")
    print(f"\nBreak-Even Analysis:")
    print(f"  Mean: {results['break_even_mean']:.1f} turns")
    print(f"  Median: {results['break_even_median']:.1f} turns")
    print(f"  Break-even rate: {results['break_even_rate']:.1%}")
    print(f"\nRent Collection:")
    print(f"  Mean total: ${results['total_rent_mean']:.0f}")
    print(f"  Median total: ${results['total_rent_median']:.0f}")
    print(f"\nGame Outcomes:")
    print(f"  Win rate: {results['win_rate']:.1%}")
    print(f"  Bankruptcy rate: {results['bankruptcy_rate']:.1%}")
