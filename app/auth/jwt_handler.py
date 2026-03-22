"""
JWT token decoding and user extraction.

Design decision: if the token is empty or invalid the request is NOT blocked —
the user is simply treated as a guest (user_id = None).
"""

from typing import Optional

import jwt

from app.utils.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.utils.logger import logger


def decode_token(token: Optional[str]) -> Optional[int]:
    """
    Decode a JWT and return the ``user_id`` claim.

    Returns ``None`` when:
    • the token string is empty / None  (guest)
    • the token is expired or malformed (treated as guest, logged as warning)
    """
    if not token:
        logger.info("No token provided — treating as guest user.")
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        logger.info("Token decoded successfully — user_id=%s", user_id)
        return user_id
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired — treating as guest.")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid JWT token (%s) — treating as guest.", exc)
        return None
