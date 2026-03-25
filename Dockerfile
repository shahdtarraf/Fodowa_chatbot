# Minimal Dockerfile for Render Free (512MB RAM)
# NO ML models, NO embeddings, fast startup

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install minimal dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and FAQ data only
COPY backend/app/ ./app/
COPY backend/data/faq.json ./data/faq.json

# Render port
ENV PORT=10000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
