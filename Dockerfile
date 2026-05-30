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

# Skills are read-only application code (the agent loads them at runtime).
COPY .claude/skills/ /app/.claude/skills/

# Template: the complete default project layout. Seeded into PROJECT_ROOT on
# first container start (see backend/app/main.py:seed_project_dir). Includes
# foundation md scaffolds, the universal laws/ rules, all helper scripts,
# the pre-seeded schemes catalogue, and empty data ledgers.
COPY goals.md principles.md user-principles.md portfolio.md decisions-log.md \
     /app/template/
COPY laws /app/template/laws
COPY scripts /app/template/scripts
COPY data/market.db /app/template/data/market.db
COPY data/transactions.json /app/template/data/transactions.json
COPY data/recurring.json /app/template/data/recurring.json
COPY data/fund_quality.json /app/template/data/fund_quality.json

# Frontend static build
COPY --from=frontend-builder /build/out/ /app/frontend/out/

ENV PROJECT_ROOT=/app/project \
    SKILLS_ROOT=/app/.claude/skills \
    TEMPLATE_DIR=/app/template \
    PYTHONPATH=/app/backend

# Persistent user data lives here. Mount a host directory at /app/project to
# preserve foundation files, NAV history, and transactions across restarts.
VOLUME ["/app/project"]
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app/backend"]
