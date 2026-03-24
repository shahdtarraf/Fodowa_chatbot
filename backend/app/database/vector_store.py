"""
FAISS vector-store loader with auto-rebuild capability.

PRODUCTION ARCHITECTURE:
- Try to load pre-built FAISS index first
- If loading fails (Pydantic incompatibility), auto-rebuild using local embeddings
- Uses HuggingFaceEmbeddings for consistent embeddings
- No external API dependency
"""

from typing import Optional
import os

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.utils.config import FAISS_INDEX_PATH, HF_EMBEDDING_MODEL, PDF_PATH
from app.utils.logger import logger

# Module-level singleton — populated by ``load_vector_store()``.
_vector_store: Optional[FAISS] = None


def _build_fresh_index() -> Optional[FAISS]:
    """
    Build a fresh FAISS index from the PDF.
    
    This is called when:
    - FAISS index doesn't exist
    - FAISS index is corrupted
    - FAISS index has Pydantic version mismatch
    
    Returns:
        FAISS vector store instance, or None if build fails.
    """
    try:
        logger.info("🔄 Building fresh FAISS index...")
        
        # Check if PDF exists
        if not os.path.exists(PDF_PATH):
            logger.error("❌ PDF file not found at '%s'. Cannot build index.", PDF_PATH)
            return None
        
        # Load PDF
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        logger.info("📄 Loading PDF from '%s'...", PDF_PATH)
        loader = PyPDFLoader(PDF_PATH)
        documents = loader.load()
        logger.info("   Loaded %d page(s).", len(documents))
        
        # Split into chunks
        logger.info("✂️ Splitting into chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        chunks = splitter.split_documents(documents)
        logger.info("   Created %d chunk(s).", len(chunks))
        
        # Initialize embeddings
        logger.info("🧠 Initializing embeddings (model: %s)...", HF_EMBEDDING_MODEL)
        embeddings = HuggingFaceEmbeddings(
            model_name=HF_EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        
        # Build FAISS index
        logger.info("🔨 Building FAISS index from %d chunks...", len(chunks))
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save to disk
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        vector_store.save_local(FAISS_INDEX_PATH)
        logger.info("💾 FAISS index saved to '%s'.", FAISS_INDEX_PATH)
        
        logger.info("✅ FAISS index built successfully (%d vectors).", vector_store.index.ntotal)
        return vector_store
        
    except Exception as exc:
        logger.error("❌ Failed to build FAISS index: %s", exc, exc_info=True)
        return None


def load_vector_store() -> Optional[FAISS]:
    """
    Load the FAISS index from disk.
    
    If loading fails (Pydantic incompatibility, corruption), automatically rebuilds.
    
    Returns:
        FAISS vector store instance, or None if both load and rebuild fail.
    """
    global _vector_store
    
    # Return cached instance if already loaded
    if _vector_store is not None:
        return _vector_store

    # Check if index directory exists
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.warning("⚠️ FAISS index directory '%s' not found.", FAISS_INDEX_PATH)
        _vector_store = _build_fresh_index()
        return _vector_store

    # Check for required FAISS files
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        logger.warning("⚠️ FAISS index files not found in '%s'.", FAISS_INDEX_PATH)
        _vector_store = _build_fresh_index()
        return _vector_store

    logger.info("Loading FAISS index from '%s' …", FAISS_INDEX_PATH)
    try:
        # Initialize embeddings (same as used during ingestion)
        logger.info("Initializing embeddings (model: %s)...", HF_EMBEDDING_MODEL)
        embeddings = HuggingFaceEmbeddings(
            model_name=HF_EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        
        # Load FAISS index
        _vector_store = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("✅ FAISS index loaded successfully (%d vectors).", _vector_store.index.ntotal)
        return _vector_store
        
    except KeyError as exc:
        # Pydantic v1/v2 incompatibility - rebuild index
        logger.warning("⚠️ FAISS index incompatible (Pydantic version mismatch): %s", exc)
        logger.info("🔄 Rebuilding FAISS index...")
        _vector_store = _build_fresh_index()
        return _vector_store
        
    except Exception as exc:
        logger.error("❌ Failed to load FAISS index: %s", exc, exc_info=True)
        logger.info("🔄 Attempting to rebuild FAISS index...")
        _vector_store = _build_fresh_index()
        return _vector_store


def get_vector_store() -> Optional[FAISS]:
    """Return the cached vector-store instance (may be ``None`` if not loaded)."""
    return _vector_store
