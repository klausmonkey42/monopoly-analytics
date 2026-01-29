"""
Property data structures for Monopoly board
"""
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class Property:
    """Represents a property on the Monopoly board"""
    position: int
    name: str
    property_type: str  # 'Street', 'Railroad', 'Utility', 'Action Spaces'
    color: Optional[str]
    purchase_price: Optional[float]
    mortgage_value: Optional[float]
    base_rent: Optional[float]
    rent_with_color_set: Optional[float]
    rent_1_house: Optional[float]
    rent_2_house: Optional[float]
    rent_3_house: Optional[float]
    rent_4_house: Optional[float]
    rent_hotel: Optional[float]
    house_cost: Optional[float]
    
    def is_purchasable(self) -> bool:
        """Can this property be purchased?"""
        return self.property_type in ['Street', 'Railroad', 'Utility']
    
    def get_rent(self, has_monopoly: bool = False, houses: int = 0) -> float:
        """Calculate rent based on development"""
        if not self.is_purchasable():
            return 0.0
        
        if houses == 0:
            if has_monopoly and self.property_type == 'Street':
                return self.rent_with_color_set or 0.0
            return self.base_rent or 0.0
        elif houses == 1:
            return self.rent_1_house or 0.0
        elif houses == 2:
            return self.rent_2_house or 0.0
        elif houses == 3:
            return self.rent_3_house or 0.0
        elif houses == 4:
            return self.rent_4_house or 0.0
        elif houses == 5:  # Hotel
            return self.rent_hotel or 0.0
        return 0.0


class MonopolyBoard:
    """Represents the complete Monopoly board"""
    
    def __init__(self, excel_path: str):
        """Load board data from Excel file"""
        df = pd.read_excel(excel_path, sheet_name='Properties')
        
        self.properties: List[Property] = []
        self.color_groups: Dict[str, List[int]] = {}
        
        for _, row in df.iterrows():
            prop = Property(
                position=int(row['Position']),
                name=str(row['Property Name']),
                property_type=str(row['Property Type']),
                color=str(row['Color']) if pd.notna(row['Color']) else None,
                purchase_price=float(row['Purchase Value']) if pd.notna(row['Purchase Value']) else None,
                mortgage_value=float(row['Mortgage Value']) if pd.notna(row['Mortgage Value']) else None,
                base_rent=float(row['Base Rent']) if pd.notna(row['Base Rent']) else None,
                rent_with_color_set=float(row['Rent - Color Set']) if pd.notna(row['Rent - Color Set']) else None,
                rent_1_house=float(row['Rent - 1']) if pd.notna(row['Rent - 1']) else None,
                rent_2_house=float(row['Rent - 2']) if pd.notna(row['Rent - 2']) else None,
                rent_3_house=float(row['Rent - 3']) if pd.notna(row['Rent - 3']) else None,
                rent_4_house=float(row['Rent - 4']) if pd.notna(row['Rent - 4']) else None,
                rent_hotel=float(row['Rent - Hotel']) if pd.notna(row['Rent - Hotel']) else None,
                house_cost=float(row['House Cost']) if pd.notna(row['House Cost']) else None,
            )
            self.properties.append(prop)
            
            # Build color group index
            if prop.color and prop.property_type == 'Street':
                if prop.color not in self.color_groups:
                    self.color_groups[prop.color] = []
                self.color_groups[prop.color].append(prop.position)
    
    def get_property(self, position: int) -> Property:
        """Get property at board position"""
        return self.properties[position]
    
    def get_property_by_name(self, name: str) -> Optional[Property]:
        """Get property by name"""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None
    
    def has_monopoly(self, owned_positions: List[int], color: str) -> bool:
        """Check if player owns all properties of a color"""
        if color not in self.color_groups:
            return False
        required = set(self.color_groups[color])
        owned = set(owned_positions)
        return required.issubset(owned)
    
    def get_monopoly_for_position(self, position: int) -> Optional[str]:
        """Get the color group for a property position"""
        prop = self.get_property(position)
        if prop.property_type == 'Street' and prop.color:
            return prop.color
        return None


def load_board(excel_path: str = '/mnt/user-data/uploads/Monopoly_Data_Input.xlsx') -> MonopolyBoard:
    """Convenience function to load the board"""
    return MonopolyBoard(excel_path)


# Test the module
if __name__ == '__main__':
    board = load_board()
    
    print("Board loaded successfully!")
    print(f"Total positions: {len(board.properties)}")
    print(f"\nColor groups: {list(board.color_groups.keys())}")
    
    # Test a property
    nc_ave = board.get_property_by_name("North Carolina Avenue")
    if nc_ave:
        print(f"\n{nc_ave.name}:")
        print(f"  Position: {nc_ave.position}")
        print(f"  Color: {nc_ave.color}")
        print(f"  Price: ${nc_ave.purchase_price}")
        print(f"  Base rent: ${nc_ave.base_rent}")
        print(f"  Rent with monopoly: ${nc_ave.rent_with_color_set}")
        print(f"  Rent with hotel: ${nc_ave.rent_hotel}")
