"""
LangChain tool: ``get_user_profile``

Calls the Django REST backend to fetch the authenticated user's profile.
The raw JWT token is passed through so the Django side can verify it.

Compatible with both OpenAI tool-calling and ReAct agents.
"""

from typing import Optional

import requests
from langchain.tools import tool

from app.utils.config import DJANGO_BACKEND_URL
from app.utils.logger import logger

# Timeout for outgoing HTTP calls to the Django backend (seconds).
_DJANGO_TIMEOUT: int = 10


def fetch_user_profile(token: str) -> str:
    """
    Call ``GET {DJANGO_BACKEND_URL}/api/profile`` using the caller's JWT
    and return a human-readable summary of the profile data.

    Returns an Arabic error message on failure so the LLM can relay it
    to the user gracefully.
    """
    if not token:
        return "المستخدم غير مسجّل الدخول (زائر). لا يمكن جلب بيانات الملف الشخصي."

    url = f"{DJANGO_BACKEND_URL.rstrip('/')}/api/profile"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        logger.info("Calling Django profile API at %s", url)
        response = requests.get(url, headers=headers, timeout=_DJANGO_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        logger.info("Profile fetched successfully for token.")

        # Build a readable summary for the LLM context.
        lines = [f"- {key}: {value}" for key, value in data.items()]
        return "بيانات الملف الشخصي للمستخدم:\n" + "\n".join(lines)

    except requests.exceptions.Timeout:
        logger.error("Django profile API timed out.")
        return "عذرًا، تعذّر الاتصال بالخادم لجلب بيانات الملف الشخصي. يرجى المحاولة لاحقًا."
    except requests.exceptions.HTTPError as exc:
        logger.error("Django profile API returned HTTP %s: %s", exc.response.status_code, exc)
        return "عذرًا، حدث خطأ أثناء جلب بيانات الملف الشخصي."
    except Exception as exc:
        logger.error("Unexpected error calling Django profile API: %s", exc, exc_info=True)
        return "عذرًا، حدث خطأ غير متوقع."


def create_profile_tool(token: Optional[str]):
    """
    Factory that returns a LangChain ``@tool`` with the caller's token
    baked into its closure so the agent can invoke it without needing to
    pass the token as an argument.

    The tool accepts an arbitrary ``query`` string (which the ReAct agent
    will supply as Action Input) but ignores it — the JWT is the only
    thing needed to fetch the profile.
    """

    @tool
    def get_user_profile(query: str = "") -> str:
        """جلب بيانات الملف الشخصي للمستخدم الحالي من المنصة. استخدم هذه الأداة عندما يسأل المستخدم عن حسابه أو بياناته الشخصية."""
        return fetch_user_profile(token or "")

    return get_user_profile
