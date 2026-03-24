FROM python:3.11-slim

WORKDIR /app

# Environment variables for proper logging
ENV PYTHONUNBUFFERED=1

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY app/ ./app/
COPY data/ ./data/

# Render sets PORT environment variable dynamically
# Default to 10000 for local development
ENV PORT=10000

# Start FastAPI server with dynamic port
# FAISS index will be rebuilt at runtime if needed (requires HUGGINGFACEHUB_API_TOKEN)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
