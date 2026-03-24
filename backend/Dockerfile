FROM python:3.11-slim

WORKDIR /app

# Environment variables for proper logging
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependencies in single layer with --no-cache-dir
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY app/ ./app/
COPY data/ ./data/

# Render sets PORT environment variable dynamically
ENV PORT=10000

# Start FastAPI server with dynamic port
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
