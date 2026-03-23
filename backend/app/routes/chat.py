"""
Chat API route — POST /chat

Accepts a user message, optional JWT, and a conversation_id.
Returns the assistant's Arabic reply.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.auth.jwt_handler import decode_token
from app.services.llm_service import get_chat_response
from app.utils.logger import logger

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint consumed by the front-end / Django proxy.

    Flow:
    1. Validate & decode JWT (guests are allowed).
    2. Delegate to the LLM service.
    3. Return the assistant's reply.
    """
    logger.info(
        "POST /chat — conversation_id=%s, message='%.80s…'",
        request.conversation_id,
        request.user_message,
    )

    # ── 1. JWT (non-blocking) ───────────────────────────
    user_id = decode_token(request.token)
    logger.info("Resolved user_id=%s (None = guest).", user_id)

    # ── 2. Get response from LLM agent ─────────────────
    try:
        reply = await get_chat_response(
            user_message=request.user_message,
            conversation_id=request.conversation_id,
            token=request.token,
        )
    except Exception as exc:
        logger.error("Unhandled error in chat endpoint: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="حدث خطأ داخلي. يرجى المحاولة لاحقًا.",
        )

    return ChatResponse(response=reply)
