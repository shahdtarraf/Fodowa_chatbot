"""
Streamlit UI for FODWA Chatbot with Authentication.

Features:
- Login/Signup pages
- Per-user chat history
- Persistent messages in SQLite
- Predefined questions
"""

import streamlit as st
import requests
from typing import List, Dict

# API endpoint
API_URL = "http://localhost:8000"  # Change for production

# Page config
st.set_page_config(
    page_title="FODWA Chatbot",
    page_icon="🤖",
    layout="centered",
)

# Import auth module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.auth_handler import signup, login
from app.database.db import get_user_messages, save_message, clear_user_messages


# ── Session State Initialization ────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "login"


# ── Helper Functions ──────────────────────────────────────────────────────
def load_chat_history(user_id: int) -> List[Dict]:
    """Load chat history from database for a user."""
    return get_user_messages(user_id)


def send_chat_request(user_message: str, user_id: int) -> str:
    """Send chat request to FastAPI backend."""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "user_message": user_message,
                "conversation_id": str(user_id),
            },
            timeout=60,
        )
        if response.status_code == 200:
            return response.json().get("response", "Sorry, I couldn't process that.")
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


def display_chat_message(role: str, content: str):
    """Display a chat message with appropriate styling."""
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content)


# ── Login Page ────────────────────────────────────────────────────────────
def show_login_page():
    st.title("🤖 FODWA Chatbot")
    st.markdown("### Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", max_chars=50)
        password = st.text_input("Password", type="password", max_chars=100)
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                result = login(username, password)
                if result["success"]:
                    st.session_state.user_id = result["user_id"]
                    st.session_state.username = result["username"]
                    st.session_state.messages = load_chat_history(result["user_id"])
                    st.session_state.page = "chat"
                    st.rerun()
                else:
                    st.error(result["error"])
    
    st.markdown("---")
    if st.button("Create new account", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()


# ── Signup Page ───────────────────────────────────────────────────────────
def show_signup_page():
    st.title("🤖 FODWA Chatbot")
    st.markdown("### Create Account")
    
    with st.form("signup_form"):
        username = st.text_input("Username (min 3 characters)", max_chars=50)
        password = st.text_input("Password (min 6 characters)", type="password", max_chars=100)
        confirm = st.text_input("Confirm Password", type="password", max_chars=100)
        submit = st.form_submit_button("Sign Up", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please fill all fields")
            elif password != confirm:
                st.error("Passwords do not match")
            else:
                result = signup(username, password)
                if result["success"]:
                    st.success("Account created! Please login.")
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(result["error"])
    
    st.markdown("---")
    if st.button("Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()


# ── Chat Page ──────────────────────────────────────────────────────────────
def show_chat_page():
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("🤖 FODWA Chatbot")
    with col2:
        st.write(f"👤 **{st.session_state.username}**")
    with col3:
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.messages = []
            st.session_state.page = "login"
            st.rerun()
    
    st.markdown("---")
    
    # Predefined questions
    st.markdown("**💡 Quick Questions:**")
    predefined_questions = [
        "ما هي منصة فودوا؟",
        "كيف يمكنني نشر إعلان؟",
        "ما هي الخدمات المتاحة؟",
        "كيف أتواصل مع الدعم؟",
    ]
    
    cols = st.columns(4)
    for i, question in enumerate(predefined_questions):
        if cols[i].button(question, key=f"pq_{i}"):
            # Save user message
            save_message(st.session_state.user_id, "user", question)
            st.session_state.messages.append({"role": "user", "content": question})
            
            # Get response
            with st.spinner("جاري التفكير..."):
                response = send_chat_request(question, st.session_state.user_id)
            
            # Save assistant message
            save_message(st.session_state.user_id, "assistant", response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    st.markdown("---")
    
    # Chat history
    st.markdown("**💬 Chat History:**")
    
    # Display messages
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            display_chat_message(msg["role"], msg["content"])
    
    # Chat input
    if prompt := st.chat_input("اكتب رسالتك هنا..."):
        # Save user message
        save_message(st.session_state.user_id, "user", prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with chat_container:
            display_chat_message("user", prompt)
        
        # Get response
        with st.spinner("جاري التفكير..."):
            response = send_chat_request(prompt, st.session_state.user_id)
        
        # Save and display assistant message
        save_message(st.session_state.user_id, "assistant", response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        with chat_container:
            display_chat_message("assistant", response)
    
    # Clear chat button
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        clear_user_messages(st.session_state.user_id)
        st.session_state.messages = []
        st.rerun()


# ── Main App Router ───────────────────────────────────────────────────────
def main():
    if st.session_state.user_id is None:
        if st.session_state.page == "signup":
            show_signup_page()
        else:
            show_login_page()
    else:
        show_chat_page()


if __name__ == "__main__":
    main()
