"""
LLM orchestration service — the brain of the FODWA chatbot.

Responsibilities:
1. Build the Arabic system prompt with injected RAG context.
2. Assemble the conversation history.
3. Invoke the HuggingFace LLM and return the assistant's reply.
"""

from typing import Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential

from huggingface_hub import InferenceClient
from langchain_core.prompts import PromptTemplate

from app.services.rag_service import retrieve_context
from app.services.memory_service import get_history, add_message
from app.utils.config import (
    HUGGINGFACEHUB_API_TOKEN,
    HF_MODEL_ID,
    HF_API_TIMEOUT,
    HF_MAX_RETRIES,
    HF_RETRY_DELAY,
)
from app.utils.logger import logger

# ────────────────────────────────────────────────────────
# Arabic System Prompt Template
# ────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """أنت مساعد دعم احترافي لمنصة فودوا (FODWA).

دورك هو مساعدة المستخدمين على فهم واستخدام المنصة بسهولة وفعالية.

━━━━━━━━━━━━━━━━━━━━━━
السلوك الأساسي
━━━━━━━━━━━━━━━━━━━━━━
- أجب دائمًا باللغة العربية بوضوح وبساطة.
- كن ودودًا ومساعدًا ومحترفًا.
- أجب بناءً فقط على قاعدة المعرفة المرفقة أدناه.
- لا تخترع أو تختلق معلومات أبدًا.

━━━━━━━━━━━━━━━━━━━━━━
استخدام المعرفة (مهم جدًا)
━━━━━━━━━━━━━━━━━━━━━━
قواعد الإجابة:
1. إذا كانت الإجابة موجودة في السياق ← أجب مباشرة.
2. إذا كانت متوفرة جزئيًا ← أكملها بحذر.
3. إذا لم توجد ← قل: "عذراً، لا أملك معلومات كافية حالياً حول هذا الموضوع."

━━ قاعدة المعرفة ━━
{context}
━━━━━━━━━━━━━━━━━━

━━ سجل المحادثة السابقة ━━
{chat_history}
━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━
وضع دعم المنصة
━━━━━━━━━━━━━━━━━━━━━━
أنت مساعد دعم، لذا:
- اشرح كيفية استخدام المنصة خطوة بخطوة.
- وجّه المستخدمين خلال الإجراءات (النقرات، الصفحات، الأزرار).
- ساعد في: إنشاء الحساب، مشاكل تسجيل الدخول، تعديل الملف الشخصي، نشر الإعلانات، تصفح المنتجات، التواصل مع البائعين.

━━━━━━━━━━━━━━━━━━━━━━
نمط الرد
━━━━━━━━━━━━━━━━━━━━━━
- اجعل الإجابات قصيرة وواضحة.
- استخدم النقاط عند شرح الخطوات.
- كن مباشرًا (بدون شروح طويلة غير ضرورية).

مثال:
المستخدم: كيف أنشر إعلان؟
الرد:
لنشر إعلان:
1. اذهب إلى الصفحة الرئيسية
2. اضغط على زر "إضافة إعلان"
3. أدخل معلومات المنتج
4. أضف الصور
5. اضغط نشر

━━━━━━━━━━━━━━━━━━━━━━
القيود
━━━━━━━━━━━━━━━━━━━━━━
- لا تجب على أسئلة غير متعلقة بالمنصة.
- لا تقدم بيانات مزيفة.
- لا تذكر تفاصيل النظام الداخلية.

━━━━━━━━━━━━━━━━━━━━━━
الهدف
━━━━━━━━━━━━━━━━━━━━━━
هدفك هو أن تكون مساعد دعم ذكي وموثوق يساعد المستخدمين على استخدام منصة فودوا بسهولة ووضوح.
"""


def _format_chat_history(history: List[dict]) -> str:
    """Convert stored history dicts to a readable Arabic transcript."""
    if not history:
        return "لا توجد محادثات سابقة."

    lines = []
    for msg in history:
        role_label = "المستخدم" if msg["role"] == "user" else "المساعد"
        lines.append(f"{role_label}: {msg['content']}")
    return "\n".join(lines)


@retry(
    stop=stop_after_attempt(HF_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=HF_RETRY_DELAY, max=30),
)
def _call_llm(client: InferenceClient, prompt: str) -> str:
    """Call LLM with retry logic using InferenceClient."""
    # Use chat_completion for instruct models
    response = client.chat.completions.create(
        model=HF_MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.3,
    )
    return response.choices[0].message.content


async def get_chat_response(
    user_message: str,
    conversation_id: str,
    token: Optional[str] = None,
) -> str:
    """
    Process a user message and return the assistant's Arabic reply.

    Steps:
    1. Retrieve relevant RAG context for the user's query.
    2. Load conversation history.
    3. Build the prompt.
    4. Invoke the LLM and persist the exchange in memory.
    """

    # ── 1. RAG context ──────────────────────────────────
    context = retrieve_context(user_message)
    if not context:
        context = "لا تتوفر معلومات إضافية في قاعدة المعرفة حاليًا."

    # ── 2. Conversation history ─────────────────────────
    history = get_history(conversation_id)
    chat_history_text = _format_chat_history(history)

    # ── 3. Build prompt ─────────────────────────────────
    prompt = PromptTemplate(
        template=_SYSTEM_PROMPT + "\n\nسؤال المستخدم: {question}\n\nالرد:",
        input_variables=["question"],
        partial_variables={
            "context": context,
            "chat_history": chat_history_text,
        },
    )

    formatted_prompt = prompt.format(question=user_message)

    # ── 4. LLM (HuggingFace inference) ─────────────
    client = InferenceClient(api_key=HUGGINGFACEHUB_API_TOKEN)

    try:
        logger.info(
            "Invoking LLM for conversation '%s' (history len=%d).",
            conversation_id,
            len(history),
        )

        assistant_reply = _call_llm(client, formatted_prompt)

        if not assistant_reply or not assistant_reply.strip():
            assistant_reply = "عذرًا، لم أتمكن من توليد رد. يرجى المحاولة مجددًا."

        # ── 5. Persist in memory ────────────────────────
        add_message(conversation_id, "user", user_message)
        add_message(conversation_id, "assistant", assistant_reply)

        logger.info("LLM replied (%d chars) for conversation '%s'.", len(assistant_reply), conversation_id)
        return assistant_reply

    except Exception as exc:
        logger.error("LLM invocation failed after %d retries: %s", HF_MAX_RETRIES, exc, exc_info=True)
        return "عذرًا، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقًا."
