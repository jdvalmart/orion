"""Diagnostics tool plus the MCP prompt and resource for session start-up."""

from __future__ import annotations

import json

from orion import projects, store
from orion.app import mcp
from orion.models import Health
from orion.tools import READ_ONLY, run


@mcp.tool(annotations=READ_ONLY)
async def orion_health() -> Health:
    """Report Orion's version, database location, counts, integrity and search status."""
    return await run(store.health)


@mcp.resource(
    "orion://project/{name}/context",
    mime_type="application/json",
    description="Phase, next steps, recent sessions and decisions of a project.",
)
def project_context_resource(name: str) -> str:
    """Project context as JSON."""
    context = store.project_context(projects.normalize(name))
    return context.model_dump_json(indent=2)


@mcp.prompt(description="Load a project's context from Orion before starting to work.")
def start_session(project: str) -> str:
    """Prompt that seeds a conversation with the project's stored context.

    Args:
        project: Project name.
    """
    context = store.project_context(projects.normalize(project))
    payload = json.dumps(context.model_dump(), indent=2, ensure_ascii=False)
    return (
        f"We are resuming work on the project '{context.project}'. "
        "This is the context stored in Orion:\n\n"
        f"```json\n{payload}\n```\n\n"
        "Summarise where we left off and propose the next step. Before deciding "
        "anything architectural, search past decisions with recall_context. "
        "Store new decisions with remember_decision and, at the end, call "
        "remember_session with a summary and next steps."
    )
