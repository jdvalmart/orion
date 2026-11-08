"""Real transports: stdio handshake and HTTP bearer-token enforcement."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

pytestmark = pytest.mark.anyio


def _env(data_dir: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("ORION_")}
    env.update(ORION_DATA_DIR=str(data_dir), ORION_SEMANTIC="off", **extra)
    return env


async def test_stdio_handshake(data_dir: Path) -> None:
    transport = StdioTransport(
        command=sys.executable, args=["-m", "orion"], env=_env(data_dir), keep_alive=False
    )
    async with Client(transport) as client:
        names = {tool.name for tool in await client.list_tools()}
        assert "recall_context" in names
        stored = await client.call_tool(
            "remember_decision", {"topic": "t", "decision": "d", "project": "stdio"}
        )
        assert stored.structured_content is not None


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def http_server(data_dir: Path) -> Iterator[str]:
    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "orion", "--transport", "http", "--port", str(port)],
        env=_env(data_dir, ORION_TOKEN="secret-token"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        for _ in range(100):
            try:
                httpx.get(url, timeout=0.5)
                break
            except httpx.TransportError:
                time.sleep(0.1)
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)


async def test_http_requires_token(http_server: str) -> None:
    response = httpx.post(
        http_server,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code == 401

    async with Client(http_server, auth="secret-token") as client:
        assert await client.list_tools()


def test_http_refuses_public_bind_without_token(data_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "orion", "--transport", "http", "--host", "0.0.0.0"],
        env=_env(data_dir),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "ORION_TOKEN" in result.stderr
