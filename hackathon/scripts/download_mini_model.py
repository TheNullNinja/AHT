# scripts/download_mini_model.py
import os
from huggingface_hub import hf_hub_download
from pathlib import Path

# Set your token here
HF_TOKEN = "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"  # Replace with your actual token

def download_model():
    MODEL_NAME = "TheBloke/Llama-3-7B-Instruct-GGUF"
    MODEL_FILE = "llama-3-7b-instruct.Q4_K_M.gguf"
    LOCAL_DIR = Path("models")
    
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = hf_hub_download(
        repo_id=MODEL_NAME,
        filename=MODEL_FILE,
        local_dir=LOCAL_DIR,
        token=HF_TOKEN 
    )
    print(f"✅ Model downloaded to {model_path}")

if __name__ == "__main__":
    download_model()