"""
House Building Engine - Optimal property development using analytical expected value
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from properties import MonopolyBoard
from game_state import Player, GameState

@dataclass
class DevelopmentOption:
    """Represents a potential house/hotel purchase"""
    property_positions: List[int]  # Can be multiple for group builds
    property_name: str
    color_group: str
    current_houses: int
    new_houses: int
    cost: float
    rent_increase: float
    expected_value: float
    ev_per_dollar: float
    is_hotel: bool
    description: str


class HouseBuildingEngine:
    """Decides optimal house building strategy using analytical expected value"""
    
    def __init__(self, board: MonopolyBoard):
        self.board = board
        # Pre-calculate landing probabilities (one-time cost)
        self.landing_probs = self._calculate_landing_probabilities()
    
    def decide_development(self, 
                          player: Player, 
                          game_state: GameState,
                          estimated_remaining_turns: int = 50) -> List[DevelopmentOption]:
        """
        Determine optimal house building strategy
        
        Args:
            player: The player making development decisions
            game_state: Current game state
            estimated_remaining_turns: How many turns we expect the game to last
        
        Returns:
            List of DevelopmentOptions to execute, in priority order
        """
        # 1. Find player's monopolies
        monopolies = self._get_player_monopolies(player, game_state)
        
        if not monopolies:
            return []  # No monopolies, can't build
        
        # 2. Calculate available budget
        available_cash = player.cash - player.min_cash_reserve
        if available_cash < 50:  # Minimum house cost
            return []
        
        # 3. Generate all possible development options
        options = self._generate_development_options(player, monopolies, game_state)
        
        if not options:
            return []
        
        # 4. Calculate Expected Value for each option
        num_opponents = len([p for p in game_state.players if not p.is_bankrupt and p != player])
        
        for option in options:
            option.expected_value = self._calculate_expected_value(
                option,
                estimated_remaining_turns,
                num_opponents
            )
            option.ev_per_dollar = option.expected_value / option.cost if option.cost > 0 else 0
        
        # 5. Apply strategic preferences
        self._apply_strategic_preferences(options, player)
        
        # 6. Greedy selection: Pick best ROI options within budget
        selected = self._greedy_selection(options, available_cash)
        
        return selected
    
    def _get_player_monopolies(self, player: Player, game_state: GameState) -> Dict[str, List[int]]:
        """Find which color groups the player has monopolies in"""
        monopolies = {}
        
        for color, positions in self.board.color_groups.items():
            # Check if player owns all properties in this color group
            if all(player.owns_property(pos) for pos in positions):
                monopolies[color] = positions
        
        return monopolies
    
    def _calculate_landing_probabilities(self) -> Dict[int, float]:
        """
        Calculate landing probabilities for all board positions
        
        Based on:
        - Dice distribution (2d6, peak at 7)
        - Jail effect (boosts Orange properties significantly)
        - Strategic position effects
        """
        probs = {}
        
        # Base probability (if board were uniform)
        base_prob = 1.0 / 40  # 2.5%
        
        for pos in range(40):
            prop = self.board.get_property(pos)
            
            # Orange properties (16-19) get significant boost from Jail at position 10
            # Players leaving jail (positions 10) most commonly land on 16-19
            if 16 <= pos <= 19:
                probs[pos] = base_prob * 1.25  # 25% boost
            
            # Red properties also benefit slightly
            elif 21 <= pos <= 24:
                probs[pos] = base_prob * 1.10
            
            # Railroads are strategically positioned
            elif pos in [5, 15, 25, 35]:
                probs[pos] = base_prob * 1.05
            
            # Go To Jail (position 30) - never landed on, always sent to Jail
            elif pos == 30:
                probs[pos] = 0.0
            
            # Jail (position 10) - higher probability (people sent here)
            elif pos == 10:
                probs[pos] = base_prob * 1.5
            
            else:
                probs[pos] = base_prob
        
        # Normalize so probabilities sum to 1.0
        total = sum(probs.values())
        return {k: v/total for k, v in probs.items()}
    
    def _generate_development_options(self, 
                                     player: Player, 
                                     monopolies: Dict[str, List[int]],
                                     game_state: GameState) -> List[DevelopmentOption]:
        """
        Generate all valid development options
        Respects Monopoly's even-building rule
        """
        options = []
        
        for color, positions in monopolies.items():
            # Get current development state for this color group
            current_houses = [player.houses.get(pos, 0) for pos in positions]
            min_houses = min(current_houses)
            max_houses = max(current_houses)
            
            # Even building rule: Can only build where you have the minimum
            # Can't build if already at hotel level (5)
            if min_houses >= 5:
                continue
            
            # Option: Build one house on each minimally-developed property
            properties_to_build = [pos for pos in positions 
                                  if player.houses.get(pos, 0) == min_houses]
            
            for pos in properties_to_build:
                prop = self.board.get_property(pos)
                
                # Determine cost (houses vs hotel)
                if min_houses < 4:
                    cost = prop.house_cost
                    is_hotel = False
                else:  # Building 5th house = hotel
                    cost = prop.house_cost  # Hotel costs same as house in standard rules
                    is_hotel = True
                
                # Calculate rent increase
                old_rent = prop.get_rent(has_monopoly=True, houses=min_houses)
                new_rent = prop.get_rent(has_monopoly=True, houses=min_houses + 1)
                rent_increase = new_rent - old_rent
                
                house_word = "hotel" if is_hotel else "house"
                
                option = DevelopmentOption(
                    property_positions=[pos],
                    property_name=prop.name,
                    color_group=color,
                    current_houses=min_houses,
                    new_houses=min_houses + 1,
                    cost=cost,
                    rent_increase=rent_increase,
                    expected_value=0,  # Calculated later
                    ev_per_dollar=0,  # Calculated later
                    is_hotel=is_hotel,
                    description=f"Build {house_word} on {prop.name} (${new_rent} rent)"
                )
                options.append(option)
        
        return options
    
    def _calculate_expected_value(self,
                                  option: DevelopmentOption,
                                  remaining_turns: int,
                                  num_opponents: int) -> float:
        """
        Calculate Expected Value for a development option
        
        EV = Rent_Increase × Landing_Probability × Remaining_Turns × Num_Opponents
        
        This is the key metric: how much additional rent we expect to collect
        from this investment over the remaining game
        """
        property_pos = option.property_positions[0]  # Primary property
        
        # Get landing probability for this property
        landing_prob = self.landing_probs.get(property_pos, 1.0/40)
        
        # Expected value calculation
        # Each opponent has landing_prob chance of landing each turn
        expected_landings = landing_prob * remaining_turns * num_opponents
        
        # Expected additional rent from this development
        ev = option.rent_increase * expected_landings
        
        return ev
    
    def _apply_strategic_preferences(self, options: List[DevelopmentOption], player: Player):
        """
        Apply strategic preferences to boost/penalize certain options
        Modifies ev_per_dollar based on strategic factors
        """
        for option in options:
            multiplier = 1.0
            
            # Preference 1: Hotels are highly desirable (finish what you started)
            if option.is_hotel:
                multiplier *= 1.3
            
            # Preference 2: Orange properties are the best (high traffic from Jail)
            if option.color_group == 'Orange':
                multiplier *= 1.2
            
            # Preference 3: Red and Yellow are also good
            elif option.color_group in ['Red', 'Yellow']:
                multiplier *= 1.1
            
            # Preference 4: Early development (first house) is valuable for monopoly rent doubling
            if option.current_houses == 0:
                multiplier *= 1.15  # Going from base to monopoly is big jump
            
            # Preference 5: Risk-based adjustments
            if player.risk_tolerance > 0.7:  # Aggressive players
                # Prefer high-rent properties even if expensive
                if option.cost > 150:
                    multiplier *= 1.1
            elif player.risk_tolerance < 0.4:  # Conservative players
                # Prefer cheaper developments
                if option.cost < 100:
                    multiplier *= 1.1
            
            # Apply multiplier
            option.ev_per_dollar *= multiplier
    
    def _greedy_selection(self, 
                         options: List[DevelopmentOption],
                         available_cash: float) -> List[DevelopmentOption]:
        """
        Greedy algorithm: Select developments with highest EV per dollar within budget
        """
        # Sort by EV per dollar (descending)
        sorted_options = sorted(options, key=lambda x: x.ev_per_dollar, reverse=True)
        
        selected = []
        spent = 0.0
        
        for option in sorted_options:
            # Check if we can afford this
            if spent + option.cost > available_cash:
                continue
            
            # Check for conflicts (can't build on same property twice)
            conflict = False
            for pos in option.property_positions:
                if any(pos in sel.property_positions for sel in selected):
                    conflict = True
                    break
            
            if conflict:
                continue
            
            # Add to selection
            selected.append(option)
            spent += option.cost
            
            # Safety: Don't overspend
            if spent >= available_cash * 0.95:  # Leave small buffer
                break
        
        return selected


def estimate_remaining_turns(game_state: GameState) -> int:
    """
    Estimate how many turns remain in the game
    
    Based on:
    - Current turn number
    - Property ownership distribution
    - Player cash levels
    """
    current_turn = game_state.total_turns
    
    # Base expectation: Games typically go 150-200 turns with development
    avg_game_length = 180
    
    # Adjust based on game state
    active_players = game_state.get_active_players()
    
    if len(active_players) <= 2:
        # Down to 2 players, game likely to end soon
        avg_game_length = min(avg_game_length, current_turn + 50)
    
    # If someone is dominating (owns many properties), they'll build houses
    # and win faster
    max_properties = max((p.get_total_properties() for p in active_players), default=0)
    if max_properties > 20:
        avg_game_length = min(avg_game_length, current_turn + 40)
    elif max_properties > 15:
        avg_game_length = min(avg_game_length, current_turn + 60)
    
    # Early game: Be optimistic about game length
    if current_turn < 30:
        remaining = avg_game_length - current_turn
    else:
        # Mid/late game: More conservative
        remaining = max(20, avg_game_length - current_turn)
    
    # Always estimate at least some remaining turns for development to pay off
    remaining = max(30, remaining)  # At least 30 turns for houses to be worthwhile
    
    return remaining


# Test the module
if __name__ == '__main__':
    from properties import load_board
    from game_state import create_game
    
    print("Testing House Building Engine\n")
    print("="*70)
    
    board = load_board()
    
    # Create test scenario: Player owns Green monopoly
    player_configs = [
        {
            'name': 'You',
            'cash': 2000,
            'position': 20,
            'owned_properties': [31, 32, 34],  # Complete Green monopoly!
            'risk_tolerance': 0.6
        },
        {
            'name': 'Opponent',
            'cash': 1500,
            'position': 10,
            'owned_properties': [1, 3],
            'risk_tolerance': 0.5
        }
    ]
    
    game = create_game(board, player_configs)
    player = game.players[0]
    
    # Initialize houses (player starts with no houses)
    for pos in player.owned_properties:
        player.houses[pos] = 0
    
    print("Test Scenario:")
    print(f"  Player: {player.name}")
    print(f"  Cash: ${player.cash}")
    print(f"  Properties: {[board.get_property(p).name for p in player.owned_properties]}")
    print(f"  Monopolies: Green (complete!)")
    
    # Create house building engine
    builder = HouseBuildingEngine(board)
    
    print("\n" + "="*70)
    print("DEVELOPMENT ANALYSIS")
    print("="*70)
    
    # Get development recommendations
    remaining_turns = estimate_remaining_turns(game)
    options = builder.decide_development(player, game, remaining_turns)
    
    if options:
        print(f"\nRecommended developments (Budget: ${player.cash - player.min_cash_reserve:.0f}):")
        print(f"Estimated remaining turns: {remaining_turns}\n")
        
        total_cost = 0
        total_ev = 0
        
        for i, option in enumerate(options, 1):
            print(f"{i}. {option.description}")
            print(f"   Cost: ${option.cost:.0f}")
            print(f"   Rent increase: ${option.rent_increase:.0f}")
            print(f"   Expected value: ${option.expected_value:.0f}")
            print(f"   EV per dollar: ${option.ev_per_dollar:.2f}")
            print(f"   ROI: {(option.expected_value / option.cost - 1) * 100:.1f}%")
            print()
            
            total_cost += option.cost
            total_ev += option.expected_value
        
        print(f"Total investment: ${total_cost:.0f}")
        print(f"Total expected return: ${total_ev:.0f}")
        print(f"Overall ROI: {(total_ev / total_cost - 1) * 100:.1f}%")
    else:
        print("No development options available (insufficient cash or no monopolies)")
