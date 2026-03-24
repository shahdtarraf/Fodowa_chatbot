"""
Application configuration — loads environment variables from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── HuggingFace ─────────────────────────────────────────
HUGGINGFACEHUB_API_TOKEN: str = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")
HF_EMBEDDING_MODEL: str = os.getenv(
    "HF_EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

# ── Django Backend ──────────────────────────────────────
DJANGO_BACKEND_URL: str = os.getenv("DJANGO_BACKEND_URL", "http://localhost:8000")

# ── JWT ─────────────────────────────────────────────────
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

# ── FAISS ───────────────────────────────────────────────
FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", str(BASE_DIR / "data" / "faiss_index"))
PDF_PATH: str = os.getenv("PDF_PATH", str(BASE_DIR / "data" / "knowledge_base.pdf"))

# ── RAG Settings ────────────────────────────────────────
RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

# ── API Settings ─────────────────────────────────────────
HF_API_TIMEOUT: int = int(os.getenv("HF_API_TIMEOUT", "60"))
HF_MAX_RETRIES: int = int(os.getenv("HF_MAX_RETRIES", "3"))
HF_RETRY_DELAY: int = int(os.getenv("HF_RETRY_DELAY", "5"))
