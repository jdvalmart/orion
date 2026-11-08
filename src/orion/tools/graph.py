"""Knowledge-graph tools: typed relationships between decisions."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from orion import projects, store
from orion.app import mcp
from orion.models import Edge, EdgePage, Related, Scope
from orion.tools import READ_ONLY, WRITE, run

Relation = Literal["depends_on", "relates_to", "alternative_to", "supersedes"]


@mcp.tool(annotations=WRITE)
async def link_concepts(
    source_id: int,
    target_id: int,
    relation: Relation,
    description: Annotated[str | None, Field(max_length=1000)] = None,
) -> Edge:
    """Create a directed relationship between two stored decisions.

    Args:
        source_id: ID of the source decision.
        target_id: ID of the target decision.
        relation: depends_on, relates_to, alternative_to or supersedes.
        description: Optional explanation of the relationship.
    """
    return await run(store.link, source_id, target_id, relation, description)


@mcp.tool(annotations=READ_ONLY)
async def find_related(id: int) -> Related:
    """Return every decision directly connected to this one, in both directions.

    Args:
        id: ID of the decision to explore.
    """
    return await run(store.related, id)


@mcp.tool(annotations=READ_ONLY)
async def browse_graph(
    scope: Scope = "project",
    project: Annotated[str | None, Field(description="Project name.")] = None,
    limit: Annotated[int, Field(ge=1, le=200)] = 50,
    offset: Annotated[int, Field(ge=0)] = 0,
    ctx: Context | None = None,
) -> EdgePage:
    """List relationships in the knowledge graph.

    Args:
        scope: "project" lists edges of the current project; "all" lists every edge.
        project: Project name. Omit to use the current workspace's project.
        limit: Page size (1-200).
        offset: Number of edges to skip, for paging.
    """
    name = None if scope == "all" else await projects.resolve(ctx, project)
    return await run(store.browse_edges, name, limit, offset)
