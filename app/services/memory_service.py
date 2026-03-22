"""
Conversation memory service — lightweight in-memory store keyed by
``conversation_id``.

Each entry is a list of ``{"role": ..., "content": ...}`` dicts compatible
with the OpenAI chat-completion message format.

Note: this is intentionally ephemeral (process-level dict).  For production
persistence, swap in Redis or a database-backed store.
"""

from typing import Dict, List

from app.utils.logger import logger

# conversation_id → list of messages
_store: Dict[str, List[dict]] = {}

# Maximum messages retained per conversation (to avoid unbounded growth).
MAX_HISTORY_LENGTH: int = 50


def get_history(conversation_id: str) -> List[dict]:
    """Return the full message history for a conversation."""
    return _store.get(conversation_id, [])


def add_message(conversation_id: str, role: str, content: str) -> None:
    """
    Append a message to the conversation history.

    ``role`` should be one of ``"user"`` or ``"assistant"``.
    """
    if conversation_id not in _store:
        _store[conversation_id] = []
        logger.info("Created new conversation memory for '%s'.", conversation_id)

    _store[conversation_id].append({"role": role, "content": content})

    # Trim old messages if needed (keep the most recent ones).
    if len(_store[conversation_id]) > MAX_HISTORY_LENGTH:
        _store[conversation_id] = _store[conversation_id][-MAX_HISTORY_LENGTH:]
        logger.debug("Trimmed conversation '%s' to %d messages.", conversation_id, MAX_HISTORY_LENGTH)


def clear_history(conversation_id: str) -> None:
    """Remove all stored messages for a conversation."""
    _store.pop(conversation_id, None)
    logger.info("Cleared memory for conversation '%s'.", conversation_id)
