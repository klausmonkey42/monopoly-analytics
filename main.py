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

def run_property_analysis(
    property_name: str,
    your_cash: float,
    your_position: int,
    your_properties: list,
    opponents: list,
    num_simulations: int = 1000,
    max_turns: int = 100
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
    
    Returns:
        Complete analysis dictionary
    """
    print(f"\n{'='*70}")
    print(f"MONOPOLY INVESTMENT ANALYZER")
    print(f"{'='*70}\n")
    
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
            'name': opp.get('name', f'Player {i+2}'),
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
        max_turns=max_turns
    )
    
    elapsed = time.time() - start_time
    print(f"\n✓ Completed in {elapsed:.2f} seconds")
    print(f"  ({elapsed/num_simulations*1000:.1f}ms per simulation)\n")
    
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
        your_cash=3500,
        your_position=20,  # Start nearby so you'll land on it
        your_properties=[31],  # Pacific Avenue
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
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE!")
        print("="*70)
        print(f"\n📊 Simulations: {analysis['simulation_metadata']['num_simulations']}")
        print(f"📈 Expected NPV: ${analysis['npv_mean']:,.0f}")
        print(f"💵 Expected Total Rent: ${analysis['expected_total_rent']:,.0f}")
        payback_str = f"{analysis['payback_mean_turns']:.1f} turns" if analysis['payback_mean_turns'] else "Never (insufficient rent)"
        print(f"⏱️  Average Payback: {payback_str}")
        print(f"💰 Recommendation: {analysis['recommendation']}")
        print("\nThis data is now ready for your analytics cards!")
    
    return analysis


if __name__ == '__main__':
    result = main()
