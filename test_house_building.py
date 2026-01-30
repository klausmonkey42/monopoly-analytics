#!/usr/bin/env python3
"""
Quick test: Run small simulation with house building
"""

from properties import load_board
from simulator import MonopolySimulator

print("="*70)
print("TESTING HOUSE BUILDING IN SIMULATION")
print("="*70)

board = load_board()
simulator = MonopolySimulator(board)

# Scenario: You own Pacific Ave, buying North Carolina completes Green monopoly
player_configs = [
    {
        'name': 'You',
        'cash': 3500,
        'position': 20,
        'owned_properties': [31],  # Pacific Avenue
        'risk_tolerance': 0.6
    },
    {
        'name': 'Opponent',
        'cash': 1500,
        'position': 5,
        'owned_properties': [1, 3],
        'risk_tolerance': 0.5
    }
]

print("\nScenario: You own Pacific Ave (Green)")
print("Target: North Carolina Ave (completes Green monopoly)")
print()

# Test WITHOUT house building
print("-" * 70)
print("TEST 1: WITHOUT House Building")
print("-" * 70)

results_no_houses = simulator.run_monte_carlo(
    target_player_idx=0,
    target_property_position=32,  # North Carolina Avenue
    player_configs=player_configs,
    num_simulations=100,
    max_turns=150,
    enable_house_building=False
)

print(f"Average rent collected: ${results_no_houses['total_rent_mean']:.0f}")
print(f"Break-even rate: {results_no_houses['break_even_rate']:.1%}")

# Test WITH house building
print("\n" + "-" * 70)
print("TEST 2: WITH House Building")
print("-" * 70)

results_with_houses = simulator.run_monte_carlo(
    target_player_idx=0,
    target_property_position=32,  # North Carolina Avenue
    player_configs=player_configs,
    num_simulations=100,
    max_turns=150,
    enable_house_building=True  # ← ENABLED!
)

print(f"Average rent collected: ${results_with_houses['total_rent_mean']:.0f}")
print(f"Break-even rate: {results_with_houses['break_even_rate']:.1%}")

# Compare
print("\n" + "="*70)
print("COMPARISON")
print("="*70)

rent_increase = results_with_houses['total_rent_mean'] - results_no_houses['total_rent_mean']
rent_pct = (rent_increase / results_no_houses['total_rent_mean'] * 100) if results_no_houses['total_rent_mean'] > 0 else 0

print(f"\nRent collection improvement: ${rent_increase:.0f} ({rent_pct:.0f}% increase)")
print(f"Break-even improvement: {results_with_houses['break_even_rate'] - results_no_houses['break_even_rate']:.1%}")

if rent_increase > 100:
    print("\n✅ HOUSE BUILDING IS WORKING!")
    print("   Rent collection significantly increased!")
else:
    print("\n⚠️  Limited improvement (may need more turns or better monopolies)")

print("\n" + "="*70)
