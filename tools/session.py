"""Session memory tools — persistent context across AI assistant sessions."""

import json
import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field, ValidationError

from app import mcp
from orion_config import SESSIONS_FILE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

class SessionEntry(BaseModel):
    """A record of one development session."""

    id: int
    summary: str
    tags: list[str] = Field(default_factory=list)
    decisions_made: list[int] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class MasterSession(BaseModel):
    """Aggregated context across all sessions — the shared brain."""

    current_phase: str = ""
    total_sessions: int = 0
    total_tools: int = 0
    summary: str = ""
    next_steps: str = ""
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class SessionStore(BaseModel):
    """Root structure of sessions.json."""

    master: MasterSession = Field(default_factory=MasterSession)
    history: list[SessionEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

def _load_store() -> SessionStore:
    """Load the session store from disk, creating it if absent."""
    if not SESSIONS_FILE.exists():
        return SessionStore()
    try:
        with open(SESSIONS_FILE) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read sessions file: %s", exc)
        return SessionStore()

    try:
        return SessionStore.model_validate(raw)
    except ValidationError as exc:
        logger.warning("Invalid sessions file, starting fresh: %s", exc)
        return SessionStore()


def _save_store(store: SessionStore) -> None:
    """Persist the session store to disk."""
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(
                store.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )
    except OSError as exc:
        logger.error("Failed to write sessions file: %s", exc)
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
def remember_session(
    summary: str,
    tags: str | None = None,
    decisions_made: str | None = None,
) -> str:
    """Save a development session summary and update the master context.

    Call this at the end of every session. It feeds both the individual
    session history and the shared master brain that recall_session reads.

    Args:
        summary: What was accomplished in this session.
        tags: Optional comma-separated tags (e.g. "graph,phases,refactor").
        decisions_made: Optional comma-separated IDs of decisions created.
    """
    store = _load_store()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    id_list = []
    if decisions_made:
        try:
            id_list = [int(d.strip()) for d in decisions_made.split(",") if d.strip()]
        except ValueError:
            return "decisions_made must be a comma-separated list of numeric IDs."

    entry = SessionEntry(
        id=store.master.total_sessions + 1,
        summary=summary.strip(),
        tags=tag_list,
        decisions_made=id_list,
    )

    store.history.append(entry)

    store.master.total_sessions = len(store.history)
    store.master.summary = summary.strip()
    store.master.updated_at = datetime.now(UTC)

    _save_store(store)

    logger.info("Saved session #%d", entry.id)
    return (
        f"Saved session #{entry.id}\n"
        f"Total sessions: {store.master.total_sessions}"
    )


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def recall_session() -> str:
    """Return the master session context — the shared brain across all sessions.

    Includes current phase, total tools, last session summary, and next steps.
    Use this at the start of every session to restore context without
    re-explaining where you left off.
    """
    store = _load_store()
    master = store.master

    if master.total_sessions == 0:
        return (
            "No sessions recorded yet."
            " Start your first session and call remember_session at the end."
        )

    recent = store.history[-3:] if len(store.history) >= 3 else store.history
    recent_text = "\n".join(
        f"  #{e.id} ({e.created_at.strftime('%Y-%m-%d')}): {e.summary[:120]}"
        for e in recent
    )

    return (
        f"# Master Session Context\n"
        f"\n"
        f"Current phase: {master.current_phase or 'not set'}\n"
        f"Total sessions: {master.total_sessions}\n"
        f"Total tools: {master.total_tools or 'not set'}\n"
        f"\n"
        f"Last session: {master.summary}\n"
        f"\n"
        f"Next steps: {master.next_steps or 'not set'}\n"
        f"\n"
        f"## Recent sessions\n"
        f"{recent_text}\n"
    )


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def browse_sessions(limit: int = 10) -> str:
    """List all recorded development sessions.

    Args:
        limit: Maximum number of sessions to show (default 10).
    """
    store = _load_store()
    if not store.history:
        return "No sessions recorded yet."

    sessions = store.history[-limit:]
    lines = [f"{len(store.history)} session(s) total, showing last {len(sessions)}:\n"]
    for s in sessions:
        tags_str = f" [{', '.join(s.tags)}]" if s.tags else ""
        lines.append(
            f"  #{s.id} | {s.created_at.strftime('%Y-%m-%d %H:%M')}{tags_str}\n"
            f"     {s.summary[:150]}"
        )

    return "\n".join(lines)
