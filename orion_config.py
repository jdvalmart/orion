"""Orion configuration — paths, defaults, constants."""

from pathlib import Path

# Data directory (gitignored)
DATA_DIR = Path(__file__).parent / "data"

# Storage files
MEMORY_FILE = DATA_DIR / "memory.json"

# Ensure data directory exists on import
DATA_DIR.mkdir(parents=True, exist_ok=True)
