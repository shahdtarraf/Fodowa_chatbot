"""
FODWA AI Chatbot Microservice — FastAPI application entry-point.

Startup sequence:
1. Configure CORS middleware.
2. Load the pre-built FAISS vector-store index.
3. Register API routers.
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.vector_store import load_vector_store
from app.routes.chat import router as chat_router
from app.utils.logger import logger
from app.utils.config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, RAG_TOP_K


# ── Lifespan (startup / shutdown) ───────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    logger.info("🚀  FODWA Chatbot Microservice starting up …")

    # Check if FAISS index exists, if not create it
    faiss_path = "data/faiss_index"
    if not os.path.exists(f"{faiss_path}/index.faiss"):
        logger.info("📦  FAISS index not found. Building from PDF knowledge base...")
        try:
            from app.ingest_data import build_faiss_index
            build_faiss_index()
            logger.info("✅  FAISS index built successfully.")
        except Exception as e:
            logger.error("❌  Failed to build FAISS index: %s", e)

    # Load FAISS index
    try:
        load_vector_store()
        logger.info("✅  FAISS vector store loaded.")
    except Exception as exc:
        logger.warning(
            "⚠️  Could not load FAISS index (%s). "
            "The chatbot will run without RAG context until the index is built.",
            exc,
        )

    yield  # ← application runs here

    logger.info("👋  FODWA Chatbot Microservice shutting down.")


# ── Application ────────────────────────────────────────
app = FastAPI(
    title="FODWA AI Chatbot",
    description="مساعد ذكي لمنصة فودوا — يجيب بالعربية بناءً على قاعدة المعرفة.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────
app.include_router(chat_router)


# ── Root endpoint ────────────────────────────────────────
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "FODWA AI Chatbot",
        "description": "مساعد ذكي لمنصة فودوا",
        "status": "running",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)",
            "docs": "/docs (GET)"
        }
    }


# ── Health check ────────────────────────────────────────
@app.get("/health")
async def health():
    """Simple health-check endpoint used by Render / load balancers."""
    return {"status": "ok", "service": "fodwa-chatbot"}
