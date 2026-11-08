"""Session tools: record work sessions and restore a project's context."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from orion import projects, store
from orion.app import mcp
from orion.models import ProjectContext, ProjectInfo, Scope, Session, SessionPage
from orion.tools import READ_ONLY, WRITE, run, split_tags


@mcp.tool(annotations=WRITE)
async def remember_session(
    summary: Annotated[str, Field(min_length=1, max_length=20_000)],
    next_steps: Annotated[str | None, Field(max_length=5_000)] = None,
    phase: Annotated[str | None, Field(max_length=200)] = None,
    tags: list[str] | str | None = None,
    decisions_made: list[int] | None = None,
    project: Annotated[str | None, Field(description="Project name.")] = None,
    ctx: Context | None = None,
) -> Session:
    """Save what happened in this session. Call it at the end of every session.

    Args:
        summary: What was accomplished.
        next_steps: What should happen next; shown by recall_session.
        phase: Current project phase or milestone, if it changed.
        tags: Optional tags.
        decisions_made: IDs of decisions stored during the session.
        project: Project name. Omit to use the current workspace's project.
    """
    name = await projects.resolve(ctx, project)
    return await run(
        store.add_session, name, summary, split_tags(tags), decisions_made, next_steps, phase
    )


@mcp.tool(annotations=READ_ONLY)
async def recall_session(
    project: Annotated[str | None, Field(description="Project name.")] = None,
    ctx: Context | None = None,
) -> ProjectContext:
    """Restore a project's context: phase, next steps, recent sessions and decisions.

    Call it at the start of every session.

    Args:
        project: Project name. Omit to use the current workspace's project.
    """
    name = await projects.resolve(ctx, project)
    return await run(store.project_context, name)


@mcp.tool(annotations=READ_ONLY)
async def browse_sessions(
    scope: Scope = "project",
    project: Annotated[str | None, Field(description="Project name.")] = None,
    limit: Annotated[int, Field(ge=1, le=100)] = 10,
    offset: Annotated[int, Field(ge=0)] = 0,
    ctx: Context | None = None,
) -> SessionPage:
    """List recorded sessions, newest first.

    Args:
        scope: "project" lists the current project; "all" lists every project.
        project: Project name. Omit to use the current workspace's project.
        limit: Page size (1-100).
        offset: Number of sessions to skip, for paging.
    """
    name = None if scope == "all" else await projects.resolve(ctx, project)
    return await run(store.browse_sessions, name, limit, offset)


@mcp.tool(annotations=READ_ONLY)
async def list_projects() -> list[ProjectInfo]:
    """List every project Orion knows about, with memory and session counts."""
    return await run(store.list_projects)
