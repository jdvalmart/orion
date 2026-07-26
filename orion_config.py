"""Orion configuration — paths, defaults, and logging setup."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LOGS_DIR = Path(__file__).parent / "logs"
MEMORY_FILE = DATA_DIR / "memory.json"
WHOAMI_FILE = DATA_DIR / "whoami.json"
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

_app_log = RotatingFileHandler(
    LOGS_DIR / "orion.log",
    maxBytes=1_048_576,  # 1 MB
    backupCount=3,
    encoding="utf-8",
)
_app_log.setLevel(logging.INFO)
_app_log.setFormatter(_formatter)

_error_log = RotatingFileHandler(
    LOGS_DIR / "errors.log",
    maxBytes=1_048_576,  # 1 MB
    backupCount=3,
    encoding="utf-8",
)
_error_log.setLevel(logging.WARNING)
_error_log.setFormatter(_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_console, _app_log, _error_log],
)