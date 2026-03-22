"""
FODWA AI Chatbot Microservice — FastAPI application entry-point.

Startup sequence:
1. Configure CORS middleware.
2. Load the pre-built FAISS vector-store index.
3. Register API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.vector_store import load_vector_store
from app.routes.chat import router as chat_router
from app.utils.logger import logger


# ── Lifespan (startup / shutdown) ───────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    logger.info("🚀  FODWA Chatbot Microservice starting up …")

    # Load FAISS index
    try:
        load_vector_store()
        logger.info("✅  FAISS vector store loaded.")
    except Exception as exc:
        logger.warning(
            "⚠️  Could not load FAISS index (%s). "
            "The chatbot will run without RAG context until the index is built. "
            "Run `python app/ingest_data.py` to create the index.",
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


# ── Health check ────────────────────────────────────────
@app.get("/health")
async def health():
    """Simple health-check endpoint used by Render / load balancers."""
    return {"status": "ok", "service": "fodwa-chatbot"}
