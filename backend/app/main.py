"""
FODWA AI Chatbot Microservice — FastAPI application entry-point.

PRODUCTION ARCHITECTURE:
- FAISS index is pre-built locally and deployed with the code
- No embedding generation at runtime (saves ~400MB RAM)
- No PDF processing at runtime
- Lightweight startup (<5 seconds)
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.vector_store import load_vector_store
from app.routes.chat import router as chat_router
from app.utils.logger import logger


# ── Lifespan (startup / shutdown) ───────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    logger.info("🚀 FODWA Chatbot Microservice starting up …")

    # Load pre-built FAISS index only - NO embedding generation, NO PDF processing
    try:
        vs = load_vector_store()
        if vs:
            logger.info("✅ FAISS vector store loaded (%d vectors).", vs.index.ntotal)
        else:
            logger.warning("⚠️ FAISS index not found. Chatbot will run without RAG context.")
    except Exception as exc:
        logger.error("❌ Failed to load FAISS index: %s", exc)

    yield

    logger.info("👋 FODWA Chatbot Microservice shutting down.")


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
