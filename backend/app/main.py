"""FastAPI application: WebSocket chat, REST endpoints for skills/settings/files."""

import asyncio
import json
import logging
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agent, config, scheduler, settings, skills

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_project_dir() -> None:
    """Populate PROJECT_ROOT from /app/template on first run.

    Only seeds items that don't already exist — preserves user changes across
    container restarts. To pick up template updates after upgrading the image,
    delete the relevant file/directory under your mounted project volume and
    restart the container.

    In dev mode, /app/template won't exist; we skip silently (the existing repo
    layout already has everything in the right places).
    """
    if not config.TEMPLATE_DIR.exists():
        logger.info(
            "No template at %s — skipping seed (dev mode)", config.TEMPLATE_DIR
        )
        return
    config.PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    seeded: list[str] = []
    for item in sorted(config.TEMPLATE_DIR.iterdir()):
        dest = config.PROJECT_ROOT / item.name
        if dest.exists():
            continue
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
        seeded.append(item.name)
    if seeded:
        logger.info("Seeded project dir with: %s", ", ".join(seeded))
    else:
        logger.info("Project dir already populated; nothing to seed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_project_dir()
    scheduler.service.start()
    try:
        yield
    finally:
        scheduler.service.shutdown()


app = FastAPI(title="Finance App Backend", version="0.1.0", lifespan=lifespan)

# CORS for local dev where the frontend may run on a different port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Settings ----------

class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    model: str | None = None
    effort: str | None = None
    daily_nav_enabled: bool | None = None


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    s = settings.load()
    # Don't echo the API key; just whether it's configured.
    return {
        "has_api_key": bool(s.anthropic_api_key),
        "model": s.model,
        "effort": s.effort,
        "daily_nav_enabled": s.daily_nav_enabled,
        "available_models": config.AVAILABLE_MODELS,
        "available_efforts": config.AVAILABLE_EFFORTS,
    }


@app.put("/api/settings")
def update_settings(payload: SettingsUpdate) -> dict[str, Any]:
    s = settings.load()
    data = payload.model_dump(exclude_none=True)
    if "anthropic_api_key" in data and not data["anthropic_api_key"]:
        data.pop("anthropic_api_key")
    updated = s.model_copy(update=data)
    settings.save(updated)
    # If the scheduler toggle changed, reconcile the running jobs.
    scheduler.service.sync_with_settings()
    return get_settings()


# ---------- Scheduler ----------

@app.get("/api/scheduler")
def scheduler_status() -> dict[str, Any]:
    return scheduler.service.status()


@app.post("/api/scheduler/run/{job_id}")
async def scheduler_run(job_id: str) -> dict[str, Any]:
    try:
        await scheduler.service.trigger(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return scheduler.service.status()


# ---------- Skills ----------

@app.get("/api/skills")
def list_skills() -> list[dict]:
    return skills.list_skills()


# ---------- Files ----------

class FileEntry(BaseModel):
    path: str
    is_dir: bool
    size: int | None = None


@app.get("/api/files")
def list_files(path: str = "") -> list[FileEntry]:
    """List files under the project root (or a subdirectory)."""
    target = (config.PROJECT_ROOT / path).resolve()
    try:
        target.relative_to(config.PROJECT_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path is outside project root")
    if not target.exists() or not target.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    entries = []
    for child in sorted(target.iterdir()):
        # Skip hidden files and the auto-config directory.
        if child.name.startswith("."):
            continue
        rel = str(child.relative_to(config.PROJECT_ROOT))
        entries.append(
            FileEntry(
                path=rel,
                is_dir=child.is_dir(),
                size=child.stat().st_size if child.is_file() else None,
            )
        )
    return entries


@app.get("/api/files/content")
def get_file_content(path: str) -> dict[str, Any]:
    target = (config.PROJECT_ROOT / path).resolve()
    try:
        target.relative_to(config.PROJECT_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path is outside project root")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="File is not text/UTF-8")
    return {"path": path, "content": content, "size": target.stat().st_size}


# ---------- WebSocket chat ----------

@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket) -> None:
    await ws.accept()
    session = agent.Session()
    try:
        while True:
            raw = await ws.receive_text()
            payload = json.loads(raw)
            kind = payload.get("kind")
            if kind == "skill":
                skill_name = payload["skill"]
                user_message = payload.get("message", "")
                await ws.send_text(
                    json.dumps({"type": "skill_started", "skill": skill_name})
                )
                async for event in agent.start_skill(session, skill_name, user_message):
                    await ws.send_text(json.dumps(event))
            elif kind == "message":
                user_message = payload.get("message", "")
                async for event in agent.continue_session(session, user_message):
                    await ws.send_text(json.dumps(event))
            elif kind == "reset":
                session = agent.Session()
                await ws.send_text(json.dumps({"type": "session_reset"}))
            elif kind == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
            else:
                await ws.send_text(
                    json.dumps({"type": "error", "message": f"Unknown kind: {kind}"})
                )
    except WebSocketDisconnect:
        return
    except Exception as exc:
        logger.exception("ws error")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            pass


# ---------- Health ----------

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------- Static frontend ----------
# In production the frontend is built into /app/frontend/out and served from /.
# In dev the frontend runs separately on :3000 and this mount is a no-op.

FRONTEND_DIR = Path("/app/frontend/out")
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
