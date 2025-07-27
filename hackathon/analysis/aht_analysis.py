from collections import Counter, defaultdict
from datetime import datetime
import json
from typing import Any, Dict, List
from feedback.feedback_loop import load_feedback

AHT_THRESHOLD = 530  # seconds


def parse_timestamp(timestamp: str) -> datetime:
    try:
        # Try with milliseconds first
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        # Fallback to format without milliseconds
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


def load_calls(file_path: str = "data/telecom_calls.jsonl") -> List[Dict[str, Any]]:
    calls = []
    with open(file_path, "r") as file:
        for line in file:
            try:
                call = json.loads(line)
                # Validate required fields
                if "call_id" not in call:
                    continue  # Skip invalid records
                calls.append(call)
            except json.JSONDecodeError:
                continue  # Skip malformed lines
    return calls

def calculate_aht(calls: List[Dict[str, Any]]) -> float:
    total_duration = sum(call["duration"] for call in calls)
    total_calls = len(calls)
    return total_duration / total_calls if total_calls > 0 else 0.0


def get_long_calls(calls: List[Dict[str, Any]], threshold: int = AHT_THRESHOLD) -> List[Dict[str, Any]]:
    return [call for call in calls if call["duration"] > threshold]


def top_contact_reasons(
    calls: List[Dict[str, Any]], top_n: int = 5
) -> List[Dict[str, Any]]:
    reasons = [call["reason"] for call in calls]
    return Counter(reasons).most_common(top_n)


def get_call_event_bottlenecks(call: Dict[str, Any]) -> Dict[str, Any]:
    events = call.get("events", [])
    if len(events) < 2:
        return {}
    
    bottlenecks = []
    for i in range(1, len(events)):
        prev_event = events[i-1]
        curr_event = events[i]
        
        # Check for required fields in both events
        if "timestamp" not in prev_event or "timestamp" not in curr_event:
            continue  # Skip if either event is missing timestamp
        if "event_type" not in prev_event or "event_type" not in curr_event:
            continue  # Skip if either event is missing event_type
            
        try:
            start_time = parse_timestamp(prev_event["timestamp"])
            end_time = parse_timestamp(curr_event["timestamp"])
            duration = (end_time - start_time).total_seconds()
            
            bottlenecks.append({
                "from": prev_event["event_type"],
                "to": curr_event["event_type"],
                "duration": duration
            })
        except (KeyError, ValueError) as e:
            # Log error and continue processing
            print(f"Error processing event timestamps: {str(e)}")
            continue
    
    if not bottlenecks:
        return {}
    
    slowest_bottleneck = max(bottlenecks, key=lambda x: x["duration"])
    return {"longest_segment": slowest_bottleneck}


def customer_level_insights(
    calls: List[Dict[str, Any]], threshold: int = 50
) -> Dict[str, Dict[str, float]]:
    customer_insights = defaultdict(lambda: {
        "total_calls": 0,
        "total_duration": 0,
        "short_call": 0
    })
    
    for call in calls:
        customer_id = call["customer"]["customer_id"]
        customer_insights[customer_id]["total_calls"] += 1
        customer_insights[customer_id]["total_duration"] += call["duration"]
        if call["duration"] < threshold:
            customer_insights[customer_id]["short_call"] += 1
    
    for cust in customer_insights:
        total = customer_insights[cust]["total_calls"]
        short = customer_insights[cust]["short_call"]
        customer_insights[cust]["short_call_percentage"] = round((short / total) * 100, 2) if total > 0 else 0

    return dict(customer_insights)

def analyze_recommendation_effectiveness() -> dict:
    """Calculate effectiveness of recommendations"""
    feedback_list = load_feedback()  # From feedback_loop.py
    
    if not feedback_list:
        return {}
    
    # Calculate overall effectiveness
    total_original = sum(fb["original_duration"] for fb in feedback_list)
    total_new = sum(fb["new_duration"] for fb in feedback_list)
    total_reduction = total_original - total_new
    avg_reduction = total_reduction / len(feedback_list)
    
    # Group by recommendation type
    effectiveness_by_type = {}
    for fb in feedback_list:
        # Extract first recommendation point (simplified)
        first_rec = fb["recommendation"].split("\n")[0].strip()
        key = first_rec[:50] + "..." if len(first_rec) > 50 else first_rec
        
        if key not in effectiveness_by_type:
            effectiveness_by_type[key] = {
                "count": 0,
                "total_red": 0,
                "scores": []
            }
        
        effectiveness_by_type[key]["count"] += 1
        effectiveness_by_type[key]["total_red"] += fb["duration_reduction"]
        effectiveness_by_type[key]["scores"].append(fb["score"])
    
    # Calculate averages
    for key, data in effectiveness_by_type.items():
        data["avg_duration_red"] = data["total_red"] / data["count"]
        data["avg_score"] = sum(data["scores"]) / len(data["scores"])
    
    return {
        "total_calls": len(feedback_list),
        "total_duration_reduction": total_reduction,
        "avg_duration_reduction": avg_reduction,
        "effectiveness_by_recommendation": effectiveness_by_type
    }