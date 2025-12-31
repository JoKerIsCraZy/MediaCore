# ==============================================
# MediaCore - Single Container Dockerfile
# ==============================================
# This builds both frontend and backend into one
# optimized container

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Build Backend
FROM python:3.12-slim AS backend-builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 3: Production
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r mediacore && useradd -r -g mediacore mediacore

# Install wheels from builder
COPY --from=backend-builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy backend code
COPY backend/ .

# Copy built frontend to static directory
COPY --from=frontend-builder /app/frontend/dist ./static

# Create data directory
RUN mkdir -p /app/data && chown -R mediacore:mediacore /app

# Switch to non-root user
USER mediacore

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the application (host/port configurable via env)
CMD ["sh", "-c", "uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
