"""
Core game mechanics: dice rolling, movement, rent payments, transactions
"""
import random
from typing import Tuple, Optional, List
from game_state import GameState, Player
from properties import Property

class GameMechanics:
    """Handles all game mechanics and rules"""
    
    def __init__(self, game_state: GameState):
        self.game = game_state
        self.board = game_state.board
    
    def roll_dice(self) -> Tuple[int, int, bool]:
        """
        Roll two dice
        Returns: (die1, die2, is_doubles)
        """
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        is_doubles = (die1 == die2)
        return die1, die2, is_doubles
    
    def move_player(self, player: Player, spaces: int) -> bool:
        """
        Move player and handle passing GO
        Returns: True if passed GO
        """
        passed_go = player.move(spaces)
        if passed_go:
            player.receive(200)  # Collect $200 for passing GO
        return passed_go
    
    def handle_landing(self, player: Player) -> dict:
        """
        Handle a player landing on a space
        Returns dict with action details for tracking
        """
        position = player.position
        prop = self.board.get_property(position)
        
        result = {
            'position': position,
            'property_name': prop.name,
            'action': None,
            'amount': 0,
            'owner': None
        }
        
        # Special spaces
        if prop.name == 'Go To Jail':
            player.position = 10  # Jail position
            player.in_jail = True
            result['action'] = 'go_to_jail'
            return result
        
        if prop.name in ['Income Tax', 'Luxury Tax']:
            # Income Tax = -200, Luxury Tax = -100 (from Excel)
            if prop.name == 'Income Tax':
                amount = 200
            else:
                amount = 100
            player.pay(amount)
            result['action'] = 'pay_tax'
            result['amount'] = -amount
            return result
        
        # Property spaces
        if not prop.is_purchasable():
            result['action'] = 'free_space'
            return result
        
        owner = self.game.get_property_owner(position)
        
        if owner is None:
            # Property available for purchase
            result['action'] = 'available_for_purchase'
            result['amount'] = prop.purchase_price
            return result
        
        if owner == player:
            # Own property, nothing happens
            result['action'] = 'own_property'
            return result
        
        # Must pay rent to owner
        rent = self.calculate_rent(position, owner)
        player.pay(rent)
        owner.receive(rent)
        
        result['action'] = 'pay_rent'
        result['amount'] = -rent
        result['owner'] = owner.name
        
        return result
    
    def calculate_rent(self, position: int, owner: Player) -> float:
        """Calculate rent for a property"""
        prop = self.board.get_property(position)
        
        # Get number of houses
        houses = owner.houses.get(position, 0)
        
        # Check for monopoly
        has_monopoly = False
        if prop.color and prop.property_type == 'Street':
            has_monopoly = self.game.player_has_monopoly(owner, prop.color)
        
        # Special case: Railroads
        if prop.property_type == 'Railroad':
            # Count owned railroads
            railroad_positions = [5, 15, 25, 35]
            owned_railroads = sum(1 for pos in railroad_positions if owner.owns_property(pos))
            # Rent: 25, 50, 100, 200 for 1,2,3,4 railroads
            rent_multiplier = 2 ** (owned_railroads - 1)
            return 25 * rent_multiplier
        
        # Special case: Utilities
        if prop.property_type == 'Utility':
            # For simplicity, use fixed multiplier (in real game, it's dice roll x 4 or x 10)
            utility_positions = [12, 28]
            owned_utilities = sum(1 for pos in utility_positions if owner.owns_property(pos))
            multiplier = 10 if owned_utilities == 2 else 4
            # Use average dice roll of 7
            return 7 * multiplier
        
        # Regular property rent
        return prop.get_rent(has_monopoly, houses)
    
    def purchase_property(self, player: Player, position: int) -> bool:
        """
        Attempt to purchase a property
        Returns True if successful
        """
        prop = self.board.get_property(position)
        
        if not prop.is_purchasable():
            return False
        
        owner = self.game.get_property_owner(position)
        if owner is not None:
            return False
        
        if prop.purchase_price is None:
            return False
        
        return player.buy_property(position, prop.purchase_price)
    
    def take_turn(self, player: Player, strategy_func=None) -> List[dict]:
        """
        Execute one player's turn
        Returns list of events that occurred
        """
        events = []
        
        if player.is_bankrupt:
            return events
        
        # Handle jail (simplified - just skip turn)
        if player.in_jail:
            player.jail_turns += 1
            if player.jail_turns >= 3:
                player.in_jail = False
                player.jail_turns = 0
            events.append({'event': 'in_jail', 'player': player.name})
            return events
        
        # Roll dice
        die1, die2, is_doubles = self.roll_dice()
        total = die1 + die2
        
        events.append({
            'event': 'roll',
            'player': player.name,
            'roll': total,
            'is_doubles': is_doubles
        })
        
        # Move
        passed_go = self.move_player(player, total)
        if passed_go:
            events.append({
                'event': 'passed_go',
                'player': player.name,
                'amount': 200
            })
        
        # Handle landing
        landing_result = self.handle_landing(player)
        landing_result['player'] = player.name
        landing_result['event'] = 'landing'
        events.append(landing_result)
        
        # Purchase decision (if property available and strategy provided)
        if landing_result['action'] == 'available_for_purchase' and strategy_func:
            should_buy = strategy_func(self.game, player, player.position)
            if should_buy:
                success = self.purchase_property(player, player.position)
                events.append({
                    'event': 'purchase',
                    'player': player.name,
                    'position': player.position,
                    'success': success,
                    'amount': -landing_result['amount'] if success else 0
                })
        
        return events


# Test the module
if __name__ == '__main__':
    from properties import load_board
    from game_state import create_game
    
    board = load_board()
    
    player_configs = [
        {
            'name': 'Player 1',
            'cash': 1500,
            'position': 0,
            'owned_properties': [],
            'risk_tolerance': 0.5
        },
        {
            'name': 'Player 2',
            'cash': 1500,
            'position': 0,
            'owned_properties': [1],  # Owns Mediterranean
            'risk_tolerance': 0.5
        }
    ]
    
    game = create_game(board, player_configs)
    mechanics = GameMechanics(game)
    
    print("Testing game mechanics...\n")
    
    # Test dice rolling
    for i in range(3):
        die1, die2, is_doubles = mechanics.roll_dice()
        print(f"Roll {i+1}: {die1} + {die2} = {die1+die2} {'(DOUBLES!)' if is_doubles else ''}")
    
    # Test rent calculation
    print("\n--- Rent Tests ---")
    prop = board.get_property_by_name("Mediterranean Avenue")
    owner = game.players[1]
    rent = mechanics.calculate_rent(1, owner)
    print(f"Rent for {prop.name} (no monopoly): ${rent}")
    
    # Give owner monopoly
    owner.owned_properties.append(3)  # Baltic Avenue
    rent_monopoly = mechanics.calculate_rent(1, owner)
    print(f"Rent for {prop.name} (with monopoly): ${rent_monopoly}")
    
    # Test a turn
    print("\n--- Turn Simulation ---")
    player = game.players[0]
    print(f"Before: {player.name} at position {player.position} with ${player.cash}")
    
    # Simple strategy: buy if affordable
    def simple_strategy(game, player, position):
        prop = game.board.get_property(position)
        return player.can_afford(prop.purchase_price)
    
    events = mechanics.take_turn(player, simple_strategy)
    
    print(f"After: {player.name} at position {player.position} with ${player.cash}")
    print(f"\nEvents:")
    for event in events:
        print(f"  {event}")
