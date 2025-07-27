# test_model_debug.py
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from rag.recommendation import llm
    print("Successfully imported llm")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

print("\n Model configuration:")
print(f"Model path: {llm.model_path}")
print(f"Context size: {llm.n_ctx}")
print(f"Threads: {llm.n_threads}")
print(f"Batch size: {llm.n_batch}")

print("\nTesting model inference...")
start_time = time.time()

try:
    prompt = "how telecom company works?"
    print(f"\n Prompt: '{prompt}'")
    response = llm.invoke(prompt, max_tokens=20)
    elapsed = time.time() - start_time
    
    print(f"\nResponse received in {elapsed:.2f} seconds:")
    print(response)
except Exception as e:
    print(f"\nInference error: {e}")
    import traceback
    traceback.print_exc()