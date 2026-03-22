# 🤖 FODWA AI Chatbot Microservice

مساعد ذكي لمنصة **فودوا (FODWA)** — يجيب باللغة العربية بناءً على قاعدة المعرفة.

## Architecture

```
User → Frontend → Django REST → [POST /chat] → FastAPI Chatbot → HuggingFace LLM
                                                    ↕
                                               FAISS (RAG)
```

## Tech Stack

Python 3.11 · FastAPI · LangChain · FAISS · HuggingFace Inference API · PyJWT · Uvicorn

---

## 🚀 Local Setup

### 1. Create & activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your values:
#   HUGGINGFACEHUB_API_TOKEN=hf_...
#   HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
#   DJANGO_BACKEND_URL=https://your-django-api.com
#   JWT_SECRET_KEY=your-secret
#   JWT_ALGORITHM=HS256
```

### 4. Place your knowledge-base PDF

```bash
# Copy your platform PDF into the data/ directory:
cp /path/to/your/platform_guide.pdf data/knowledge_base.pdf
```

### 5. Run the ingestion script (builds the FAISS index)

```bash
python app/ingest_data.py
```

You should see output like:
```
📄  Loading PDF from 'data/knowledge_base.pdf' …
✂️  Splitting into chunks …
🧠  Generating embeddings via HuggingFace API …
💾  FAISS index saved to 'data/faiss_index'.
✅  Ingestion complete — N chunks indexed.
```

### 6. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Test it

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "ما هي منصة فودوا؟",
    "conversation_id": "test-123",
    "token": ""
  }'
```

---

## 🌐 Deploy on Render

### Option A: Docker Deploy

1. Push this repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Connect your GitHub repository.
4. Set **Environment** to **Docker**.
5. Add environment variables in the Render dashboard:
   - `HUGGINGFACEHUB_API_TOKEN`
   - `HF_MODEL_ID` (optional, defaults to Qwen/Qwen2.5-7B-Instruct)
   - `DJANGO_BACKEND_URL`
   - `JWT_SECRET_KEY`
   - `JWT_ALGORITHM`
6. **Important**: Run the ingestion script before deploy or include the pre-built `data/faiss_index/` in the repo.

### Option B: Native Python Deploy

1. Set **Build Command**: `pip install -r requirements.txt`
2. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
3. Add the same environment variables.

---

## 📁 Project Structure

```
app/
 ├── main.py                  # FastAPI app entry-point
 ├── ingest_data.py           # PDF → FAISS ingestion script
 ├── routes/
 │    └── chat.py             # POST /chat endpoint
 ├── services/
 │    ├── llm_service.py      # LLM agent orchestration
 │    ├── rag_service.py      # FAISS similarity search
 │    ├── memory_service.py   # In-memory conversation history
 │    └── tool_service.py     # LangChain tool (profile lookup)
 ├── auth/
 │    └── jwt_handler.py      # JWT decode (guest-safe)
 ├── database/
 │    └── vector_store.py     # FAISS index loader
 ├── models/
 │    └── schemas.py          # Pydantic request/response models
 └── utils/
      ├── config.py           # Environment config
      └── logger.py           # Centralised logger
data/
 └── knowledge_base.pdf       # Your platform PDF
```

## API Reference

### `POST /chat`

**Request:**
```json
{
  "user_message": "string",
  "conversation_id": "string",
  "token": "string | null"
}
```

**Response:**
```json
{
  "response": "string (Arabic)"
}
```

### `GET /health`

Returns `{"status": "ok", "service": "fodwa-chatbot"}`.

---

## License

Internal — FODWA Platform.
