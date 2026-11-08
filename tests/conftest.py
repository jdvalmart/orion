"""Shared fixtures. Every test runs against a fresh temporary data dir — never real data."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastmcp import Client

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(autouse=True)
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate Orion: temp data dir, keyword search only, no project pinning, no git cwd."""
    directory = tmp_path / "data"
    monkeypatch.setenv("ORION_DATA_DIR", str(directory))
    monkeypatch.setenv("ORION_SEMANTIC", "off")
    for name in ("ORION_PROJECT", "ORION_S3_BUCKET", "ORION_TOKEN", "ORION_MODELS_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    return directory


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    """In-memory MCP client connected to the Orion server."""
    from orion.app import mcp

    async with Client(mcp) as connected:
        yield connected
