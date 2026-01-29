"""
Player and game state management
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from properties import MonopolyBoard, Property

@dataclass
class Player:
    """Represents a player in the game"""
    name: str
    cash: float
    position: int = 0
    owned_properties: List[int] = field(default_factory=list)
    houses: Dict[int, int] = field(default_factory=dict)  # position -> num_houses (5 = hotel)
    in_jail: bool = False
    jail_turns: int = 0
    is_bankrupt: bool = False
    
    # Strategy parameters
    risk_tolerance: float = 0.5  # 0-1, higher = more aggressive
    min_cash_reserve: float = 200.0  # Minimum cash to keep on hand
    
    def can_afford(self, amount: float) -> bool:
        """Check if player can afford a purchase while maintaining reserve"""
        return (self.cash - amount) >= self.min_cash_reserve
    
    def pay(self, amount: float) -> bool:
        """Player pays money. Returns False if bankrupt"""
        self.cash -= amount
        if self.cash < 0:
            self.is_bankrupt = True
            return False
        return True
    
    def receive(self, amount: float):
        """Player receives money"""
        self.cash += amount
    
    def buy_property(self, position: int, price: float) -> bool:
        """Attempt to buy a property"""
        if not self.can_afford(price):
            return False
        
        self.cash -= price
        self.owned_properties.append(position)
        self.houses[position] = 0  # No houses initially
        return True
    
    def owns_property(self, position: int) -> bool:
        """Check if player owns a property"""
        return position in self.owned_properties
    
    def get_total_properties(self) -> int:
        """Count total owned properties"""
        return len(self.owned_properties)
    
    def move(self, spaces: int, board_size: int = 40) -> bool:
        """Move player on board. Returns True if passed GO"""
        old_position = self.position
        self.position = (self.position + spaces) % board_size
        
        # Check if passed GO
        return self.position < old_position
    

@dataclass
class GameState:
    """Represents the complete state of a Monopoly game"""
    board: MonopolyBoard
    players: List[Player]
    current_turn: int = 0
    current_player_idx: int = 0
    total_turns: int = 0  # Total turns taken by all players
    
    def get_current_player(self) -> Player:
        """Get the player whose turn it is"""
        return self.players[self.current_player_idx]
    
    def next_player(self):
        """Move to next player's turn"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        if self.current_player_idx == 0:
            self.current_turn += 1
        self.total_turns += 1
    
    def get_property_owner(self, position: int) -> Optional[Player]:
        """Find who owns a property, if anyone"""
        for player in self.players:
            if player.owns_property(position):
                return player
        return None
    
    def get_active_players(self) -> List[Player]:
        """Get players who are not bankrupt"""
        return [p for p in self.players if not p.is_bankrupt]
    
    def is_game_over(self) -> bool:
        """Check if game is over (only 1 player remaining)"""
        return len(self.get_active_players()) <= 1
    
    def get_winner(self) -> Optional[Player]:
        """Get the winner, if game is over"""
        active = self.get_active_players()
        if len(active) == 1:
            return active[0]
        return None
    
    def player_has_monopoly(self, player: Player, color: str) -> bool:
        """Check if player has a color monopoly"""
        return self.board.has_monopoly(player.owned_properties, color)


def create_game(board: MonopolyBoard, 
                player_configs: List[Dict]) -> GameState:
    """
    Create a new game state
    
    player_configs: List of dicts with keys: name, cash, position, owned_properties, risk_tolerance
    """
    players = []
    for config in player_configs:
        player = Player(
            name=config.get('name', 'Player'),
            cash=config.get('cash', 1500),
            position=config.get('position', 0),
            owned_properties=config.get('owned_properties', []).copy(),
            risk_tolerance=config.get('risk_tolerance', 0.5),
            min_cash_reserve=config.get('min_cash_reserve', 200)
        )
        # Initialize houses dict for owned properties
        for pos in player.owned_properties:
            player.houses[pos] = 0
        players.append(player)
    
    return GameState(board=board, players=players)


# Test the module
if __name__ == '__main__':
    from properties import load_board
    
    board = load_board()
    
    # Create test game
    player_configs = [
        {
            'name': 'You',
            'cash': 3500,
            'position': 32,  # North Carolina Avenue
            'owned_properties': [31],  # Pacific Avenue
            'risk_tolerance': 0.7
        },
        {
            'name': 'Player 2',
            'cash': 1800,
            'position': 15,
            'owned_properties': [1, 3],  # Mediterranean and Baltic
            'risk_tolerance': 0.3
        },
        {
            'name': 'Player 3',
            'cash': 2200,
            'position': 25,
            'owned_properties': [5, 15],  # Railroads
            'risk_tolerance': 0.5
        },
        {
            'name': 'Player 4',
            'cash': 1500,
            'position': 10,
            'owned_properties': [],
            'risk_tolerance': 0.6
        }
    ]
    
    game = create_game(board, player_configs)
    
    print("Game created successfully!")
    print(f"\nPlayers:")
    for p in game.players:
        print(f"  {p.name}: ${p.cash}, Position {p.position}, "
              f"Properties: {p.get_total_properties()}")
    
    # Test property ownership
    nc_ave_pos = 32
    owner = game.get_property_owner(nc_ave_pos)
    print(f"\nNorth Carolina Avenue (pos {nc_ave_pos}) owner: {owner.name if owner else 'None'}")
    
    # Test buying
    player = game.players[0]
    prop = board.get_property(nc_ave_pos)
    print(f"\n{player.name} attempting to buy {prop.name} for ${prop.purchase_price}")
    if player.buy_property(nc_ave_pos, prop.purchase_price):
        print(f"  Success! {player.name} now has ${player.cash}")
        print(f"  Total properties: {player.get_total_properties()}")
    else:
        print(f"  Failed - insufficient funds")
