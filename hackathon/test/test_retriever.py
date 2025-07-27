# test/test_retriever.py
import sys
import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.retriever import get_retriever

retriever = get_retriever()
query = "customer has slow internet issue"
docs = retriever.invoke(query)

print("\nTop 5 relevant documents:\n")
for i, doc in enumerate(docs, 1):
    print(f"{i}. {doc.page_content[:200]}...\n")
