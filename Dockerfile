# Production Dockerfile for Render deployment
# This file MUST be at the root level for Render to find it

FROM python:3.11-slim

WORKDIR /app

# Environment variables for proper logging and fast startup
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TRANSFORMERS_CACHE=/app/.cache
ENV HF_HOME=/app/.cache

# Install dependencies in single layer with --no-cache-dir
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model during build (not runtime)
# This caches the model in the Docker image for faster startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Copy application code and data (including pre-built FAISS index)
COPY backend/app/ ./app/
COPY backend/data/ ./data/

# Render sets PORT environment variable dynamically
ENV PORT=10000

# Start FastAPI server with dynamic port
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
