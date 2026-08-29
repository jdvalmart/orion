"""Orion configuration — paths, defaults, and logging setup."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LOGS_DIR = Path(__file__).parent / "logs"
MEMORY_FILE = DATA_DIR / "memory.json"
WHOAMI_FILE = DATA_DIR / "whoami.json"
GRAPH_FILE = DATA_DIR / "graph.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"
CHROMA_PATH = DATA_DIR / "chroma_db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(_formatter)

handlers = [_console]

# Try to add file handlers, but don't fail if permission denied
# (e.g., when running stdio locally while container owns the files)
try:
    _app_log = RotatingFileHandler(
        LOGS_DIR / "orion.log",
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
        delay=True,  # Don't open file until first log
    )
    _app_log.setLevel(logging.INFO)
    _app_log.setFormatter(_formatter)
    handlers.append(_app_log)
except (PermissionError, OSError):
    pass

try:
    _error_log = RotatingFileHandler(
        LOGS_DIR / "errors.log",
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
        delay=True,
    )
    _error_log.setLevel(logging.WARNING)
    _error_log.setFormatter(_formatter)
    handlers.append(_error_log)
except (PermissionError, OSError):
    pass

logging.basicConfig(
    level=logging.INFO,
    handlers=handlers,
)