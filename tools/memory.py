"""Memory tools — persistent context for AI assistants."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field, ValidationError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def _entry_text(entry: MemoryEntry) -> str:
    return f"{entry.topic} {' '.join(entry.tags)} {entry.decision}"


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


def _format_entry(entry: MemoryEntry, score: Optional[float] = None) -> str:
    tags_str = f" [{', '.join(entry.tags)}]" if entry.tags else ""
    prefix = f"#{entry.id} | {entry.topic}{tags_str}"
    if score is not None:
        prefix = f"#{entry.id} [{score:.2f}] | {entry.topic}{tags_str}"
    return f"{prefix}\n   {entry.decision}\n"


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
    """Search past decisions using TF-IDF semantic ranking.

    Ranks entries by cosine similarity between the query and the full
    text of each memory (topic + tags + decision).

    Args:
        query: Search query. Can be a keyword, phrase, or question.
        limit: Maximum number of results to return (default 5).
    """
    entries = _load_entries()
    if not entries:
        return "No memories stored yet."

    corpus = [_entry_text(e) for e in entries]
    vectorizer = TfidfVectorizer(stop_words=None, lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    query_vec = vectorizer.transform([query])

    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

    scored = [(float(similarities[i]), entries[i]) for i in np.argsort(-similarities)]
    results = [(s, e) for s, e in scored if s > 0][:limit]

    if not results:
        return f"No memories found matching: {query}"

    return "\n".join(_format_entry(e, s) for s, e in results)


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)
def revise_decision(
    id: int,
    topic: Optional[str] = None,
    decision: Optional[str] = None,
    tags: Optional[str] = None,
) -> str:
    """Update an existing decision. Only provided fields are changed.

    Args:
        id: The numeric ID of the decision to update.
        topic: New topic for this decision (leave empty to keep current).
        decision: New decision text (leave empty to keep current).
        tags: New comma-separated tags (leave empty to keep current).
    """
    entries = _load_entries()

    for entry in entries:
        if entry.id == id:
            if topic is not None:
                entry.topic = topic.strip()
            if decision is not None:
                entry.decision = decision.strip()
            if tags is not None:
                entry.tags = [t.strip() for t in tags.split(",") if t.strip()]

            _save_entries(entries)
            logger.info("Revised decision #%d", id)
            return f"Revised decision #{id}: {entry.topic}"

    return f"Decision #{id} not found. Use browse_memories to see all entries."


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
    },
)
def forget_decision(id: int) -> str:
    """Permanently delete a decision by its ID.

    Args:
        id: The numeric ID of the decision to delete.
    """
    entries = _load_entries()

    for i, entry in enumerate(entries):
        if entry.id == id:
            topic = entry.topic
            entries.pop(i)
            _save_entries(entries)
            logger.info("Forgot decision #%d: %s", id, topic)
            return f"Forgot decision #{id}: {topic}"

    return f"Decision #{id} not found. Use browse_memories to see all entries."


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def browse_memories() -> str:
    """List all stored decisions with their IDs, topics, and tags.

    Use this to see what's in memory before revising or forgetting.
    """
    entries = _load_entries()
    if not entries:
        return "No memories stored yet."

    lines = [f"{len(entries)} memories stored:\n"]
    for entry in entries:
        tags_str = f" [{', '.join(entry.tags)}]" if entry.tags else ""
        lines.append(f"  #{entry.id} | {entry.topic}{tags_str}")

    return "\n".join(lines)
