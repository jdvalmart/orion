"""Profile tools: who the developer is, stored as free-form sections."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from orion import store
from orion.app import mcp
from orion.tools import READ_ONLY, WRITE, run


@mcp.tool(annotations=READ_ONLY)
async def whoami() -> dict[str, Any]:
    """Return the developer's profile: role, work, skills, projects, goals.

    Use it when you need context about the person you are assisting.
    """
    return await run(store.get_profile)


@mcp.tool(annotations=WRITE)
async def update_profile(
    section: Annotated[str, Field(min_length=1, max_length=64)],
    value: Annotated[
        Any,
        Field(description="New content for the section (text, list or object); null removes it."),
    ],
) -> dict[str, Any]:
    """Replace one section of the developer profile, or remove it.

    Args:
        section: Section name, e.g. "summary", "skills", "learning_goals".
        value: New content for the section (text, list or object); null removes it.
    """
    return await run(store.set_profile_section, section, value)
