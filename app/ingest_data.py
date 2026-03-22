"""
Data Ingestion Script — PDF → FAISS vector index.

Usage:
    python app/ingest_data.py

This script:
1. Loads the PDF from ``data/knowledge_base.pdf``.
2. Splits it into chunks with RecursiveCharacterTextSplitter.
3. Generates embeddings via HuggingFaceEmbeddings (FREE — runs locally).
4. Saves the FAISS index to ``data/faiss_index/``.

Run this ONCE (or whenever the PDF is updated) before starting the server.
"""

import os
import sys

# Ensure the project root is on sys.path so ``app.utils`` can be imported
# when the script is executed directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from app.utils.config import (
    FAISS_INDEX_PATH,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
    HF_EMBEDDING_MODEL,
    HUGGINGFACEHUB_API_TOKEN,
    HF_MAX_RETRIES,
    HF_RETRY_DELAY,
)
from app.utils.logger import logger

# ── Paths ───────────────────────────────────────────────
PDF_PATH = os.path.join("data", "knowledge_base.pdf")


def build_faiss_index() -> None:
    """Build FAISS index from PDF - can be called from main.py on startup."""
    
    # 1. Validate that the PDF exists
    if not os.path.isfile(PDF_PATH):
        logger.error("❌  PDF not found at '%s'. Place your knowledge-base PDF there first.", PDF_PATH)
        return

    # 2. Load the PDF
    logger.info("📄  Loading PDF from '%s' …", PDF_PATH)
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    logger.info("   Loaded %d page(s).", len(documents))

    # 3. Split into chunks
    logger.info("✂️  Splitting into chunks (size=%d, overlap=%d) …", RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info("   Created %d chunk(s).", len(chunks))

    # 4. Generate embeddings & build FAISS index (local model - no API needed)
    logger.info("🧠  Loading local embedding model '%s' …", HF_EMBEDDING_MODEL)
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("   ✅ Embedding model loaded.")

    # Build FAISS index
    @retry(
        stop=stop_after_attempt(HF_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=HF_RETRY_DELAY, max=30),
    )
    def _build_index():
        return FAISS.from_documents(chunks, embeddings)

    vector_store = _build_index()

    # 5. Save to disk
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    vector_store.save_local(FAISS_INDEX_PATH)
    logger.info("💾  FAISS index saved to '%s'.", FAISS_INDEX_PATH)
    logger.info("✅  Ingestion complete — %d chunks indexed.", len(chunks))


def ingest() -> None:
    """Run the full ingestion pipeline (CLI entry point)."""
    build_faiss_index()


if __name__ == "__main__":
    ingest()
