"""
Data Ingestion Script — PDF → FAISS vector index.

Usage:
    python app/ingest_data.py

This script:
1. Loads the PDF from ``data/knowledge_base.pdf``.
2. Splits it into chunks with RecursiveCharacterTextSplitter.
3. Generates embeddings via HuggingFace Inference API (lightweight, no local model).
4. Saves the FAISS index to ``data/faiss_index/``.

Run this ONCE (or whenever the PDF is updated) before starting the server.

IMPORTANT: Uses same embedding configuration as vector_store.py for consistency.
"""

import os
import sys

# Ensure the project root is on sys.path so ``app.utils`` can be imported
# when the script is executed directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from app.utils.config import (
    FAISS_INDEX_PATH,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
    HF_EMBEDDING_MODEL,
    HUGGINGFACEHUB_API_TOKEN,
)
from app.utils.logger import logger

# ── Paths ───────────────────────────────────────────────
PDF_PATH = os.path.join("data", "knowledge_base.pdf")


def build_faiss_index() -> None:
    """Build FAISS index from PDF using HuggingFace Inference API embeddings."""
    
    # 1. Validate that the PDF exists
    if not os.path.isfile(PDF_PATH):
        logger.error("❌  PDF not found at '%s'. Place your knowledge-base PDF there first.", PDF_PATH)
        return

    # 2. Validate API token
    if not HUGGINGFACEHUB_API_TOKEN:
        logger.error("❌  HUGGINGFACEHUB_API_TOKEN not set. Please set it in .env file.")
        return

    # 3. Load the PDF
    logger.info("📄  Loading PDF from '%s' …", PDF_PATH)
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    logger.info("   Loaded %d page(s).", len(documents))

    # 4. Split into chunks
    logger.info("✂️  Splitting into chunks (size=%d, overlap=%d) …", RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info("   Created %d chunk(s).", len(chunks))

    # 5. Generate embeddings locally (no external API)
    logger.info("🧠  Loading local HuggingFace embeddings...")
    logger.info("   Model: %s", HF_EMBEDDING_MODEL)
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
    )
    logger.info("   ✅ Embeddings model loaded.")

    # 6. Build FAISS index
    logger.info("🔨  Building FAISS index from %d chunks...", len(chunks))
    vector_store = FAISS.from_documents(chunks, embeddings)

    # 7. Save to disk
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    vector_store.save_local(FAISS_INDEX_PATH)
    logger.info("💾  FAISS index saved to '%s'.", FAISS_INDEX_PATH)
    logger.info("✅  Ingestion complete — %d chunks indexed.", len(chunks))


def ingest() -> None:
    """Run the full ingestion pipeline (CLI entry point)."""
    build_faiss_index()


if __name__ == "__main__":
    ingest()
