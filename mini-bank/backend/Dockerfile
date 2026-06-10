# syntax=docker/dockerfile:1.7
# Build context: mini-bank/ (the whole directory).
# Build with: docker buildx build --platform linux/amd64 -f backend/Dockerfile -t IMAGE .

# ---- Stage 1: build React/Vite frontend ----
FROM node:20-alpine AS frontend-builder
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/index.html ./
COPY frontend/src ./src
RUN npm run build

# ---- Stage 2: build Python wheels ----
FROM python:3.12-slim AS py-builder
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/src ./src
RUN pip install --no-cache-dir --upgrade pip build && \
    pip wheel --no-cache-dir --wheel-dir=/wheels .

# ---- Stage 3: runtime ----
FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home --shell /bin/bash app && \
    apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
COPY --from=py-builder /wheels /wheels
COPY backend/pyproject.toml ./
COPY backend/src ./src
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
RUN pip install --no-cache-dir --no-index --find-links=/wheels minibank && \
    rm -rf /wheels
# Frontend static files served by FastAPI StaticFiles mount in main.py
COPY --from=frontend-builder /fe/dist /app/static
USER app
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    STATIC_DIR=/app/static
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn minibank.main:app --host 0.0.0.0 --port ${PORT}"]
