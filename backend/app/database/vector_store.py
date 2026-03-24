"""
FAISS vector-store loader with auto-rebuild capability.

PRODUCTION ARCHITECTURE:
- Uses local HuggingFace embeddings (no external API dependency)
- Consistent embeddings between ingestion and retrieval
- Auto-rebuilds FAISS index if corrupted or incompatible
"""

from typing import Optional
import os

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.utils.config import FAISS_INDEX_PATH, HF_EMBEDDING_MODEL
from app.utils.logger import logger

# Module-level singleton — populated by ``load_vector_store()``.
_vector_store: Optional[FAISS] = None


def _rebuild_index() -> Optional[FAISS]:
    """Rebuild FAISS index from source PDF."""
    try:
        logger.info("🔄 Rebuilding FAISS index...")
        from app.ingest_data import build_faiss_index
        build_faiss_index()
        
        # Try loading again after rebuild
        logger.info("Initializing local HuggingFace embeddings (model: %s)...", HF_EMBEDDING_MODEL)
        embeddings = HuggingFaceEmbeddings(
            model_name=HF_EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        
        _vs = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("✅ FAISS index rebuilt and loaded successfully (%d vectors).", _vs.index.ntotal)
        return _vs
    except Exception as exc:
        logger.error("❌ Failed to rebuild FAISS index: %s", exc, exc_info=True)
        return None


def load_vector_store() -> Optional[FAISS]:
    """
    Load the pre-built FAISS index from disk.
    
    If loading fails (Pydantic incompatibility, corruption), automatically rebuilds.
    
    Uses HuggingFaceEmbeddings for:
    - Accurate semantic search (same embeddings used during ingestion)
    - Local embeddings (no external API dependency)
    - Consistency with ingest_data.py
    """
    global _vector_store

    # Check if index directory exists
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.warning("FAISS index directory '%s' does not exist.", FAISS_INDEX_PATH)
        return _rebuild_index()

    # Check for required FAISS files
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        logger.warning("FAISS index files not found in '%s'.", FAISS_INDEX_PATH)
        return _rebuild_index()

    logger.info("Loading FAISS index from '%s' …", FAISS_INDEX_PATH)
    try:
        # Use local HuggingFace embeddings - no external API dependency
        logger.info("Initializing local HuggingFace embeddings (model: %s)...", HF_EMBEDDING_MODEL)
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
        # Pydantic v1/v2 incompatibility - rebuild index
        logger.warning("⚠️ FAISS index incompatible (Pydantic version mismatch). Rebuilding...")
        return _rebuild_index()
    except Exception as exc:
        logger.error("❌ Failed to load FAISS index: %s", exc, exc_info=True)
        # Try rebuilding as last resort
        logger.info("Attempting to rebuild FAISS index...")
        return _rebuild_index()


def get_vector_store() -> Optional[FAISS]:
    """Return the cached vector-store instance (may be ``None`` if not loaded)."""
    return _vector_store
