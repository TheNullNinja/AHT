from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional, List, Any, DefaultDict
from analysis.aht_analysis import (
    load_calls,
    calculate_aht,
    get_long_calls,
    top_contact_reasons,
    get_call_event_bottlenecks,
    customer_level_insights
)
from rag.recommendation import get_recommendations, llm as recommendation_llm
from analysis.simulation import simulate_aht_reduction
from feedback.feedback_loop import (
    save_feedback,
    summarize_feedback,
    retrain_faiss_with_feedback
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model before serving requests"""
    print("Warming up LLM...")
    # Warm up the model with a short prompt
    recommendation_llm.invoke("Telecom customer service assistant warm up")
    print("Model ready to serve requests")
    yield  # App runs here
    # Optional cleanup at shutdown
    print("Shutting down model")

app = FastAPI(title="Telecom Intelligence RAG API", lifespan=lifespan)

class CallData(BaseModel):
    notes: str
    reason: str
    events: List[Dict[str, Any]]  # Added event structure
    call_id: str  # Added call_id for consistency
    duration: Optional[float] = None


class FeedbackItem(BaseModel):
    call_id: str
    context: str
    recommendation: str
    score: int
    original_duration: float
    new_duration: float
    comment: Optional[str] = None


@app.post("/recommendations", response_model=Dict[str, Any])
def get_recommendations_endpoint(call: CallData):
    """Generate recommendations based on call notes and reason"""
    query = f"{call.notes}\nReason: {call.reason}"
    result = get_recommendations(query)
    call_dict = {
        "events": call.events,
        "call_id": call.call_id,
        "duration": call.duration,
        "reason": call.reason,
        "notes": call.notes
    }
    try:
        bottleneck = get_call_event_bottlenecks(call_dict)
    except Exception as e:
        bottleneck = {"error": str(e)}
    
    return {
        "recommendations": result,
        "bottleneck": bottleneck
    }

'''Provides a comprehensive summary of Average Handling Time (AHT) metrics across all calls'''
@app.get("/aht/summary", response_model=Dict[str, Any])
def aht_summary(cost_per_call: float = Query(8.0, gt=0, description="Operational cost per call in dollars")):
    """Get AHT summary statistics"""
    calls = load_calls()
    aht = calculate_aht(calls)
    long_calls = get_long_calls(calls)
    top_reasons = top_contact_reasons(long_calls)

    long_call_duration = sum(call['duration'] for call in long_calls)
    potential_savings = (long_call_duration * 0.5) / 3600 * (cost_per_call / 3600) * 4
    
    return {
        "average_aht": round(aht, 2),
        "long_calls_count": len(long_calls),
        "long_calls_percentage": round(len(long_calls) / len(calls) * 100, 2),
        "top_contact_reasons": top_reasons,
        "estimated_annual_savings": round(potential_savings, 2),
        "cost_per_call": cost_per_call,
        "notes": "Savings assume 50% reduction in long call durations"
    }

'''For contact-specific insights , sample : GET /aht/reason/Billing%20Inquiry'''
@app.get("/aht/reason/{contact_reason}")
async def get_reason_insights(contact_reason: str):
    calls = load_calls()
    reason_calls = [c for c in calls if c['reason'].lower() == contact_reason.lower()]
    
    if not reason_calls:
        raise HTTPException(404, detail="Contact reason not found")
    
    # Get bottlenecks specific to this reason
    bottlenecks = DefaultDict(list)
    for call in reason_calls:
        if 'events' in call:
            bottle = get_call_event_bottlenecks(call)
            if bottle and "longest_segment" in bottle:
                segment = bottle["longest_segment"]
                key = f"{segment['from']} → {segment['to']}"
                bottlenecks[key].append(segment['duration'])
    
    # Average bottleneck durations
    avg_bottlenecks = [{
        "transition": k,
        "avg_duration": sum(v)/len(v)
    } for k, v in bottlenecks.items()]
    
    # Get customer insights
    cust_insights = customer_level_insights(reason_calls)
    top_customers = sorted(
        [(k, v) for k, v in cust_insights.items()],
        key=lambda x: x[1]['total_calls'],
        reverse=True
    )[:5]
    
    return {
        "contact_reason": contact_reason,
        "total_calls": len(reason_calls),
        "average_duration": calculate_aht(reason_calls),
        "long_calls": len(get_long_calls(reason_calls)),
        "customer_insights": {"top_customers": top_customers},
        "bottlenecks": avg_bottlenecks,
        "recommendations": get_recommendations(f"Reduce AHT for {contact_reason}")
    }


@app.get("/aht/details/{call_id}", response_model=Dict[str, Any])
def aht_details(call_id: str):
    try:
        """Get AHT details for a specific call"""
        calls = load_calls()
        call = next((c for c in calls if str(c.get("call_id", "")) == call_id), None)
    
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
    
         # Get call details
        details = {
            "call_id": call.get("call_id", "N/A"),
            "customer_id": call.get("customer", {}).get("customer_id", "N/A"),
            "reason": call.get("reason", "Unknown"),
            "duration": call.get("duration", 0),
            "agent_id": call.get("agent", {}).get("agent_id", "N/A"),
            "timestamp": call.get("timestamp", "Not recorded")
        }

     # Get bottlenecks if events exist
        if "events" in call and isinstance(call["events"], list):
            try:
                details["bottlenecks"] = get_call_event_bottlenecks(call)
            except Exception as e:
                details["bottlenecks"] = f"Analysis error: {str(e)}"
        else:
            details["bottlenecks"] = "No event data available"
    
        # Get AI recommendations
        query = f"Call {call_id}: {details['reason']} (Duration: {details['duration']}s)"
        try:
            details["recommendations"] = get_recommendations(query)
        except Exception as e:
            details["recommendations"] = [f"Could not generate recommendations: {str(e)}"]
            
        return details
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/customer/insights/{customer_id}", response_model=Dict[str, Any])
def customer_insights(customer_id: str):
    """Get insights for a specific customer"""
    calls = load_calls()
    insights = customer_level_insights(calls)
    
    if customer_id not in insights:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return insights[customer_id]


@app.post("/feedback/save", response_model=Dict[str, str])
def save_feedback_endpoint(feedback: FeedbackItem):
    """Save user feedback"""
    if feedback.score < 1 or feedback.score > 5:
        raise HTTPException(
            status_code=400,
            detail="Score must be between 1 and 5"
        )
    
    save_feedback(
        call_id=feedback.call_id,
        context=feedback.context,
        recommendation=feedback.recommendation,
        score=feedback.score,
        original_duration=feedback.original_duration,
        new_duration=feedback.new_duration, 
        comment=feedback.comment
    )
    
    return {"message": "Feedback saved with effectiveness metrics"}


@app.get("/feedback/summary", response_model=Dict[str, Any])
def get_feedback_summary():
    """Get feedback summary"""
    return summarize_feedback()


@app.post("/feedback/retrain", response_model=Dict[str, str])
def retrain_model():
    """Retrain the FAISS index with new feedback"""
    message = retrain_faiss_with_feedback()
    return {"message": message}


'''The /aht/simulation endpoint performs a what-if analysis to estimate the potential impact of implementing recommendations on call handling efficiency. 
Here's what it does and how it works:
Purpose:
Business Impact Forecasting: Estimates potential cost savings from reducing Average Handling Time (AHT)
ROI Calculation: Helps justify investments in process improvements
Scenario Planning: Allows testing different improvement scenarios

How It Works:
Parameters:
improvement_factor (% reduction in long call durations)
Example: 0.5 = 50% reduction
cost_per_call (operational cost per call in dollars)

Calculation Process: calls simulate_aht_reduction'''

@app.get("/aht/simulation", response_model=Dict[str, Any])
def aht_simulation(
    improvement_factor: float = Query(0.5, gt=0, le=1, description="% reduction in long call durations"),
    cost_per_call: float = Query(8.0, gt=0, description="Operational cost per call in dollars")
):
    """Simulate AHT reduction and cost savings after implementing recommendations"""
    return simulate_aht_reduction(
        improvement_factor=improvement_factor,
        cost_per_call=cost_per_call
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)