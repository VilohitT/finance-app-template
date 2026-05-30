"""Path and constant configuration for the backend.

In Docker, PROJECT_ROOT defaults to /app/data (the volume mount), so the user's
foundation files persist across container restarts. In dev, set PROJECT_ROOT
to the repo root to point at the existing template directory.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "/app/data")).resolve()
SKILLS_ROOT = Path(os.environ.get("SKILLS_ROOT", "/app/.claude/skills")).resolve()
SCRIPTS_ROOT = Path(os.environ.get("SCRIPTS_ROOT", "/app/scripts")).resolve()
LAWS_ROOT = Path(os.environ.get("LAWS_ROOT", PROJECT_ROOT / "laws")).resolve()

CONFIG_DIR = PROJECT_ROOT / ".config"
CONFIG_FILE = CONFIG_DIR / "settings.json"
SESSIONS_DIR = PROJECT_ROOT / ".sessions"

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_EFFORT = "high"
MAX_TOKENS = 32000

# Models the user can pick in /settings. Keep this short and accurate;
# unfamiliar IDs will 404 on the Anthropic API.
AVAILABLE_MODELS = [
    {"id": "claude-opus-4-7", "label": "Opus 4.7 — most capable"},
    {"id": "claude-opus-4-6", "label": "Opus 4.6 — prior Opus, still strong"},
    {"id": "claude-sonnet-4-6", "label": "Sonnet 4.6 — fast + capable"},
    {"id": "claude-haiku-4-5", "label": "Haiku 4.5 — fastest, cheapest"},
]

AVAILABLE_EFFORTS = [
    {"id": "low", "label": "Low — fast, less reasoning"},
    {"id": "medium", "label": "Medium — balanced"},
    {"id": "high", "label": "High — recommended"},
    {"id": "xhigh", "label": "xHigh — for coding / agentic work"},
    {"id": "max", "label": "Max — Opus only, max correctness"},
]

# Tool restrictions: allowed roots for filesystem operations.
ALLOWED_READ_ROOTS = [PROJECT_ROOT, SKILLS_ROOT, SCRIPTS_ROOT]
ALLOWED_WRITE_ROOTS = [PROJECT_ROOT]
