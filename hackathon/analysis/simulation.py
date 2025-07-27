# hackaton/analysis/simulation.py
import json
from pathlib import Path
from analysis.aht_analysis import load_calls, calculate_aht, get_long_calls, top_contact_reasons

def simulate_aht_reduction(data_path: str = "data/telecom_calls.jsonl", 
                          improvement_factor: float = 0.5,
                          cost_per_call: float = 8.0) -> dict:
    """
    Simulate AHT reduction and cost savings after implementing recommendations
    Args:
        improvement_factor: % reduction in long call durations (0.5 = 50% reduction)
        cost_per_call: Operational cost per call in dollars
    Returns:
        Dictionary with simulation results
    """
    # Load original data
    calls = load_calls(data_path)
    original_aht = calculate_aht(calls)
    long_calls = get_long_calls(calls)
    top_reasons = top_contact_reasons(long_calls, top_n=10)
    
    # Create simulated calls with reduced duration for long calls
    simulated_calls = []
    long_call_ids = {call['call_id'] for call in long_calls}
    
    for call in calls:
        if call['call_id'] in long_call_ids:
            # Apply improvement factor to long calls
            modified_call = call.copy()
            modified_call['duration'] = call['duration'] * (1 - improvement_factor)
            simulated_calls.append(modified_call)
        else:
            simulated_calls.append(call)
    
    # Calculate new metrics
    new_aht = calculate_aht(simulated_calls)
    new_long_calls = get_long_calls(simulated_calls)
    
    # Calculate savings
    reduction_per_call = sum(call['duration'] for call in long_calls) * improvement_factor
    total_savings = reduction_per_call / 3600 * (cost_per_call / 3600)  # Convert to hours
    
    return {
        "original_aht": original_aht,
        "new_aht": new_aht,
        "aht_reduction": original_aht - new_aht,
        "reduction_percentage": (original_aht - new_aht) / original_aht * 100,
        "original_long_calls": len(long_calls),
        "new_long_calls": len(new_long_calls),
        "estimated_annual_savings": total_savings * 4,  # Quarterly to annual
        "improvement_factor": improvement_factor,
        "cost_per_call": cost_per_call,
        "top_contact_reasons": top_reasons
    }

if __name__ == "__main__":
    results = simulate_aht_reduction()
    print("AHT Simulation Results:")
    print(f"Original AHT: {results['original_aht']:.2f} seconds")
    print(f"New AHT: {results['new_aht']:.2f} seconds")
    print(f"Reduction: {results['aht_reduction']:.2f} seconds ({results['reduction_percentage']:.2f}%)")
    print(f"Long calls reduced: {results['original_long_calls']} → {results['new_long_calls']}")
    print(f"Estimated Annual Savings: ${results['estimated_annual_savings']:,.2f}")
    print("\nTop Contact Reasons for Long Calls:")
    for reason, count in results['top_contact_reasons']:
        print(f"- {reason}: {count} calls")