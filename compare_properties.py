#!/usr/bin/env python3
"""
Compare multiple properties to find the best investment
"""

from main import run_property_analysis

# Properties to compare
properties_to_test = [
    "Boardwalk",
    "Park Place",
    "Illinois Avenue",
    "New York Avenue",
    "North Carolina Avenue",
    "Reading Railroad",
    "B&O Railroad"
]

print("\n" + "="*70)
print("PROPERTY INVESTMENT COMPARISON")
print("="*70)
print("\nRunning simulations for multiple properties...")
print("(This will take a few minutes)\n")

results = []

for i, prop_name in enumerate(properties_to_test, 1):
    print(f"[{i}/{len(properties_to_test)}] Analyzing {prop_name}...")
    
    try:
        analysis = run_property_analysis(
            property_name=prop_name,
            your_cash=3500,
            your_position=0,
            your_properties=[],
            opponents=[
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
            ],
            num_simulations=500,  # Fewer simulations for speed
            max_turns=150
        )
        
        results.append({
            'property': prop_name,
            'price': analysis['purchase_price'],
            'npv': analysis['npv_mean'],
            'roi': analysis['roi'],
            'payback': analysis['payback_mean_turns'],
            'rent': analysis['expected_total_rent'],
            'recommendation': analysis['recommendation']
        })
        
    except Exception as e:
        print(f"   Error analyzing {prop_name}: {e}")
        continue

# Print comparison table
print("\n" + "="*70)
print("INVESTMENT COMPARISON SUMMARY")
print("="*70)
print(f"\n{'Property':<25} {'Price':>8} {'NPV':>10} {'ROI':>8} {'Rent':>8} {'Decision':>12}")
print("-"*70)

# Sort by NPV (best investment first)
for r in sorted(results, key=lambda x: x['npv'], reverse=True):
    print(f"{r['property']:<25} ${r['price']:>7,.0f} ${r['npv']:>9,.0f} "
          f"{r['roi']:>7.1f}% ${r['rent']:>7,.0f}  {r['recommendation']:>12}")

print("\n" + "="*70)
print("\n💡 Best Investment (by NPV):")
best = max(results, key=lambda x: x['npv'])
print(f"   {best['property']} - NPV: ${best['npv']:,.0f}, ROI: {best['roi']:.1f}%")

print("\n📊 Results saved! Use this data for your analytics cards.")
