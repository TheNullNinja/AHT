import json
import os
from pathlib import Path
from typing import List, Dict
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

FEEDBACK_FILE = Path("data/feedback.jsonl")

# Create the embeddings model once (module-level)
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")

# Initialize index directory
index_dir = "data/retriever_db"
os.makedirs(index_dir, exist_ok=True)

def save_feedback(
    call_id: str,
    context: str,
    recommendation: str,
    score: int,
    original_duration: int,  # New field
    new_duration: int,       # New field
    comment: str = ""
) -> None:
    """Save user feedback to a JSONL file."""
    duration_reduction = original_duration - new_duration
    percent_reduction = (duration_reduction / original_duration * 100) if original_duration > 0 else 0
    feedback = {
        "call_id": call_id,
        "context": context,
        "recommendation": recommendation,
        "score": score,
        "original_duration": original_duration,
        "new_duration": new_duration,
        "duration_reduction": duration_reduction,
        "percent_reduction": round(percent_reduction, 2),
        "comment": comment
    }
    
    with FEEDBACK_FILE.open("a") as f:
        f.write(json.dumps(feedback) + "\n")


def load_feedback() -> List[Dict]:
    """Load all feedback entries from JSONL file."""
    if not FEEDBACK_FILE.exists():
        return []
    
    with FEEDBACK_FILE.open("r") as f:
        return [json.loads(line) for line in f]


def summarize_feedback() -> Dict[str, any]:
    """Generate summary statistics with effectiveness metrics."""
    feedback_list = load_feedback()
    
    if not feedback_list:
        return {
            "total": 0,
            "average_score": 0.0,
            "avg_duration_reduction": 0.0,
            "avg_percent_reduction": 0.0,
            "high_quality": [],
            "low_quality": []
        }
    
    total = len(feedback_list)
    avg_score = sum(fb["score"] for fb in feedback_list) / total
    avg_duration_red = sum(fb["duration_reduction"] for fb in feedback_list) / total
    avg_percent_red = sum(fb["percent_reduction"] for fb in feedback_list) / total
    
    return {
        "total": total,
        "average_score": round(avg_score, 2),
        "avg_duration_reduction": round(avg_duration_red, 2),
        "avg_percent_reduction": round(avg_percent_red, 2),
        "low_quality": sorted(feedback_list, key=lambda x: x["score"])[:3],
        "high_quality": sorted(feedback_list, key=lambda x: x["percent_reduction"], reverse=True)[:3]
    }


def get_positive_feedback_contexts(min_score: int = 4, min_reduction: float = 10.0 ) -> List[Dict]:
    """Retrieve positive feedback entries above a minimum score."""
    return [
        {
            "call_id": fb["call_id"],
            "context": fb["context"],
            "recommendation": fb["recommendation"],
            "percent_reduction": fb["percent_reduction"]
        }
        for fb in load_feedback()
        if fb["score"] >= min_score and fb["percent_reduction"] >= min_reduction
    ]


def retrain_faiss_with_feedback() -> str:
    """Update FAISS index with positive feedback entries."""

    entries = get_positive_feedback_contexts()
    
    if not entries:
        return "No positive feedback to update FAISS index."
    
    # Create document objects for FAISS
    texts = [
        Document(
            page_content=(
                f"Context: {entry['context']}\n"
                f"Recommendation: {entry['recommendation']}"
            )
        )
        for entry in entries
    ]
    
    try:
        db = FAISS.load_local(
            index_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"Creating new index because: {str(e)}")
        db = FAISS.from_documents(texts, embeddings)
        db.save_local(index_dir)
        return f"Created new FAISS index with {len(texts)} entries"
    
    # Add new documents to existing index
    db.add_documents(texts)
    db.save_local(index_dir)
    
    return f"Updated FAISS index with {len(texts)} positive feedback entries."