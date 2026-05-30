"""Persistent settings: API key, model selection, user preferences."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from . import config


class Settings(BaseModel):
    anthropic_api_key: Optional[str] = None
    model: str = config.DEFAULT_MODEL
    effort: str = config.DEFAULT_EFFORT
    daily_nav_enabled: bool = True


def load() -> Settings:
    if not config.CONFIG_FILE.exists():
        return Settings()
    try:
        data = json.loads(config.CONFIG_FILE.read_text())
        return Settings.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return Settings()


def save(settings: Settings) -> None:
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = config.CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(settings.model_dump_json(indent=2))
    tmp.replace(config.CONFIG_FILE)
    # Restrict permissions — contains the API key.
    config.CONFIG_FILE.chmod(0o600)
