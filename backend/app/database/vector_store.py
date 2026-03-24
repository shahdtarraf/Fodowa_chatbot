"""
FAISS vector-store loader.

PRODUCTION ARCHITECTURE:
- Uses HuggingFace Inference API for embeddings (lightweight, no local model)
- Consistent embeddings between ingestion and retrieval
- FAISS index must be pre-built locally using ingest_data.py
"""

from typing import Optional
import os
import pickle

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceInferenceEmbeddings

from app.utils.config import FAISS_INDEX_PATH, HF_EMBEDDING_MODEL, HUGGINGFACEHUB_API_TOKEN
from app.utils.logger import logger

# Module-level singleton — populated by ``load_vector_store()``.
_vector_store: Optional[FAISS] = None


def load_vector_store() -> Optional[FAISS]:
    """
    Load the pre-built FAISS index from disk.
    
    Uses HuggingFaceInferenceAPIEmbeddings for:
    - Accurate semantic search (same embeddings used during ingestion)
    - Lightweight runtime (no local model loading, ~0MB RAM)
    - Consistency with ingest_data.py
    """
    global _vector_store

    # Check if index directory exists
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.warning("FAISS index directory '%s' does not exist.", FAISS_INDEX_PATH)
        return None

    # Check for required FAISS files
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        logger.warning("FAISS index files not found in '%s'.", FAISS_INDEX_PATH)
        return None

    logger.info("Loading FAISS index from '%s' …", FAISS_INDEX_PATH)
    try:
        # Validate API token
        if not HUGGINGFACEHUB_API_TOKEN:
            logger.error("HUGGINGFACEHUB_API_TOKEN not set. Cannot load FAISS index.")
            return None
        
        # Use HuggingFace Inference API - lightweight, accurate embeddings
        # Must match the embeddings used during ingestion
        logger.info("Initializing HuggingFace embeddings (model: %s)...", HF_EMBEDDING_MODEL)
        embeddings = HuggingFaceInferenceEmbeddings(
            model_name=HF_EMBEDDING_MODEL,
            huggingface_api_token=HUGGINGFACEHUB_API_TOKEN,
        )
        
        logger.info("Loading FAISS index from disk...")
        
        # Load FAISS index manually to avoid Pydantic v1/v2 pickle issues
        import faiss
        index = faiss.read_index(index_file)
        
        # Load docstore with Pydantic v2 compatibility
        with open(pkl_file, "rb") as f:
            data = pickle.load(f)
        
        # Reconstruct vector store
        _vector_store = FAISS(
            embedding_function=embeddings.embed_query,
            index=index,
            docstore=data.get("docstore") if isinstance(data, dict) else data[0],
            index_to_docstore_id=data.get("index_to_docstore_id") if isinstance(data, dict) else data[1],
        )
        
        logger.info("✅ FAISS index loaded successfully (%d vectors).", _vector_store.index.ntotal)
        return _vector_store
    except Exception as exc:
        logger.error("❌ Failed to load FAISS index: %s", exc, exc_info=True)
        return None


def get_vector_store() -> Optional[FAISS]:
    """Return the cached vector-store instance (may be ``None`` if not loaded)."""
    return _vector_store
