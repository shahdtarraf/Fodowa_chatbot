# 🤖 FODWA AI Chatbot - Production Architecture

مساعد ذكي لمنصة **فودوا (FODWA)** — يجيب باللغة العربية بناءً على قاعدة المعرفة.

## 📁 Project Structure

```
Fodowa_chatbot/
├── backend/                 # FastAPI + RAG + FAISS (Render)
│   ├── app/
│   │   ├── main.py         # FastAPI entry point
│   │   ├── database/       # Vector store & SQLite
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # RAG, LLM, Memory
│   │   └── utils/          # Config, Logger
│   ├── data/
│   │   ├── faiss_index/    # Pre-built FAISS index
│   │   └── knowledge_base.pdf
│   ├── Dockerfile
│   ├── requirements.txt    # Heavy ML dependencies
│   └── render.yaml
│
├── frontend/               # Streamlit UI (Streamlit Cloud)
│   ├── streamlit_app.py
│   └── requirements.txt    # Lightweight only
│
└── README.md
```

## 🔗 Architecture

```
┌─────────────────┐
│  Streamlit UI   │  (Streamlit Cloud)
│  frontend/      │
└────────┬────────┘
         │ POST /chat
         ▼
┌─────────────────┐
│  FastAPI        │  (Render)
│  backend/       │
│  ├─ FAISS       │
│  ├─ RAG         │
│  └─ LLM API     │
└─────────────────┘
```

## Tech Stack

**Backend:** Python 3.11 · FastAPI · LangChain · FAISS · HuggingFace Inference API

**Frontend:** Streamlit · Requests

---

## 🚀 Deployment

### Backend (Render)

1. Push to GitHub
2. Create Web Service on [Render](https://render.com)
3. Set **Root Directory**: `backend`
4. Set **Docker Context**: `backend`
5. Environment variables:
   - `HUGGINGFACEHUB_API_TOKEN`
   - `HF_MODEL_ID` (default: Qwen/Qwen2.5-7B-Instruct)
   - `HF_EMBEDDING_MODEL`

**Backend URL:** `https://fodowa-chatbot.onrender.com`

### Frontend (Streamlit Cloud)

1. Go to [Streamlit Cloud](https://share.streamlit.io)
2. Deploy from `frontend/streamlit_app.py`
3. Requirements: `frontend/requirements.txt`

---

## 🧪 Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## 📦 Dependencies

### Backend (Heavy - Render)
- fastapi, uvicorn
- langchain, langchain-community, langchain-core
- faiss-cpu
- huggingface-hub

### Frontend (Lightweight - Streamlit Cloud)
- streamlit
- requests

---

## API Reference

### `POST /chat`

**Request:**
```json
{
  "user_message": "ما هي منصة فودوا؟",
  "conversation_id": "session-123"
}
```

**Response:**
```json
{
  "response": "منصة فودوا هي منصة إلكترونية متعددة الخدمات..."
}
```

### `GET /health`

Returns `{"status": "ok", "service": "fodwa-chatbot"}`.

---

## License

Internal — FODWA Platform.
