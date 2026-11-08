"""Orion MCP tools.

Each module registers its tools with ``@mcp.tool`` on import. Tools are thin
async wrappers: they resolve the project, run the blocking store call in a
worker thread (embedding can take a second) and map domain errors to MCP tool
errors so the client sees ``isError: true`` instead of a fake success string.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from fastmcp.exceptions import ToolError

from orion.store import InvalidInputError, NotFoundError

T = TypeVar("T")


async def run(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a store function off the event loop, translating domain errors."""
    try:
        return await asyncio.to_thread(fn, *args, **kwargs)
    except (NotFoundError, InvalidInputError, ValueError) as exc:
        raise ToolError(str(exc)) from exc


def split_tags(tags: list[str] | str | None) -> list[str] | None:
    """Accept a list or the legacy comma-separated string."""
    if tags is None:
        return None
    if isinstance(tags, str):
        return [t for t in tags.split(",") if t.strip()]
    return tags


READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}
WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False}
DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False}
