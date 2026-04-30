# ── Stage 1: dependency install ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed only for building some Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY app ./app

# Ensure database directory exists (used by SQLite in dev; ignored when DATABASE_URL is set)
RUN mkdir -p /app/database /app/app/rl/models && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Azure Container Apps expects the container to listen on $PORT (default 8000).
# We also enable --workers 1 to keep SQLite file-locking safe; scale via replicas.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]