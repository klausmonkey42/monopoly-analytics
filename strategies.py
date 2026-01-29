"""
AI strategies for computer players
"""
from game_state import GameState, Player
from properties import Property

def conservative_strategy(game: GameState, player: Player, position: int) -> bool:
    """
    Conservative buying strategy
    - Only buy if cash > 3x purchase price
    - Prioritize completing monopolies
    - Keep large cash reserve
    """
    prop = game.board.get_property(position)
    
    if not prop.is_purchasable() or prop.purchase_price is None:
        return False
    
    # Need 3x the price in cash
    if player.cash < prop.purchase_price * 3:
        return False
    
    # Always buy if it completes a monopoly
    if prop.color and prop.property_type == 'Street':
        # Check if we own other properties in this color group
        color_group_positions = game.board.color_groups.get(prop.color, [])
        owned_in_group = sum(1 for pos in color_group_positions 
                            if player.owns_property(pos))
        total_in_group = len(color_group_positions)
        
        # If this would complete monopoly, buy it
        if owned_in_group == total_in_group - 1:
            return True
    
    # Otherwise, only buy cheap properties
    return prop.purchase_price <= 150


def aggressive_strategy(game: GameState, player: Player, position: int) -> bool:
    """
    Aggressive buying strategy
    - Buy almost everything if affordable
    - Willing to go low on cash
    - Prioritize high-value properties
    """
    prop = game.board.get_property(position)
    
    if not prop.is_purchasable() or prop.purchase_price is None:
        return False
    
    # Buy if we can afford it with minimal reserve
    min_reserve = 100
    if player.cash < prop.purchase_price + min_reserve:
        return False
    
    # Don't buy utilities or cheap properties in late game
    if prop.property_type == 'Utility':
        return player.get_total_properties() < 3
    
    if prop.purchase_price < 100:
        return player.get_total_properties() < 5
    
    # Buy everything else
    return True


def balanced_strategy(game: GameState, player: Player, position: int) -> bool:
    """
    Balanced strategy - adapts based on game state
    - Considers monopoly potential
    - Considers property value
    - Maintains reasonable cash reserve
    """
    prop = game.board.get_property(position)
    
    if not prop.is_purchasable() or prop.purchase_price is None:
        return False
    
    # Check affordability (2x price + reserve)
    reserve_needed = 250
    if player.cash < prop.purchase_price * 2 + reserve_needed:
        return False
    
    # High priority: Completes monopoly
    if prop.color and prop.property_type == 'Street':
        color_group_positions = game.board.color_groups.get(prop.color, [])
        owned_in_group = sum(1 for pos in color_group_positions 
                            if player.owns_property(pos))
        total_in_group = len(color_group_positions)
        
        # Would complete monopoly - high priority
        if owned_in_group == total_in_group - 1:
            return True
        
        # Starts a new monopoly - medium priority for good colors
        if owned_in_group == 0:
            good_colors = ['Orange', 'Red', 'Yellow', 'Green']
            if prop.color in good_colors:
                return True
    
    # Medium priority: Railroads (always good income)
    if prop.property_type == 'Railroad':
        return True
    
    # Lower priority: Utilities
    if prop.property_type == 'Utility':
        utility_positions = [12, 28]
        owned_utilities = sum(1 for pos in utility_positions 
                             if player.owns_property(pos))
        # Buy second utility to complete the pair
        return owned_utilities == 1
    
    # For other streets, buy if value is good
    if prop.purchase_price and prop.rent_hotel:
        # Simple value metric: hotel rent / price
        value_ratio = prop.rent_hotel / prop.purchase_price
        return value_ratio > 3.5
    
    return False


def get_strategy(risk_tolerance: float):
    """
    Get strategy function based on risk tolerance
    0.0-0.4: Conservative
    0.4-0.6: Balanced
    0.6-1.0: Aggressive
    """
    if risk_tolerance < 0.4:
        return conservative_strategy
    elif risk_tolerance < 0.6:
        return balanced_strategy
    else:
        return aggressive_strategy


def analyze_purchase_value(game: GameState, player: Player, position: int) -> dict:
    """
    Analyze the value of purchasing a property
    Returns metrics for decision making
    """
    prop = game.board.get_property(position)
    
    analysis = {
        'position': position,
        'name': prop.name,
        'price': prop.purchase_price,
        'affordable': False,
        'completes_monopoly': False,
        'monopoly_color': None,
        'expected_rent': 0,
        'value_score': 0
    }
    
    if not prop.is_purchasable() or prop.purchase_price is None:
        return analysis
    
    analysis['affordable'] = player.can_afford(prop.purchase_price)
    
    # Check monopoly status
    if prop.color and prop.property_type == 'Street':
        color_group_positions = game.board.color_groups.get(prop.color, [])
        owned_in_group = sum(1 for pos in color_group_positions 
                            if player.owns_property(pos))
        total_in_group = len(color_group_positions)
        
        if owned_in_group == total_in_group - 1:
            analysis['completes_monopoly'] = True
            analysis['monopoly_color'] = prop.color
    
    # Calculate expected rent (base + potential with houses)
    has_monopoly = analysis['completes_monopoly']
    analysis['expected_rent'] = prop.get_rent(has_monopoly, 0)
    
    # Simple value score
    if prop.purchase_price and prop.rent_hotel:
        analysis['value_score'] = prop.rent_hotel / prop.purchase_price
    
    return analysis


# Test the module
if __name__ == '__main__':
    from properties import load_board
    from game_state import create_game
    
    board = load_board()
    
    player_configs = [
        {
            'name': 'Conservative Player',
            'cash': 1500,
            'position': 0,
            'owned_properties': [],
            'risk_tolerance': 0.2
        },
        {
            'name': 'Balanced Player',
            'cash': 1500,
            'position': 0,
            'owned_properties': [31],  # Pacific Ave
            'risk_tolerance': 0.5
        },
        {
            'name': 'Aggressive Player',
            'cash': 1500,
            'position': 0,
            'owned_properties': [],
            'risk_tolerance': 0.8
        }
    ]
    
    game = create_game(board, player_configs)
    
    print("Testing AI Strategies\n")
    print("="*60)
    
    # Test property: North Carolina Avenue (completes monopoly for balanced player)
    nc_position = 32
    nc_prop = board.get_property(nc_position)
    
    print(f"\nProperty: {nc_prop.name}")
    print(f"Price: ${nc_prop.purchase_price}")
    print(f"Color: {nc_prop.color}")
    
    for player in game.players:
        strategy = get_strategy(player.risk_tolerance)
        should_buy = strategy(game, player, nc_position)
        
        print(f"\n{player.name} (risk={player.risk_tolerance}):")
        print(f"  Cash: ${player.cash}")
        print(f"  Decision: {'BUY' if should_buy else 'PASS'}")
        
        # Show analysis
        analysis = analyze_purchase_value(game, player, nc_position)
        print(f"  Analysis:")
        print(f"    - Affordable: {analysis['affordable']}")
        print(f"    - Completes monopoly: {analysis['completes_monopoly']}")
        print(f"    - Expected rent: ${analysis['expected_rent']}")
        print(f"    - Value score: {analysis['value_score']:.2f}")
