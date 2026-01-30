#!/usr/bin/env python3
"""
Compare simulation results WITH and WITHOUT house building
This shows the dramatic impact of property development
"""

from main import run_property_analysis

print("\n" + "="*70)
print("HOUSE BUILDING IMPACT COMPARISON")
print("="*70)
print("\nScenario: You own Pacific Avenue and want to buy North Carolina Avenue")
print("This would complete the Green monopoly!")
print()

# Common configuration
property_name = "North Carolina Avenue"
your_cash = 3500
your_position = 20
your_properties = [31]  # Pacific Avenue
opponents = [
    {
        'name': 'Player 2',
        'cash': 1800,
        'position': 5,
        'properties': [1, 3],
        'risk_tolerance': 0.3
    },
    {
        'name': 'Player 3',
        'cash': 2200,
        'position': 10,
        'properties': [5, 15],
        'risk_tolerance': 0.5
    },
    {
        'name': 'Player 4',
        'cash': 1500,
        'position': 20,
        'properties': [],
        'risk_tolerance': 0.6
    }
]

print("="*70)
print("SCENARIO 1: WITHOUT House Building (Current Implementation)")
print("="*70)
print("Running 1000 simulations...")

analysis_no_houses = run_property_analysis(
    property_name=property_name,
    your_cash=your_cash,
    your_position=your_position,
    your_properties=your_properties,
    opponents=opponents,
    num_simulations=1000,
    max_turns=200,
    enable_house_building=False  # ← No house building
)

print("\n" + "="*70)
print("SCENARIO 2: WITH House Building (NEW!)")
print("="*70)
print("Running 1000 simulations with house building enabled...")

analysis_with_houses = run_property_analysis(
    property_name=property_name,
    your_cash=your_cash,
    your_position=your_position,
    your_properties=your_properties,
    opponents=opponents,
    num_simulations=1000,
    max_turns=200,
    enable_house_building=True  # ← WITH house building!
)

# Compare results
print("\n" + "="*70)
print("COMPARISON SUMMARY")
print("="*70)

print(f"\n{'Metric':<30} {'WITHOUT Houses':<20} {'WITH Houses':<20} {'Improvement':<15}")
print("-"*85)

# NPV
npv_no = analysis_no_houses['npv_mean']
npv_yes = analysis_with_houses['npv_mean']
npv_improvement = ((npv_yes - npv_no) / abs(npv_no) * 100) if npv_no != 0 else 0
print(f"{'Net Present Value':<30} ${npv_no:>17,.0f}  ${npv_yes:>17,.0f}  {npv_improvement:>13.1f}%")

# ROI
roi_no = analysis_no_houses['roi']
roi_yes = analysis_with_houses['roi']
roi_improvement = roi_yes - roi_no
print(f"{'Return on Investment':<30} {roi_no:>17.1f}%  {roi_yes:>17.1f}%  {roi_improvement:>13.1f} pts")

# Total Rent
rent_no = analysis_no_houses['expected_total_rent']
rent_yes = analysis_with_houses['expected_total_rent']
rent_improvement = ((rent_yes - rent_no) / rent_no * 100) if rent_no > 0 else 0
print(f"{'Expected Total Rent':<30} ${rent_no:>17,.0f}  ${rent_yes:>17,.0f}  {rent_improvement:>13.1f}%")

# Payback
payback_no = analysis_no_houses.get('payback_mean_turns')
payback_yes = analysis_with_houses.get('payback_mean_turns')
if payback_no and payback_yes:
    payback_improvement = payback_no - payback_yes
    print(f"{'Payback Period (turns)':<30} {payback_no:>17.1f}  {payback_yes:>17.1f}  {payback_improvement:>13.1f}")
elif payback_yes and not payback_no:
    print(f"{'Payback Period (turns)':<30} {'Never':>17}  {payback_yes:>17.1f}  {'Now viable!':>13}")
else:
    print(f"{'Payback Period (turns)':<30} {'N/A':>17}  {'N/A':>17}  {'N/A':>13}")

# Recommendation
rec_no = analysis_no_houses['recommendation']
rec_yes = analysis_with_houses['recommendation']
print(f"\n{'Recommendation':<30} {rec_no:>17}  {rec_yes:>17}")

print("\n" + "="*70)
print("KEY INSIGHTS")
print("="*70)

if npv_yes > npv_no:
    improvement_amount = npv_yes - npv_no
    print(f"\n✨ House building TRANSFORMS this investment!")
    print(f"   NPV improves by ${improvement_amount:,.0f} ({abs(npv_improvement):.0f}% better)")
    print(f"   ROI goes from {roi_no:.1f}% to {roi_yes:.1f}%")
    
    if roi_yes > 50:
        print(f"\n🏆 With houses, this becomes a PROFITABLE investment!")
    
    print(f"\n💡 Why? Houses multiply rent by 5-49x!")
    print(f"   Base rent: $26")
    print(f"   With monopoly: $52")
    print(f"   With 1 house: $130 (5x base)")
    print(f"   With hotel: $1,275 (49x base!)")
    
    print(f"\n📊 Players with monopolies automatically build houses")
    print(f"   This generates MUCH more rent over the game")

else:
    print(f"\nHouse building didn't improve results significantly.")
    print(f"Possible reasons:")
    print(f"  - Not enough time to build houses")
    print(f"  - Other players also building houses (competition)")
    print(f"  - Games ending before houses pay off")

print("\n" + "="*70)
