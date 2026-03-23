"""
Pydantic request / response schemas for the chat API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend / Django proxy."""
    user_message: str = Field(..., min_length=1, description="The user's message text")
    conversation_id: str = Field(..., min_length=1, description="Unique conversation identifier")
    token: Optional[str] = Field(default=None, description="JWT token (optional – guests send empty/null)")


class ChatResponse(BaseModel):
    """Outgoing response returned to the caller."""
    response: str = Field(..., description="The assistant's reply in Arabic")
