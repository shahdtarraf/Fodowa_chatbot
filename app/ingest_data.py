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

import time
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings
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


def ingest() -> None:
    """Run the full ingestion pipeline."""

    # 1. Validate that the PDF exists
    if not os.path.isfile(PDF_PATH):
        logger.error("❌  PDF not found at '%s'. Place your knowledge-base PDF there first.", PDF_PATH)
        sys.exit(1)

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

    # 4. Generate embeddings & build FAISS index (Serverless API)
    logger.info("🧠  Generating embeddings via HuggingFace API with '%s' …", HF_EMBEDDING_MODEL)
    embeddings = HuggingFaceEndpointEmbeddings(
        model=HF_EMBEDDING_MODEL,
        huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
    )

    # Warmup with retry - model may be cold on HuggingFace Serverless API
    max_warmup_retries = 10
    warmup_success = False
    for attempt in range(1, max_warmup_retries + 1):
        try:
            logger.info("   Warming up embedding model (Attempt %d/%d)...", attempt, max_warmup_retries)
            res = embeddings.embed_query("warmup")
            if isinstance(res, list) and len(res) > 0:
                logger.info("   ✅ Model is ready! Proceeding with chunk embedding...")
                warmup_success = True
                break
        except Exception as e:
            wait_time = min(attempt * 10, 60)  # Exponential backoff, max 60s
            logger.warning("   Model warming up, waiting %ds... (Error: %s)", wait_time, repr(e))
            time.sleep(wait_time)

    if not warmup_success:
        logger.warning("   ⚠️ Warmup didn't complete but proceeding anyway...")

    # Build FAISS index with retry
    @retry(
        stop=stop_after_attempt(HF_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=HF_RETRY_DELAY, max=30),
    )
    def build_faiss_index():
        return FAISS.from_documents(chunks, embeddings)

    vector_store = build_faiss_index()

    # 5. Save to disk
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    vector_store.save_local(FAISS_INDEX_PATH)
    logger.info("💾  FAISS index saved to '%s'.", FAISS_INDEX_PATH)
    logger.info("✅  Ingestion complete — %d chunks indexed.", len(chunks))


if __name__ == "__main__":
    ingest()
