"""Knowledge graph tools — link concepts and explore relationships."""

import json
import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field, ValidationError

from app import mcp
from orion_config import GRAPH_FILE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

RELATION_TYPES = {"depends_on", "relates_to", "alternative_to", "supersedes"}


class GraphEdge(BaseModel):
    """A directed relationship between two decisions."""

    source_id: int
    target_id: int
    relation: str
    description: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

def _load_edges() -> list[GraphEdge]:
    """Load all graph edges from disk."""
    if not GRAPH_FILE.exists():
        return []
    try:
        with open(GRAPH_FILE) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read graph file: %s", exc)
        return []

    edges = []
    for item in raw:
        try:
            edges.append(GraphEdge.model_validate(item))
        except ValidationError as exc:
            logger.warning("Skipping invalid graph edge: %s", exc)
    return edges


def _save_edges(edges: list[GraphEdge]) -> None:
    """Persist graph edges to disk."""
    try:
        with open(GRAPH_FILE, "w") as f:
            json.dump(
                [edge.model_dump(mode="json") for edge in edges],
                f,
                indent=2,
                ensure_ascii=False,
            )
    except OSError as exc:
        logger.error("Failed to write graph file: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)
def link_concepts(
    source_id: int,
    target_id: int,
    relation: str,
    description: str | None = None,
) -> str:
    """Create a relationship between two stored decisions.

    Use this to express that one concept depends on, relates to, is an
    alternative to, or supersedes another.

    Args:
        source_id: The ID of the source decision (from).
        target_id: The ID of the target decision (to).
        relation: One of: depends_on, relates_to, alternative_to, supersedes.
        description: Optional explanation of the relationship.
    """
    if relation not in RELATION_TYPES:
        types = ", ".join(sorted(RELATION_TYPES))
        return f"Invalid relation type: {relation}\nValid types: {types}"

    if source_id == target_id:
        return "Cannot link a decision to itself."

    edges = _load_edges()

    for edge in edges:
        if (
            edge.source_id == source_id
            and edge.target_id == target_id
            and edge.relation == relation
        ):
            return f"#{source_id} is already {relation} #{target_id}."

    edge = GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        description=description.strip() if description else None,
    )
    edges.append(edge)
    _save_edges(edges)

    desc = f": {description}" if description else ""
    logger.info("Linked #%d --%s--> #%d%s", source_id, relation, target_id, desc)
    return f"Linked #{source_id} --{relation}--> #{target_id}{desc}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def find_related(id: int) -> str:
    """Return all decisions directly connected to this one.

    Args:
        id: The numeric ID of the decision to explore.
    """
    edges = _load_edges()
    incoming = [e for e in edges if e.target_id == id]
    outgoing = [e for e in edges if e.source_id == id]

    if not incoming and not outgoing:
        return f"No relationships found for decision #{id}."

    lines = []

    if outgoing:
        lines.append(f"#{id} points to:")
        for e in outgoing:
            desc = f" — {e.description}" if e.description else ""
            lines.append(f"  --{e.relation}--> #{e.target_id}{desc}")

    if incoming:
        lines.append(f"\n#{id} is referenced by:")
        for e in incoming:
            desc = f" — {e.description}" if e.description else ""
            lines.append(f"  #{e.source_id} --{e.relation}--> {desc}".rstrip())

    return "\n".join(lines)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def browse_graph() -> str:
    """List all relationships in the knowledge graph."""
    edges = _load_edges()
    if not edges:
        return "No relationships defined yet. Use link_concepts to create some."

    lines = [f"{len(edges)} relationship(s):\n"]
    for e in edges:
        desc = f" — {e.description}" if e.description else ""
        lines.append(f"  #{e.source_id} --{e.relation}--> #{e.target_id}{desc}")

    return "\n".join(lines)
