from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def get_retriever():
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"}
    )
    
    # Load FAISS index
    vector_store = FAISS.load_local(
        "data/retriever_db",
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    return vector_store.as_retriever(
        search_kwargs={"k": 5}
    )