"""
Financial analytics calculator for simulation results
"""
import numpy as np
from typing import Dict, List
import numpy_financial as npf

def calculate_npv(cash_flows: List[float], discount_rate: float = 0.05) -> float:
    """
    Calculate Net Present Value
    
    Args:
        cash_flows: List of cash flows by period (turn)
        discount_rate: Discount rate per turn (default 5% = 0.05)
    
    Returns:
        NPV value
    """
    npv = 0
    for t, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate) ** t)
    return npv


def calculate_irr(cash_flows: List[float]) -> float:
    """
    Calculate Internal Rate of Return
    
    Args:
        cash_flows: List of cash flows by period
    
    Returns:
        IRR as a decimal (e.g., 0.15 = 15%)
    """
    try:
        return npf.irr(cash_flows)
    except:
        return 0.0


def calculate_roi(initial_investment: float, total_return: float) -> float:
    """
    Calculate Return on Investment
    
    Args:
        initial_investment: Initial cost
        total_return: Total returns received
    
    Returns:
        ROI as a percentage
    """
    if initial_investment == 0:
        return 0
    return ((total_return - initial_investment) / initial_investment) * 100


def analyze_property_investment(simulation_stats: Dict, 
                                discount_rate: float = 0.05) -> Dict:
    """
    Calculate comprehensive financial metrics from simulation results
    
    Args:
        simulation_stats: Output from Monte Carlo simulation
        discount_rate: Discount rate for NPV calculation
    
    Returns:
        Dictionary with financial metrics
    """
    # Extract data
    purchase_price = simulation_stats['property_price']
    mean_rent_by_turn = simulation_stats['rent_by_turn_mean']
    total_rent_mean = simulation_stats['total_rent_mean']
    break_even_mean = simulation_stats['break_even_mean']
    break_even_distribution = simulation_stats['break_even_distribution']
    
    # Calculate NPV for mean cash flow
    cash_flows = [-purchase_price] + list(mean_rent_by_turn[1:])
    npv_mean = calculate_npv(cash_flows, discount_rate)
    
    # Calculate NPV distribution (sample from simulations)
    # For simplicity, we'll calculate NPV for different scenarios
    num_turns = len(mean_rent_by_turn)
    npv_samples = []
    
    # Generate sample NPVs using the percentile data
    p25_rent = simulation_stats['rent_by_turn_p25']
    p75_rent = simulation_stats['rent_by_turn_p75']
    
    # NPV at 25th percentile (pessimistic)
    cash_flows_p25 = [-purchase_price] + list(p25_rent[1:])
    npv_p25 = calculate_npv(cash_flows_p25, discount_rate)
    
    # NPV at 75th percentile (optimistic)  
    cash_flows_p75 = [-purchase_price] + list(p75_rent[1:])
    npv_p75 = calculate_npv(cash_flows_p75, discount_rate)
    
    # Calculate IRR
    irr_value = calculate_irr(cash_flows)
    
    # Calculate ROI
    roi_value = calculate_roi(purchase_price, total_rent_mean)
    
    # Payback period statistics
    payback_p50 = break_even_mean if break_even_mean > 0 else None
    payback_p25 = np.percentile(break_even_distribution, 25) if break_even_distribution else None
    payback_p75 = np.percentile(break_even_distribution, 75) if break_even_distribution else None
    
    # Expected value calculation
    expected_profit = total_rent_mean - purchase_price
    profit_margin = (expected_profit / purchase_price * 100) if purchase_price > 0 else 0
    
    # Risk metrics
    rent_volatility = simulation_stats['total_rent_std']
    coefficient_of_variation = (rent_volatility / total_rent_mean * 100) if total_rent_mean > 0 else 0
    
    # Recommendation logic
    def get_recommendation(npv, roi, break_even_rate, payback):
        if npv > purchase_price * 0.5 and roi > 100 and break_even_rate > 0.7:
            return "STRONG BUY", "Excellent value with high returns and reliable payback"
        elif npv > 0 and roi > 50 and break_even_rate > 0.5:
            return "BUY", "Positive returns with acceptable risk"
        elif npv > -purchase_price * 0.2 and break_even_rate > 0.3:
            return "HOLD", "Marginal returns, consider alternatives"
        else:
            return "PASS", "Poor returns or high risk"
    
    recommendation, reasoning = get_recommendation(
        npv_mean, roi_value, 
        simulation_stats['break_even_rate'], 
        payback_p50
    )
    
    return {
        # Core metrics
        'purchase_price': purchase_price,
        'expected_total_rent': total_rent_mean,
        'expected_profit': expected_profit,
        'profit_margin_pct': profit_margin,
        
        # NPV Analysis
        'npv_mean': npv_mean,
        'npv_p25': npv_p25,
        'npv_p75': npv_p75,
        'npv_distribution': [npv_p25, npv_mean, npv_p75],
        
        # IRR and ROI
        'irr': irr_value * 100,  # Convert to percentage
        'roi': roi_value,
        
        # Payback Analysis
        'payback_mean_turns': payback_p50,
        'payback_p25_turns': payback_p25,
        'payback_p75_turns': payback_p75,
        'break_even_probability': simulation_stats['break_even_rate'],
        
        # Risk Metrics
        'rent_volatility': rent_volatility,
        'coefficient_of_variation': coefficient_of_variation,
        'win_rate_with_property': simulation_stats['win_rate'],
        'bankruptcy_risk': simulation_stats['bankruptcy_rate'],
        
        # Recommendation
        'recommendation': recommendation,
        'reasoning': reasoning,
        
        # Cash flow data for visualization
        'cash_flow_mean': mean_rent_by_turn,
        'cash_flow_p25': p25_rent,
        'cash_flow_p75': p75_rent,
        'break_even_distribution': break_even_distribution,
    }


def format_analysis_report(property_name: str, analysis: Dict) -> str:
    """Generate a formatted text report"""
    
    # Handle None values
    payback_mean = analysis['payback_mean_turns']
    payback_p25 = analysis['payback_p25_turns']
    payback_p75 = analysis['payback_p75_turns']
    
    payback_mean_str = f"{payback_mean:.1f} turns" if payback_mean else "N/A (never broke even)"
    if payback_p25 and payback_p75:
        payback_range_str = f"{payback_p25:.1f} - {payback_p75:.1f} turns"
    else:
        payback_range_str = "N/A"
    
    report = f"""
{'='*70}
INVESTMENT ANALYSIS: {property_name}
{'='*70}

PURCHASE DECISION: {analysis['recommendation']}
Reasoning: {analysis['reasoning']}

FINANCIAL METRICS
{'─'*70}
Purchase Price:           ${analysis['purchase_price']:,.0f}
Expected Total Rent:      ${analysis['expected_total_rent']:,.0f}
Expected Profit:          ${analysis['expected_profit']:,.0f}
Profit Margin:            {analysis['profit_margin_pct']:.1f}%

NET PRESENT VALUE
{'─'*70}
NPV (Mean):               ${analysis['npv_mean']:,.0f}
NPV (25th percentile):    ${analysis['npv_p25']:,.0f}
NPV (75th percentile):    ${analysis['npv_p75']:,.0f}

RETURNS
{'─'*70}
Internal Rate of Return:  {analysis['irr']:.2f}%
Return on Investment:     {analysis['roi']:.1f}%

PAYBACK PERIOD
{'─'*70}
Mean Payback:             {payback_mean_str}
25th-75th Percentile:     {payback_range_str}
Break-Even Probability:   {analysis['break_even_probability']*100:.1f}%

RISK ASSESSMENT
{'─'*70}
Rent Volatility:          ${analysis['rent_volatility']:,.0f}
Coefficient of Variation: {analysis['coefficient_of_variation']:.1f}%
Win Rate with Property:   {analysis['win_rate_with_property']*100:.1f}%
Bankruptcy Risk:          {analysis['bankruptcy_risk']*100:.1f}%

{'='*70}
"""
    return report


# Test the analytics
if __name__ == '__main__':
    # Mock simulation stats for testing
    mock_stats = {
        'property_name': 'North Carolina Avenue',
        'property_price': 300,
        'num_simulations': 1000,
        'purchase_rate': 0.95,
        'break_even_mean': 12.5,
        'break_even_median': 11.0,
        'break_even_std': 4.2,
        'break_even_distribution': np.random.normal(12.5, 4.2, 800).tolist(),
        'break_even_rate': 0.80,
        'total_rent_mean': 875,
        'total_rent_median': 820,
        'total_rent_std': 245,
        'rent_by_turn_mean': np.array([-300, -280, -240, -180, -100, 0, 120, 260, 420, 600, 750, 875]),
        'rent_by_turn_std': np.array([0, 30, 45, 60, 75, 90, 110, 130, 150, 170, 190, 245]),
        'rent_by_turn_p25': np.array([-300, -290, -260, -210, -140, -50, 60, 180, 320, 480, 620, 730]),
        'rent_by_turn_p75': np.array([-300, -270, -220, -150, -60, 50, 180, 340, 520, 720, 880, 1020]),
        'win_rate': 0.35,
        'bankruptcy_rate': 0.05,
        'final_cash_mean': 1850
    }
    
    print("Testing Financial Analytics\n")
    
    analysis = analyze_property_investment(mock_stats, discount_rate=0.05)
    
    print(format_analysis_report('North Carolina Avenue', analysis))
    
    print("\nKey Metrics Summary:")
    print(f"  NPV: ${analysis['npv_mean']:,.0f}")
    print(f"  IRR: {analysis['irr']:.2f}%")
    print(f"  ROI: {analysis['roi']:.1f}%")
    print(f"  Payback: {analysis['payback_mean_turns']:.1f} turns")
    print(f"  Recommendation: {analysis['recommendation']}")
