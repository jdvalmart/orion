"""Resolve which project a tool call belongs to.

Order of precedence:
1. The ``project`` argument passed by the assistant.
2. ``ORION_PROJECT`` in the server environment (pin a client to one project).
3. The first MCP root the client advertises (Claude Code and others send the
   workspace folder).
4. The git repository containing the server's working directory (clients
   such as OpenCode start the server inside the project).
5. ``general``.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from fastmcp import Context
from mcp import types

from orion.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_PROJECT = "general"
_INVALID = re.compile(r"[^a-z0-9._-]+")
_ORION_ROOT = Path(__file__).resolve().parents[2]


def normalize(name: str) -> str:
    """Canonical project name: lowercase, dashes for anything outside [a-z0-9._-]."""
    cleaned = _INVALID.sub("-", name.strip().lower()).strip("-.")[:64]
    if not cleaned:
        raise ValueError(f"Invalid project name: {name!r}")
    return cleaned


def _git_root(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def _from_cwd() -> str | None:
    root = _git_root(Path.cwd().resolve())
    if root is None or root == _ORION_ROOT:
        return None
    return normalize(root.name)


async def _from_roots(ctx: Context) -> str | None:
    try:
        session = ctx.session
        supports_roots = session.check_client_capability(
            types.ClientCapabilities(roots=types.RootsCapability())
        )
        if not supports_roots:
            return None
        result = await asyncio.wait_for(session.list_roots(), timeout=2.0)
    except (RuntimeError, ValueError, AttributeError, TimeoutError) as exc:
        logger.debug("MCP roots unavailable: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001 — a misbehaving client must never break a tool call
        logger.debug("MCP roots request failed: %s", exc)
        return None
    for root in result.roots:
        parsed = urlparse(str(root.uri))
        if parsed.scheme == "file" and parsed.path:
            return normalize(Path(unquote(parsed.path)).name)
    return None


async def resolve(ctx: Context | None, explicit: str | None) -> str:
    """Project name for this call."""
    if explicit and explicit.strip():
        return normalize(explicit)
    configured = get_settings().project
    if configured:
        return normalize(configured)
    if ctx is not None:
        from_roots = await _from_roots(ctx)
        if from_roots:
            return from_roots
    return _from_cwd() or DEFAULT_PROJECT
