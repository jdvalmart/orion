"""Runtime configuration read from environment variables.

Settings are read on every call instead of cached at import time so tests
(and long-lived HTTP servers) pick up changes without re-importing modules.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _default_data_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "orion"


@dataclass(frozen=True)
class Settings:
    """Resolved Orion settings."""

    data_dir: Path
    log_level: str
    project: str | None
    token: str | None
    semantic: str
    embed_model: str
    s3_bucket: str | None
    s3_prefix: str
    models_override: Path | None = None

    @property
    def db_path(self) -> Path:
        return self.data_dir / "orion.db"

    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def models_dir(self) -> Path:
        return self.models_override or self.data_dir / "models"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"


def get_settings() -> Settings:
    """Read settings from the environment."""
    env = os.environ
    data_dir = Path(env["ORION_DATA_DIR"]).expanduser() if env.get("ORION_DATA_DIR") else None
    return Settings(
        data_dir=data_dir or _default_data_dir(),
        log_level=env.get("ORION_LOG_LEVEL", "INFO").upper(),
        project=env.get("ORION_PROJECT") or None,
        token=env.get("ORION_TOKEN") or None,
        semantic=env.get("ORION_SEMANTIC", "auto").lower(),
        embed_model=env.get("ORION_EMBED_MODEL", DEFAULT_EMBED_MODEL),
        s3_bucket=env.get("ORION_S3_BUCKET") or None,
        s3_prefix=env.get("ORION_S3_PREFIX", "orion-backup").strip("/"),
        models_override=Path(env["ORION_MODELS_DIR"]).expanduser()
        if env.get("ORION_MODELS_DIR")
        else None,
    )


def setup_logging(settings: Settings) -> None:
    """Log to stderr (never stdout: stdio transport owns it) and a rotating file."""
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handlers: list[logging.Handler] = []

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    handlers.append(console)

    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_dir / "orion.log",
            maxBytes=1_048_576,
            backupCount=3,
            encoding="utf-8",
            delay=True,
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except OSError as exc:
        sys.stderr.write(f"orion: file logging disabled: {exc}\n")

    logging.basicConfig(level=settings.log_level, handlers=handlers, force=True)
