import os
import sys
import requests
from pathlib import Path

MODEL_URL = "https://huggingface.co/TheBloke/Llama-3-7B-Instruct-GGUF/resolve/main/llama-3-7b-instruct.Q4_K_M.gguf"
MODEL_PATH = Path("hackaton/models/llama-3.1-7b.Q4_K_M.gguf")
MODEL_DIR = MODEL_PATH.parent

def download_model():
    print(f"Target model path: {MODEL_PATH}")
    
    if MODEL_PATH.exists():
        print("Model already exists. No download needed.")
        return

    print("Model not found. Starting download...")
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Stream the download to avoid memory overload
    with requests.get(MODEL_URL, stream=True) as r:
        r.raise_for_status()
        with open(MODEL_PATH, 'wb') as f:
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    done = int(50 * downloaded / total)
                    sys.stdout.write('\r[{}{}] {:.2f}%'.format(
                        '=' * done, ' ' * (50 - done), 100 * downloaded / total))
                    sys.stdout.flush()
    print("\n Download complete.")

if __name__ == "__main__":
    try:
        download_model()
    except requests.exceptions.HTTPError as e:
        print("Error downloading the model.")
        print("You may need to log in and accept the model license on Hugging Face:")
        print("https://huggingface.co/TheBloke/Llama-3-7B-Instruct-GGUF")
        print("Then use a personal access token if needed.")
        print("More info: https://huggingface.co/docs/huggingface_hub/guides/download#using-authentication-tokens")
