# ── Build stage ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps needed by FAISS
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from the builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Expose the port Render expects
EXPOSE 10000

# Default startup command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
