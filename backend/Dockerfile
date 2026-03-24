FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY data/ ./data/

# Render sets PORT environment variable dynamically
# Default to 10000 for local development
ENV PORT=10000

# Start FastAPI server with dynamic port
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
