"""Memory tools — persistent context for AI assistants."""

import json
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from orion_config import MEMORY_FILE


def _load_memory() -> list[dict]:
    """Load all memory entries from disk."""
    if not MEMORY_FILE.exists():
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def _save_memory(entries: list[dict]) -> None:
    """Persist memory entries to disk."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def remember_decision(topic: str, decision: str, tags: str = "") -> str:
    """Store a development decision or architectural choice for future reference.

    Args:
        topic: What area this decision belongs to (e.g. "database", "auth", "deploy")
        decision: The decision itself — what was chosen and why
        tags: Optional comma-separated tags for filtering (e.g. "python,fastapi")
    """
    entries = _load_memory()
    entry = {
        "id": len(entries) + 1,
        "topic": topic.strip(),
        "decision": decision.strip(),
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    _save_memory(entries)
    return f"Stored decision #{entry['id']}: {topic}"


def recall_context(query: str, limit: int = 5) -> str:
    """Search past decisions and context by keyword.

    Args:
        query: Keywords to search for in topics, decisions, and tags
        limit: Maximum number of results (default 5)
    """
    entries = _load_memory()
    if not entries:
        return "No memories stored yet."

    query_lower = query.lower()
    query_words = query_lower.split()

    scored = []
    for entry in entries:
        text = f"{entry['topic'].lower()} {entry['decision'].lower()} {' '.join(entry['tags']).lower()}"
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = scored[:limit]

    if not results:
        return f"No memories found matching: {query}"

    lines = []
    for score, entry in results:
        tags_str = f" [{', '.join(entry['tags'])}]" if entry["tags"] else ""
        lines.append(
            f"#{entry['id']} | {entry['topic']}{tags_str}\n"
            f"   {entry['decision']}\n"
        )

    return "\n".join(lines)


def register_memory_tools(mcp: FastMCP) -> None:
    """Register memory tools on the MCP server instance."""
    mcp.tool()(remember_decision)
    mcp.tool()(recall_context)
