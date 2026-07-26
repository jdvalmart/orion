"""Orion configuration — paths, defaults, and logging setup."""

import logging
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
WHOAMI_FILE = DATA_DIR / "whoami.json"
ERROR_LOG_FILE = DATA_DIR / "errors.log"

DATA_DIR.mkdir(parents=True, exist_ok=True)

_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(_formatter)

_errors = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
_errors.setLevel(logging.WARNING)
_errors.setFormatter(_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_console, _errors],
)
