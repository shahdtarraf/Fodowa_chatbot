"""
FAISS vector-store loader - LOAD ONLY.

CRITICAL: FAISS index MUST be pre-built before deployment.
- No runtime rebuild (too slow, requires model download)
- No model download at startup
- Fast startup (<5 seconds)

The index is built offline using ingest_data.py and committed to the repo.
"""

from typing import Optional
import os

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.utils.config import FAISS_INDEX_PATH, HF_EMBEDDING_MODEL
from app.utils.logger import logger

# Module-level singleton — populated by ``load_vector_store()``.
_vector_store: Optional[FAISS] = None


def load_vector_store() -> Optional[FAISS]:
    """
    Load the pre-built FAISS index from disk.
    
    CRITICAL: This function ONLY loads - no rebuild, no model download.
    The FAISS index must be pre-built using ingest_data.py before deployment.
    
    Returns:
        FAISS vector store instance, or None if index doesn't exist.
    """
    global _vector_store
    
    # Return cached instance if already loaded
    if _vector_store is not None:
        return _vector_store

    # Check if index directory exists
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.warning("⚠️ FAISS index directory '%s' not found. RAG disabled.", FAISS_INDEX_PATH)
        logger.warning("⚠️ Run 'python app/ingest_data.py' to build the index.")
        return None

    # Check for required FAISS files
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        logger.warning("⚠️ FAISS index files not found in '%s'. RAG disabled.", FAISS_INDEX_PATH)
        return None

    logger.info("Loading FAISS index from '%s' …", FAISS_INDEX_PATH)
    try:
        # Use local HuggingFace embeddings - model must be cached
        logger.info("Initializing embeddings (model: %s)...", HF_EMBEDDING_MODEL)
        embeddings = HuggingFaceEmbeddings(
            model_name=HF_EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        
        logger.info("Loading FAISS index from disk...")
        _vector_store = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("✅ FAISS index loaded successfully (%d vectors).", _vector_store.index.ntotal)
        return _vector_store
        
    except KeyError as exc:
        # Pydantic v1/v2 incompatibility
        logger.error("❌ FAISS index incompatible (Pydantic version mismatch): %s", exc)
        logger.error("❌ Rebuild the index using: python app/ingest_data.py")
        return None
        
    except Exception as exc:
        logger.error("❌ Failed to load FAISS index: %s", exc, exc_info=True)
        return None


def get_vector_store() -> Optional[FAISS]:
    """Return the cached vector-store instance (may be ``None`` if not loaded)."""
    return _vector_store
