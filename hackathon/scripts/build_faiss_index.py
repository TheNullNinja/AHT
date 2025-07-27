# hackaton/scripts/build_faiss_index.py

import os
import json
from pathlib import Path
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.schema import Document
from tqdm import tqdm

DATA_FILE = Path("data/telecom_calls.jsonl")
INDEX_DIR = "data/retriever_db"

def load_calls(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found.")
    with open(file_path, "r") as f:
        return [json.loads(line) for line in f]

def build_documents(calls):
    docs = []
    for call in calls:
        context = call.get("notes", "")
        reason = call.get("reason", "")
        customer_id = call.get("customer", {}).get("customer_id", "unknown")
        doc_text = f"Customer ID: {customer_id}\nReason: {reason}\nNotes: {context}"
        docs.append(Document(page_content=doc_text))
    return docs

def main():
    print("Loading call data...")
    calls = load_calls(DATA_FILE)

    print(f"Building {len(calls)} documents...")
    documents = build_documents(calls)

    print("Generating embeddings...")
    embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en-v1.5")

    print("Building FAISS index...")
    db = FAISS.from_documents(documents, embeddings)

    print(f"Saving FAISS index to {INDEX_DIR}")
    db.save_local(INDEX_DIR)
    print(" Done.")

if __name__ == "__main__":
    main()
