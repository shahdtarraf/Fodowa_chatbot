"""
FAISS vector-store loader.

PRODUCTION ARCHITECTURE:
- Uses FakeEmbeddings for loading pre-built FAISS index
- No heavy embedding model loaded at runtime (saves ~400MB RAM)
- FAISS index must be pre-built locally using ingest_data.py
"""

from typing import Optional
import os

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import FakeEmbeddings

from app.utils.config import FAISS_INDEX_PATH
from app.utils.logger import logger

# Module-level singleton — populated by ``load_vector_store()``.
_vector_store: Optional[FAISS] = None


def load_vector_store() -> Optional[FAISS]:
    """
    Load the pre-built FAISS index from disk.
    
    Uses FakeEmbeddings because:
    - The index is already built with real embeddings
    - We only need embeddings for similarity search interface
    - FakeEmbeddings are lightweight (no model loading)
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
        # Use FakeEmbeddings - lightweight, no model loading
        # The index was built with real embeddings, we just need the interface
        embeddings = FakeEmbeddings()
        _vector_store = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS index loaded successfully (%d vectors).", _vector_store.index.ntotal)
        return _vector_store
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc, exc_info=True)
        return None


def get_vector_store() -> Optional[FAISS]:
    """Return the cached vector-store instance (may be ``None`` if not loaded)."""
    return _vector_store
