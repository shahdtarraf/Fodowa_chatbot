"""
FAISS vector-store loader - LOAD ONLY (NO EMBEDDINGS).

CRITICAL: FAISS index MUST be pre-built before deployment.
- No runtime rebuild (too slow, requires model download)
- No model download at startup
- No embeddings initialization
- Fast startup (<5 seconds)

The index is built offline using ingest_data.py and committed to the repo.
At runtime, we ONLY load the pre-built index - no embeddings needed.
"""

from typing import Optional
import os
import pickle

from langchain_community.vectorstores import FAISS

from app.utils.config import FAISS_INDEX_PATH
from app.utils.logger import logger

# Module-level singleton — populated by ``load_vector_store()``.
_vector_store: Optional[FAISS] = None


def load_vector_store() -> Optional[FAISS]:
    """
    Load the pre-built FAISS index from disk.
    
    CRITICAL: This function ONLY loads - no rebuild, no model download, no embeddings.
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
        logger.warning("⚠️ Run 'python app/ingest_data.py' locally to build the index.")
        return None

    # Check for required FAISS files
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        logger.warning("⚠️ FAISS index files not found in '%s'. RAG disabled.", FAISS_INDEX_PATH)
        return None

    logger.info("Loading FAISS index from '%s' …", FAISS_INDEX_PATH)
    try:
        # Load FAISS directly without embeddings
        # The index is already built - we just need to deserialize it
        import faiss
        
        # Load the FAISS index
        index = faiss.read_index(index_file)
        
        # Load the docstore and index_to_docstore_id
        with open(pkl_file, "rb") as f:
            docstore, index_to_docstore_id = pickle.load(f)
        
        # Create a minimal FAISS wrapper without embeddings
        # We'll use a dummy embedding function for similarity search
        class DummyEmbeddings:
            """Dummy embeddings - not used for pre-built index."""
            def embed_documents(self, texts):
                raise NotImplementedError("Embeddings not available at runtime")
            def embed_query(self, text):
                raise NotImplementedError("Embeddings not available at runtime")
        
        # Create FAISS instance manually
        _vector_store = FAISS(
            embedding_function=DummyEmbeddings(),
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
        )
        
        logger.info("✅ FAISS index loaded successfully (%d vectors).", index.ntotal)
        return _vector_store
        
    except KeyError as exc:
        # Pydantic v1/v2 incompatibility
        logger.error("❌ FAISS index incompatible (Pydantic version mismatch): %s", exc)
        logger.error("❌ Rebuild the index locally using: python app/ingest_data.py")
        return None
        
    except Exception as exc:
        logger.error("❌ Failed to load FAISS index: %s", exc, exc_info=True)
        return None


def get_vector_store() -> Optional[FAISS]:
    """Return the cached vector-store instance (may be ``None`` if not loaded)."""
    return _vector_store
