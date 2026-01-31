"""
CSV Export Module for Monopoly Strategy Analyzer
Exports simulation data in various formats for external analysis
"""

import csv
from typing import List, Dict, Any
from datetime import datetime
import os


class MonopolyCSVExporter:
    """Handles all CSV export functionality for Monopoly simulations"""
    
    def __init__(self, output_dir: str = "csv_exports"):
        """
        Initialize the CSV exporter
        
        Args:
            output_dir: Directory to save CSV files (created if doesn't exist)
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def export_simulation_runs(self, simulation_results: List[Dict], 
                              property_name: str = "property") -> str:
        """
        Export individual simulation runs - each row is one complete game
        
        Args:
            simulation_results: List of simulation result dictionaries
            property_name: Name of property being analyzed
            
        Returns:
            Path to the created CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/simulation_runs_{property_name}_{timestamp}.csv"
        
        headers = [
            'simulation_number',
            'total_investment',
            'total_returns',
            'net_profit',
            'roi_percent',
            'npv',
            'irr_percent',
            'properties_owned',
            'houses_built',
            'hotels_built',
            'total_rent_collected',
            'years_simulated',
            'total_turns',
            'final_cash',
            'bought_property'
        ]
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for i, result in enumerate(simulation_results, 1):
                row = {
                    'simulation_number': i,
                    'total_investment': result.get('totalInvestment', 0),
                    'total_returns': result.get('totalReturns', 0),
                    'net_profit': result.get('netProfit', 0),
                    'roi_percent': result.get('roi', 0),
                    'npv': result.get('npv', 0),
                    'irr_percent': result.get('irr', 0),
                    'properties_owned': result.get('propertiesOwned', 0),
                    'houses_built': result.get('housesBuilt', 0),
                    'hotels_built': result.get('hotelsBuilt', 0),
                    'total_rent_collected': result.get('totalRentCollected', 0),
                    'years_simulated': result.get('yearsSimulated', 0),
                    'total_turns': result.get('totalTurns', 0),
                    'final_cash': result.get('finalCash', 0),
                    'bought_property': result.get('boughtProperty', False)
                }
                writer.writerow(row)
        
        print(f"✅ Exported {len(simulation_results)} simulation runs to: {filename}")
        return filename
    
    def export_cash_flow_timeline(self, simulation_results: List[Dict], 
                                  property_name: str = "property") -> str:
        """
        Export turn-by-turn cash flow data across all simulations
        
        Args:
            simulation_results: List of simulation result dictionaries
            property_name: Name of property being analyzed
            
        Returns:
            Path to the created CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/cash_flow_timeline_{property_name}_{timestamp}.csv"
        
        # Find the maximum number of turns across all simulations
        max_turns = max((len(result.get('cashFlowByTurn', [])) 
                        for result in simulation_results), default=0)
        
        if max_turns == 0:
            print("⚠️  No cash flow timeline data available")
            return None
        
        headers = ['turn'] + [f'sim_{i+1}' for i in range(len(simulation_results))]
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for turn in range(max_turns):
                row = [turn + 1]
                for result in simulation_results:
                    cash_flow = result.get('cashFlowByTurn', [])
                    value = cash_flow[turn] if turn < len(cash_flow) else ''
                    row.append(value)
                writer.writerow(row)
        
        print(f"✅ Exported cash flow timeline ({max_turns} turns) to: {filename}")
        return filename
    
    def export_property_statistics(self, simulation_results: List[Dict],
                                   property_name: str = "property") -> str:
        """
        Export aggregated statistics across all simulations
        
        Args:
            simulation_results: List of simulation result dictionaries
            property_name: Name of property being analyzed
            
        Returns:
            Path to the created CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/property_statistics_{property_name}_{timestamp}.csv"
        
        # Calculate statistics
        total_sims = len(simulation_results)
        bought_count = sum(1 for r in simulation_results if r.get('boughtProperty', False))
        
        roi_values = [r.get('roi', 0) for r in simulation_results]
        npv_values = [r.get('npv', 0) for r in simulation_results]
        net_profit_values = [r.get('netProfit', 0) for r in simulation_results]
        
        stats = [
            ('Property Name', property_name),
            ('Total Simulations', total_sims),
            ('Purchase Rate', f"{(bought_count/total_sims*100):.1f}%" if total_sims > 0 else "0%"),
            ('Times Purchased', bought_count),
            ('Times Not Purchased', total_sims - bought_count),
            ('', ''),
            ('ROI Statistics', ''),
            ('Mean ROI (%)', f"{sum(roi_values)/len(roi_values):.2f}" if roi_values else "0"),
            ('Median ROI (%)', f"{sorted(roi_values)[len(roi_values)//2]:.2f}" if roi_values else "0"),
            ('Min ROI (%)', f"{min(roi_values):.2f}" if roi_values else "0"),
            ('Max ROI (%)', f"{max(roi_values):.2f}" if roi_values else "0"),
            ('', ''),
            ('NPV Statistics', ''),
            ('Mean NPV ($)', f"{sum(npv_values)/len(npv_values):.2f}" if npv_values else "0"),
            ('Median NPV ($)', f"{sorted(npv_values)[len(npv_values)//2]:.2f}" if npv_values else "0"),
            ('Min NPV ($)', f"{min(npv_values):.2f}" if npv_values else "0"),
            ('Max NPV ($)', f"{max(npv_values):.2f}" if npv_values else "0"),
            ('', ''),
            ('Net Profit Statistics', ''),
            ('Mean Net Profit ($)', f"{sum(net_profit_values)/len(net_profit_values):.2f}" if net_profit_values else "0"),
            ('Median Net Profit ($)', f"{sorted(net_profit_values)[len(net_profit_values)//2]:.2f}" if net_profit_values else "0"),
            ('Min Net Profit ($)', f"{min(net_profit_values):.2f}" if net_profit_values else "0"),
            ('Max Net Profit ($)', f"{max(net_profit_values):.2f}" if net_profit_values else "0")
        ]
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for metric, value in stats:
                writer.writerow([metric, value])
        
        print(f"✅ Exported property statistics to: {filename}")
        return filename
    
    def export_house_building_log(self, simulation_results: List[Dict],
                                  property_name: str = "property") -> str:
        """
        Export house/hotel building decisions from simulations
        
        Args:
            simulation_results: List of simulation result dictionaries
            property_name: Name of property being analyzed
            
        Returns:
            Path to the created CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/house_building_log_{property_name}_{timestamp}.csv"
        
        headers = [
            'simulation_number',
            'turn',
            'property_name',
            'action',
            'houses_before',
            'houses_after',
            'cost',
            'expected_value',
            'player_cash_after'
        ]
        
        rows_written = 0
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for i, result in enumerate(simulation_results, 1):
                building_log = result.get('houseBuildingLog', [])
                for entry in building_log:
                    row = {
                        'simulation_number': i,
                        'turn': entry.get('turn', ''),
                        'property_name': entry.get('property', ''),
                        'action': entry.get('action', ''),
                        'houses_before': entry.get('housesBefore', ''),
                        'houses_after': entry.get('housesAfter', ''),
                        'cost': entry.get('cost', ''),
                        'expected_value': entry.get('expectedValue', ''),
                        'player_cash_after': entry.get('cashAfter', '')
                    }
                    writer.writerow(row)
                    rows_written += 1
        
        if rows_written > 0:
            print(f"✅ Exported {rows_written} house building decisions to: {filename}")
        else:
            print(f"⚠️  No house building data available")
        
        return filename if rows_written > 0 else None
    
    def export_all(self, simulation_results: List[Dict], 
                   property_name: str = "property") -> Dict[str, str]:
        """
        Export all available CSV formats
        
        Args:
            simulation_results: List of simulation result dictionaries
            property_name: Name of property being analyzed
            
        Returns:
            Dictionary mapping export type to filename
        """
        print(f"\n📊 Exporting CSV data for {property_name}...")
        print(f"   Total simulations: {len(simulation_results)}")
        print(f"   Output directory: {self.output_dir}/\n")
        
        exported_files = {}
        
        # Export simulation runs
        exported_files['simulation_runs'] = self.export_simulation_runs(
            simulation_results, property_name
        )
        
        # Export cash flow timeline
        cash_flow_file = self.export_cash_flow_timeline(
            simulation_results, property_name
        )
        if cash_flow_file:
            exported_files['cash_flow_timeline'] = cash_flow_file
        
        # Export property statistics
        exported_files['property_statistics'] = self.export_property_statistics(
            simulation_results, property_name
        )
        
        # Export house building log
        house_log_file = self.export_house_building_log(
            simulation_results, property_name
        )
        if house_log_file:
            exported_files['house_building_log'] = house_log_file
        
        print(f"\n✅ All exports complete! {len(exported_files)} files created.\n")
        return exported_files


def export_comparison_csv(properties_data: Dict[str, List[Dict]], 
                          output_dir: str = "csv_exports") -> str:
    """
    Export comparison data across multiple properties
    
    Args:
        properties_data: Dictionary mapping property names to simulation results
        output_dir: Directory to save CSV file
        
    Returns:
        Path to the created CSV file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/property_comparison_{timestamp}.csv"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    headers = [
        'property_name',
        'num_simulations',
        'mean_roi_percent',
        'median_roi_percent',
        'mean_npv',
        'median_npv',
        'mean_net_profit',
        'median_net_profit',
        'purchase_rate_percent',
        'mean_houses_built',
        'mean_hotels_built',
        'mean_rent_collected'
    ]
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for property_name, results in properties_data.items():
            if not results:
                continue
            
            bought_count = sum(1 for r in results if r.get('boughtProperty', False))
            roi_values = [r.get('roi', 0) for r in results]
            npv_values = [r.get('npv', 0) for r in results]
            profit_values = [r.get('netProfit', 0) for r in results]
            houses_values = [r.get('housesBuilt', 0) for r in results]
            hotels_values = [r.get('hotelsBuilt', 0) for r in results]
            rent_values = [r.get('totalRentCollected', 0) for r in results]
            
            row = {
                'property_name': property_name,
                'num_simulations': len(results),
                'mean_roi_percent': sum(roi_values) / len(roi_values) if roi_values else 0,
                'median_roi_percent': sorted(roi_values)[len(roi_values)//2] if roi_values else 0,
                'mean_npv': sum(npv_values) / len(npv_values) if npv_values else 0,
                'median_npv': sorted(npv_values)[len(npv_values)//2] if npv_values else 0,
                'mean_net_profit': sum(profit_values) / len(profit_values) if profit_values else 0,
                'median_net_profit': sorted(profit_values)[len(profit_values)//2] if profit_values else 0,
                'purchase_rate_percent': (bought_count / len(results) * 100) if results else 0,
                'mean_houses_built': sum(houses_values) / len(houses_values) if houses_values else 0,
                'mean_hotels_built': sum(hotels_values) / len(hotels_values) if hotels_values else 0,
                'mean_rent_collected': sum(rent_values) / len(rent_values) if rent_values else 0
            }
            writer.writerow(row)
    
    print(f"✅ Exported property comparison to: {filename}")
    return filename
