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

#### Option A: Using render.yaml (Recommended)

1. Push to GitHub
2. Create Web Service on [Render](https://dashboard.render.com)
3. Connect repository: `shahdtarraf/Fodowa_chatbot`
4. Render will auto-detect `backend/render.yaml`
5. Add environment variable: `HUGGINGFACEHUB_API_TOKEN`

#### Option B: Manual Configuration

1. Create Web Service on [Render](https://dashboard.render.com)
2. Connect repository: `shahdtarraf/Fodowa_chatbot`
3. Set **Root Directory**: `backend`
4. Set **Environment**: `Docker`
5. Set **Docker Context**: `backend`
6. Set **Dockerfile Path**: `./Dockerfile`

#### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `HUGGINGFACEHUB_API_TOKEN` | HF API token for embeddings | ✅ Yes |
| `HF_MODEL_ID` | LLM model ID | No (default: Qwen/Qwen2.5-7B-Instruct) |
| `HF_EMBEDDING_MODEL` | Embedding model | No (default: paraphrase-multilingual-MiniLM-L12-v2) |
| `RAG_TOP_K` | Retrieved chunks count | No (default: 5) |

#### Expected Logs on Startup

```
✅ Loading FAISS index from 'data/faiss_index' …
✅ Initializing HuggingFace embeddings...
✅ FAISS index loaded successfully (16 vectors).
✅ Uvicorn running on http://0.0.0.0:$PORT
```

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
