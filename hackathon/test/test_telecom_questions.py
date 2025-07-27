import sys
import os
import time
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.recommendation import get_recommendations
from feedback.feedback_loop import save_feedback

questions = [
    {
        "notes": "Customer reports slow internet speeds between 7-10 PM daily",
        "reason": "network congestion"
    },
    {
        "notes": "Customer was charged $50 extra for international roaming they didn't use",
        "reason": "billing dispute"
    },
    # Add all 10 questions here
]

for i, q in enumerate(questions, 1):
    print(f"\nQuestion {i}: {q['reason'].upper()}")
    print(f"   {q['notes']}")
    query = f"{q['notes']}\nReason: {q['reason']}"
    
    # Simulate original call duration (random for testing)
    original_duration = random.randint(300, 800)  # 5-13 minutes
    
    response = get_recommendations(query)
    
    # Simulate new call duration after recommendation
    # In real system, agent would record actual duration
    new_duration = max(original_duration * random.uniform(0.3, 0.8), 60)  # 30-70% reduction
    
    print(f"Recommendation:")
    print(response)
    print("-" * 80)
    
    # Save feedback with duration metrics
    save_feedback(
        call_id=f"test_{i}",
        context=q['notes'],
        recommendation=response,
        score=random.randint(3,5),  # Simulated score
        original_duration=original_duration,
        new_duration=new_duration
    )