"""
FODWA Chatbot - Minimal FastAPI Server for Render Free (512MB RAM).

NO ML models, NO embeddings, NO external APIs.
Uses lightweight difflib matching for FAQ responses.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("fodwa")

# Import FAQ service
from app.services.faq_service import get_chat_response, load_faq

# ── Request/Response Models ───────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"

class ChatResponse(BaseModel):
    response: str

# ── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="FODWA Chatbot",
    description="مساعد ذكي لمنصة فودوا - يجيب على الأسئلة الشائعة",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Load FAQ on startup."""
    logger.info("🚀 FODWA Chatbot starting...")
    
    faq = load_faq()
    if faq:
        logger.info(f"✅ Loaded {len(faq)} FAQ items")
    else:
        logger.warning("⚠️ No FAQ data loaded")
    
    logger.info("✅ Ready to serve requests")


# ── Endpoints ───────────────────────────────────────────────
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "FODWA Chatbot",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.get("/health")
async def health():
    """Health check for Render."""
    return {"status": "ok", "service": "fodwa-chatbot"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Uses lightweight difflib matching - no ML models.
    """
    logger.info(f"POST /chat - message: {request.message[:50]}...")
    
    try:
        response = get_chat_response(request.message)
        logger.info(f"✅ Response: {response[:50]}...")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")


# ── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
