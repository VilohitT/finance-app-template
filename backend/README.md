# Backend — FastAPI + Anthropic SDK

Python service that exposes the finance-app skills via a WebSocket chat interface and REST endpoints. Designed to run inside a Docker container with the user's data directory mounted at `/app/data`.

## Architecture

- **Custom tool-use loop**, not Managed Agents — tools (`read_file`, `write_file`, `edit_file`, `bash`) execute on the user's local filesystem so foundation md's and the SQLite NAV database stay local.
- **WebSocket** (`/ws/chat`) for streaming chat responses.
- **REST** for settings, skill listing, and file browsing.
- **APScheduler** runs `scripts/fetch_nav.py` daily at 22:30 local time (Phase 5 — not yet wired).

## Local dev

```bash
pip install -r requirements.txt
PROJECT_ROOT=$(pwd)/.. SKILLS_ROOT=$(pwd)/../.claude/skills SCRIPTS_ROOT=$(pwd)/../scripts \
  uvicorn app.main:app --reload --port 8000
```

The frontend should be running separately on port 3000 (see `../frontend/README.md`).

## Production

The Dockerfile builds both the backend and the frontend (statically exported) into a single image. The backend serves the frontend at `/` and the API at `/api/*` / `/ws/chat`.
