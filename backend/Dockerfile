# Stage 1: Build Vue frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json .
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
LABEL org.opencontainers.image.title="web-rsync" \
      org.opencontainers.image.description="Web UI for managing rsync jobs" \
      org.opencontainers.image.url="https://hub.docker.com/r/jabastien/web-rsync" \
      org.opencontainers.image.source="https://github.com/jabastien/web-rsync" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.authors="Alain"
WORKDIR /app

RUN apt-get update && apt-get install -y rsync openssh-client && rm -rf /var/lib/apt/lists/*

COPY --from=frontend-builder /build/backend/static ./backend/static

COPY backend/pyproject.toml .
RUN pip install uv && uv pip install --system -r pyproject.toml

COPY backend/ ./backend/

ENV DATA_DIR=/data
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
