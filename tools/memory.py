"""Memory tools — persistent context for AI assistants."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from app import mcp
from orion_config import MEMORY_FILE

logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    """A single development decision or architectural choice."""

    id: int
    topic: str
    decision: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _load_entries() -> list[MemoryEntry]:
    """Load all memory entries from disk, validating against the model."""
    if not MEMORY_FILE.exists():
        logger.debug("Memory file not found, returning empty list")
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read memory file: %s", exc)
        return []

    entries = []
    for item in raw:
        try:
            entries.append(MemoryEntry.model_validate(item))
        except ValidationError as exc:
            logger.warning("Skipping invalid memory entry: %s", exc)
    return entries


def _save_entries(entries: list[MemoryEntry]) -> None:
    """Persist memory entries to disk."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(
                [entry.model_dump(mode="json") for entry in entries],
                f,
                indent=2,
                ensure_ascii=False,
            )
    except OSError as exc:
        logger.error("Failed to write memory file: %s", exc)
        raise


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)
def remember_decision(
    topic: str,
    decision: str,
    tags: Optional[str] = None,
) -> str:
    """Store a development decision or architectural choice for future reference.

    Args:
        topic: What area this decision belongs to (e.g. "database", "auth", "deploy").
        decision: The decision itself — what was chosen and why.
        tags: Optional comma-separated tags for filtering (e.g. "python,fastapi").
    """
    entries = _load_entries()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    entry = MemoryEntry(
        id=len(entries) + 1,
        topic=topic.strip(),
        decision=decision.strip(),
        tags=tag_list,
    )

    entries.append(entry)
    _save_entries(entries)

    logger.info("Stored decision #%d: %s", entry.id, topic)
    return f"Stored decision #{entry.id}: {topic}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def recall_context(query: str, limit: int = 5) -> str:
    """Search past decisions and context by keyword.

    Args:
        query: Keywords to search for in topics, decisions, and tags.
        limit: Maximum number of results to return (default 5).
    """
    entries = _load_entries()
    if not entries:
        return "No memories stored yet."

    query_lower = query.lower()
    query_words = query_lower.split()

    scored: list[tuple[int, MemoryEntry]] = []
    for entry in entries:
        text = (
            f"{entry.topic.lower()} "
            f"{entry.decision.lower()} "
            f"{' '.join(entry.tags).lower()}"
        )
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = scored[:limit]

    if not results:
        return f"No memories found matching: {query}"

    lines: list[str] = []
    for score, entry in results:
        tags_str = f" [{', '.join(entry.tags)}]" if entry.tags else ""
        lines.append(
            f"#{entry.id} | {entry.topic}{tags_str}\n"
            f"   {entry.decision}\n"
        )

    return "\n".join(lines)
