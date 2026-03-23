"""
FODWA AI Assistant - Streamlit Frontend

Production-ready chat UI for Streamlit Cloud deployment.
Connects to FastAPI backend on Render.

Features:
- Modern chat interface with st.chat_message
- Predefined quick questions
- Session-based chat memory
- Arabic-first design
"""

import streamlit as st
import requests
from typing import List, Dict

# ── Configuration ────────────────────────────────────────────────────────
API_URL = "https://fodowa-chatbot.onrender.com/chat"

# Page config
st.set_page_config(
    page_title="FODWA AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session State Initialization ────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "streamlit-session"


# ── Helper Functions ──────────────────────────────────────────────────────
def send_chat_request(user_message: str) -> str:
    """Send chat request to FastAPI backend on Render."""
    try:
        response = requests.post(
            API_URL,
            json={
                "user_message": user_message,
                "conversation_id": st.session_state.conversation_id,
            },
            timeout=60,
        )
        if response.status_code == 200:
            return response.json().get("response", "عذراً، لم أتمكن من معالجة طلبك.")
        else:
            return f"⚠️ خطأ في الخادم: {response.status_code}"
    except requests.exceptions.Timeout:
        return "⚠️ انتهت مهلة الاتصال. يرجى المحاولة مرة أخرى."
    except requests.exceptions.ConnectionError:
        return "⚠️ حدث خطأ في الاتصال بالخادم. يرجى التحقق من اتصالك بالإنترنت."
    except Exception as e:
        return f"⚠️ حدث خطأ غير متوقع: {str(e)}"


def display_message(role: str, content: str):
    """Display a chat message with appropriate styling."""
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content)


# ── UI Header ──────────────────────────────────────────────────────────────
st.title("🤖 FODWA AI Assistant")
st.markdown("""
مساعد ذكي لمنصة فودوا - اسأل أي سؤال عن خدمات المنصة والبيع والشراء والإعلانات.
""")

st.markdown("---")

# ── Predefined Questions ──────────────────────────────────────────────────
st.markdown("### 💡 أسئلة سريعة")

predefined_questions = [
    "ما هي منصة فودوا؟",
    "ما الخدمات التي تقدمها المنصة؟",
    "كيف يمكنني البيع على فودوا؟",
    "هل المنصة مجانية؟",
]

cols = st.columns(4)
for i, question in enumerate(predefined_questions):
    if cols[i].button(question, key=f"pq_{i}", use_container_width=True):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Get response from API
        with st.spinner("جاري التفكير..."):
            response = send_chat_request(question)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

st.markdown("---")

# ── Chat History Display ──────────────────────────────────────────────────
st.markdown("### 💬 المحادثة")

# Display all messages
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        display_message(msg["role"], msg["content"])

# ── Chat Input ─────────────────────────────────────────────────────────────
if prompt := st.chat_input("اكتب سؤالك هنا..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message immediately
    with chat_container:
        display_message("user", prompt)
    
    # Get response from API
    with st.spinner("جاري التفكير..."):
        response = send_chat_request(prompt)
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display assistant response
    with chat_container:
        display_message("assistant", response)

# ── Clear Chat Button ─────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9em;">
    🚀 مدعوم بواسطة AI | FODWA Chatbot v1.0
</div>
""", unsafe_allow_html=True)
