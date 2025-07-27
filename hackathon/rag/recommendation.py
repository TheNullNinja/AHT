from pathlib import Path
import os
from rag.retriever import get_retriever
from langchain_community.llms import LlamaCpp

# Get absolute path to model
BASE_DIR = Path(__file__).resolve().parent.parent  # Points to hackathon directory
MODEL_DIR = BASE_DIR / "models"
MODEL_FILE = "Phi-3-mini-4k-instruct-q4.gguf"
MODEL_PATH = str(MODEL_DIR / MODEL_FILE)

# Verify model exists
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at: {MODEL_PATH}")

llm = LlamaCpp(
    model_path=MODEL_PATH,
    n_ctx=2048,          # Reduced context size
    n_threads=8,         # Use all CPU cores
    n_gpu_layers=0,      # Disable GPU acceleration
    n_batch=256,         # Smaller batches
    max_tokens=256,      # Shorter responses
    temperature=0.2,     # More deterministic responses
    verbose=True,
    seed=42              # For reproducibility
)

def get_recommendations(query: str) -> str:
    retriever = get_retriever()
    docs = retriever.invoke(query)
    context = "\n---\n".join([doc.page_content for doc in docs])
    
    # prompt = f"""
    # You are an expert in telecom customer service and helpful AI assistant. 
    # Based on the following call summary, provide recommendations for improving customer service:
    # {query}

    # And here is the context from previous calls:
    # {context}

    # Provide actionable recommendations to improve customer service and reduce Average Handling Time (AHT). 
    # Use the context to support your suggestions. Be specific and provide concrete steps.
    # """

    prompt = f"""<|system|>
    You are a telecom customer service expert. Provide exact actionable recommendations to reduce Average Handling Time (AHT) for the given issue. 
    Be specific and provide concrete prioritize solutions that:
    1.Can be implemented immediately
    2. Address the root cause
    3. Prevent recurrence
    Format response as numbered points only. No explanations needed.<|end|>
    <|user|>
    ISSUE: {query}
    CONTEXT: {context}<|end|>
    <|assistant|>"""
    
    response = llm.invoke(prompt, 
                        max_tokens=200, 
                        temperature=0.1,  
                        repeat_penalty=1.2,  
                        stop=["<|end|>", "\n\n"]
                    )  
    
    return response.strip()