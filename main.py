#!/usr/bin/env python3
"""
Monopoly Property Investment Analyzer
Main script to run complete Monte Carlo analysis
"""

import sys
import time
from properties import load_board
from simulator import MonopolySimulator
from analytics import analyze_property_investment, format_analysis_report
from csv_exporter import MonopolyCSVExporter


def convert_results_for_csv(sim_stats, individual_results):
    """
    Convert SimulationResult objects to dictionary format for CSV export

    Args:
        sim_stats: Aggregated statistics from simulator
        individual_results: List of SimulationResult objects

    Returns:
        List of dictionaries with CSV-friendly field names
    """
    csv_data = []

    for sim_result in individual_results:
        # Calculate ROI
        if sim_result.property_purchased and sim_result.purchase_price > 0:
            roi = ((sim_result.total_rent_collected - sim_result.purchase_price)
                   / sim_result.purchase_price * 100)
        else:
            roi = 0

        csv_data.append({
            'boughtProperty': sim_result.property_purchased,
            'totalInvestment': sim_result.purchase_price,
            'totalReturns': sim_result.total_rent_collected,
            'netProfit': sim_result.total_rent_collected - sim_result.purchase_price,
            'roi': roi,
            'npv': 0,  # Will be calculated if needed
            'irr': 0,  # Will be calculated if needed
            'propertiesOwned': 1 if sim_result.property_purchased else 0,
            'housesBuilt': 0,  # Not tracked in current SimulationResult
            'hotelsBuilt': 0,  # Not tracked in current SimulationResult
            'totalRentCollected': sim_result.total_rent_collected,
            'yearsSimulated': sim_result.turns_played // 52,  # Rough estimate
            'totalTurns': sim_result.turns_played,
            'finalCash': sim_result.final_player_cash,
            'cashFlowByTurn': list(sim_result.rent_by_turn.values()) if hasattr(sim_result, 'rent_by_turn') else []
        })

    return csv_data


def run_property_analysis(
        property_name: str,
        your_cash: float,
        your_position: int,
        your_properties: list,
        opponents: list,
        num_simulations: int = 1000,
        max_turns: int = 250,
        enable_house_building: bool = True,
        export_csv: bool = True
):
    """
    Run complete analysis for a property purchase decision

    Args:
        property_name: Name of property to analyze
        your_cash: Your current cash
        your_position: Your current board position
        your_properties: List of property positions you own
        opponents: List of dicts with opponent data
        num_simulations: Number of Monte Carlo simulations
        max_turns: Maximum turns per game
        enable_house_building: Whether to enable house building
        export_csv: Whether to export results to CSV files

    Returns:
        Complete analysis dictionary (with csv_files if export_csv=True)
    """
    print(f"\n{'=' * 70}")
    print(f"MONOPOLY INVESTMENT ANALYZER")
    print(f"{'=' * 70}\n")

    # Load board
    print("Loading board data...")
    board = load_board()

    # Find property
    target_property = board.get_property_by_name(property_name)
    if not target_property:
        print(f"Error: Property '{property_name}' not found!")
        return None

    print(f"Analyzing: {target_property.name}")
    print(f"Purchase Price: ${target_property.purchase_price}")
    print(f"Color: {target_property.color}")

    # Check if completes monopoly
    if target_property.color:
        color_properties = board.color_groups.get(target_property.color, [])
        owned_in_color = [p for p in your_properties if p in color_properties]
        if len(owned_in_color) == len(color_properties) - 1:
            print(f"⭐ COMPLETES {target_property.color.upper()} MONOPOLY!")

    # Build player configurations
    player_configs = [
        {
            'name': 'You',
            'cash': your_cash,
            'position': your_position,
            'owned_properties': your_properties.copy(),
            'risk_tolerance': 0.6
        }
    ]

    for i, opp in enumerate(opponents):
        player_configs.append({
            'name': opp.get('name', f'Player {i + 2}'),
            'cash': opp.get('cash', 1500),
            'position': opp.get('position', 0),
            'owned_properties': opp.get('properties', []).copy(),
            'risk_tolerance': opp.get('risk_tolerance', 0.5)
        })

    # Initialize simulator
    print(f"\nInitializing Monte Carlo simulator...")
    simulator = MonopolySimulator(board)

    # Run simulations
    print(f"Running {num_simulations} simulations (max {max_turns} turns each)...")
    print("This may take a minute...\n")

    start_time = time.time()

    sim_stats = simulator.run_monte_carlo(
        target_player_idx=0,
        target_property_position=target_property.position,
        player_configs=player_configs,
        num_simulations=num_simulations,
        max_turns=max_turns,
        enable_house_building=enable_house_building,
        return_individual_results=export_csv  # Get individual results for CSV export
    )

    elapsed = time.time() - start_time
    print(f"\n✓ Completed in {elapsed:.2f} seconds")
    print(f"  ({elapsed / num_simulations * 1000:.1f}ms per simulation)\n")

    # Export to CSV if requested
    csv_files = None
    if export_csv and 'individual_results' in sim_stats:
        print("Exporting results to CSV...")
        csv_data = convert_results_for_csv(sim_stats, sim_stats['individual_results'])

        exporter = MonopolyCSVExporter(output_dir="csv_exports")
        csv_files = exporter.export_all(
            simulation_results=csv_data,
            property_name=property_name.replace(" ", "_")
        )

        # Remove individual_results from sim_stats to save memory
        del sim_stats['individual_results']

    # Calculate financial metrics
    print("Calculating financial metrics...")
    analysis = analyze_property_investment(sim_stats, discount_rate=0.05)

    # Add simulation metadata
    analysis['simulation_metadata'] = {
        'num_simulations': num_simulations,
        'max_turns': max_turns,
        'elapsed_time': elapsed,
        'property_position': target_property.position
    }

    # Add CSV file paths if exported
    if csv_files:
        analysis['csv_files'] = csv_files

    # Print report
    print(format_analysis_report(target_property.name, analysis))

    return analysis


def main():
    """Run the analyzer with the scenario from your question"""

    # YOUR SCENARIO:
    # You have $3500, just landed on North Carolina Avenue
    # You own Pacific Avenue (position 31)
    # 3 other players in the game

    analysis = run_property_analysis(
        property_name="North Carolina Avenue",
        your_cash=5500,
        your_position=20,  # Start nearby so you'll land on it
        your_properties=[11, 13, 14, 31, 34, 37, 39],  # Pacific Avenue
        opponents=[
            {
                'name': 'Player 2',
                'cash': 1800,
                'position': 5,
                'properties': [1, 3],  # Brown properties
                'risk_tolerance': 0.3
            },
            {
                'name': 'Player 3',
                'cash': 2200,
                'position': 10,
                'properties': [5, 15],  # Railroads
                'risk_tolerance': 0.5
            },
            {
                'name': 'Player 4',
                'cash': 1500,
                'position': 0,
                'properties': [],
                'risk_tolerance': 0.6
            }
        ],
        num_simulations=2000,  # Run 2000 simulations for good statistics
        max_turns=200  # Much longer games to allow properties to pay off
    )

    if analysis:
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE!")
        print("=" * 70)
        print(f"\n📊 Simulations: {analysis['simulation_metadata']['num_simulations']}")
        print(f"📈 Expected NPV: ${analysis['npv_mean']:,.0f}")
        print(f"💵 Expected Total Rent: ${analysis['expected_total_rent']:,.0f}")
        payback_str = f"{analysis['payback_mean_turns']:.1f} turns" if analysis[
            'payback_mean_turns'] else "Never (insufficient rent)"
        print(f"⏱️  Average Payback: {payback_str}")
        print(f"💰 Recommendation: {analysis['recommendation']}")

        # Show CSV export info
        if 'csv_files' in analysis:
            print(f"\n📁 CSV Exports Created:")
            for export_type, filepath in analysis['csv_files'].items():
                filename = filepath.split('/')[-1]
                print(f"   • {export_type}: {filename}")
            print(f"\n   All files saved to: csv_exports/")

        print("\nThis data is now ready for your analytics cards!")

    return analysis


if __name__ == '__main__':
    result = main()
