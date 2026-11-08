"""Memory tools: store, search, revise, forget and browse decisions."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from orion import projects, store
from orion.app import mcp
from orion.models import Memory, MemoryPage, Scope, SearchResult
from orion.tools import DESTRUCTIVE, READ_ONLY, WRITE, run, split_tags

Tags = Annotated[
    list[str] | str | None,
    Field(description="Tags for filtering, e.g. ['python', 'fastapi']."),
]
ProjectArg = Annotated[
    str | None,
    Field(description="Project name. Omit to use the current workspace's project."),
]


@mcp.tool(annotations=WRITE)
async def remember_decision(
    topic: Annotated[str, Field(min_length=1, max_length=200)],
    decision: Annotated[str, Field(min_length=1, max_length=20_000)],
    tags: Tags = None,
    project: ProjectArg = None,
    supersedes: int | None = None,
    ctx: Context | None = None,
) -> Memory:
    """Store a development decision or architectural choice for future sessions.

    Args:
        topic: Short area label, e.g. "database", "auth", "payments-wompi".
        decision: What was decided and why, including rejected alternatives.
        tags: Optional tags for filtering.
        project: Project name. Omit to use the current workspace's project.
        supersedes: ID of an older decision this one replaces; links them in the graph.
    """
    name = await projects.resolve(ctx, project)
    return await run(store.add_memory, name, topic, decision, split_tags(tags), supersedes)


@mcp.tool(annotations=READ_ONLY)
async def recall_context(
    query: Annotated[str, Field(min_length=1, max_length=500)],
    limit: Annotated[int, Field(ge=1, le=50)] = 5,
    scope: Scope = "project",
    project: ProjectArg = None,
    ctx: Context | None = None,
) -> SearchResult:
    """Search past decisions by keywords and, when enabled, semantic similarity.

    Args:
        query: Keywords, a phrase or a question.
        limit: Maximum number of results (1-50).
        scope: "project" searches the current project only; "all" searches every project.
        project: Project name. Omit to use the current workspace's project.
    """
    name = None if scope == "all" else await projects.resolve(ctx, project)
    return await run(store.search_memories, query, name, limit)


@mcp.tool(annotations=WRITE)
async def revise_decision(
    id: int,
    topic: Annotated[str | None, Field(max_length=200)] = None,
    decision: Annotated[str | None, Field(max_length=20_000)] = None,
    tags: Tags = None,
    project: Annotated[str | None, Field(description="Move the decision to this project.")] = None,
) -> Memory:
    """Update an existing decision. Only the provided fields change.

    Args:
        id: ID of the decision to update.
        topic: New topic.
        decision: New decision text.
        tags: New tags (replaces the current list).
        project: Move the decision to this project.
    """
    name = projects.normalize(project) if project else None
    return await run(store.update_memory, id, topic, decision, split_tags(tags), name)


@mcp.tool(annotations=DESTRUCTIVE)
async def forget_decision(id: int) -> Memory:
    """Delete a decision and every graph relationship that touches it.

    Args:
        id: ID of the decision to delete.
    """
    return await run(store.delete_memory, id)


@mcp.tool(annotations=READ_ONLY)
async def browse_memories(
    scope: Scope = "project",
    project: ProjectArg = None,
    tag: str | None = None,
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
    offset: Annotated[int, Field(ge=0)] = 0,
    ctx: Context | None = None,
) -> MemoryPage:
    """List stored decisions (newest first) without their full text.

    Args:
        scope: "project" lists the current project; "all" lists every project.
        project: Project name. Omit to use the current workspace's project.
        tag: Only decisions with this tag.
        limit: Page size (1-100).
        offset: Number of entries to skip, for paging.
    """
    name = None if scope == "all" else await projects.resolve(ctx, project)
    return await run(store.browse_memories, name, tag, limit, offset)
