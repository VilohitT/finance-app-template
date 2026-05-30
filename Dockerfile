# Multi-stage build: compile the Next.js frontend, then layer it into the
# Python backend image. Single image serves both at the same port.

# ---------- Stage 1: build frontend ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: backend ----------
FROM python:3.11-slim AS backend
WORKDIR /app

# System deps: sqlite3 CLI for scripts that shell out, ca-certificates for
# outbound HTTPS to AMFI, plus build tools for any wheels that need them.
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps first for layer caching.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Backend source
COPY backend/ /app/backend/

# Skills, scripts, laws — baked into the image (not user data).
COPY .claude/skills/ /app/.claude/skills/
COPY scripts/ /app/scripts/
COPY laws/ /app/laws/

# Foundation file scaffolds — used by /setup to seed an empty data volume.
COPY goals.md principles.md user-principles.md portfolio.md decisions-log.md /app/template/

# Frontend static build
COPY --from=frontend-builder /build/out/ /app/frontend/out/

ENV PROJECT_ROOT=/app/data \
    SKILLS_ROOT=/app/.claude/skills \
    SCRIPTS_ROOT=/app/scripts \
    PYTHONPATH=/app/backend

# Default: mount the user's data directory at /app/data.
VOLUME ["/app/data"]
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app/backend"]
