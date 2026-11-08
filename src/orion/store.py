"""Data access layer: every read and write Orion performs goes through here.

Tools stay thin wrappers around these functions, which keeps the logic
testable without an MCP client (including the multi-process tests).
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

from orion import __version__, semantic
from orion.config import get_settings
from orion.db import RELATION_TYPES, SCHEMA_VERSION, now_iso, reading, writing
from orion.models import (
    Edge,
    EdgePage,
    Health,
    MatchKind,
    Memory,
    MemoryHit,
    MemoryPage,
    MemorySummary,
    ProjectContext,
    ProjectInfo,
    Related,
    RelatedLink,
    SearchResult,
    Session,
    SessionPage,
)

logger = logging.getLogger(__name__)

RRF_K = 60
PROFILE_SECTION_MAX = 20_000

_MEMORY_SELECT = (
    "SELECT m.id, p.name AS project, m.topic, m.decision, m.tags, m.created_at, m.updated_at "
    "FROM memories m JOIN projects p ON p.id = m.project_id"
)
_SESSION_SELECT = (
    "SELECT s.id, p.name AS project, s.summary, s.next_steps, s.tags, s.decisions, s.created_at "
    "FROM sessions s JOIN projects p ON p.id = s.project_id"
)


class NotFoundError(LookupError):
    """A referenced memory, session or section does not exist."""


class InvalidInputError(ValueError):
    """Input is well-typed but semantically invalid."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def clean_tags(tags: list[str] | None) -> list[str]:
    """Lowercase, strip and de-duplicate tags, preserving order."""
    seen: dict[str, None] = {}
    for tag in tags or []:
        normalized = tag.strip().lower()
        if normalized:
            seen.setdefault(normalized, None)
    return list(seen)


def _require_text(value: str, field: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise InvalidInputError(f"{field} must not be empty.")
    return stripped


def _project_id(conn: sqlite3.Connection, name: str, *, create: bool) -> int | None:
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if row is not None:
        return int(row[0])
    if not create:
        return None
    cursor = conn.execute(
        "INSERT INTO projects (name, created_at) VALUES (?, ?)", (name, now_iso())
    )
    return int(cursor.lastrowid or 0)


def _memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        project=row["project"],
        topic=row["topic"],
        decision=row["decision"],
        tags=json.loads(row["tags"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _summary(row: sqlite3.Row) -> MemorySummary:
    return MemorySummary(
        id=row["id"],
        project=row["project"],
        topic=row["topic"],
        tags=json.loads(row["tags"]),
        created_at=row["created_at"],
    )


def _session(row: sqlite3.Row) -> Session:
    return Session(
        id=row["id"],
        project=row["project"],
        summary=row["summary"],
        next_steps=row["next_steps"],
        tags=json.loads(row["tags"]),
        decisions=json.loads(row["decisions"]),
        created_at=row["created_at"],
    )


def _active_memory(conn: sqlite3.Connection, memory_id: int) -> Memory:
    row = conn.execute(
        f"{_MEMORY_SELECT} WHERE m.id = ? AND m.deleted_at IS NULL", (memory_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError(f"Memory #{memory_id} not found.")
    return _memory(row)


STOPWORDS = frozenset(
    [
        "a",
        "al",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "con",
        "de",
        "del",
        "el",
        "en",
        "es",
        "for",
        "from",
        "how",
        "in",
        "is",
        "la",
        "las",
        "lo",
        "los",
        "of",
        "on",
        "or",
        "para",
        "por",
        "que",
        "se",
        "sin",
        "the",
        "to",
        "un",
        "una",
        "what",
        "with",
        "y",
    ]
)


def fts_query(text: str) -> str | None:
    """Turn free text into a safe FTS5 query of OR-ed quoted terms.

    Stopwords (Spanish and English) are dropped, and only words of four or
    more letters match as prefixes: "con*" would otherwise hit "conventions".
    """
    words = [w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS]
    if not words:
        return None
    return " OR ".join(
        f'"{word}"*' if len(word) >= 4 else f'"{word}"' for word in dict.fromkeys(words)
    )


# ---------------------------------------------------------------------------
# Memories
# ---------------------------------------------------------------------------


def add_memory(
    project: str,
    topic: str,
    decision: str,
    tags: list[str] | None = None,
    supersedes: int | None = None,
    path: Path | None = None,
) -> Memory:
    """Store a new memory, optionally marking an older one as superseded."""
    topic = _require_text(topic, "topic")
    decision = _require_text(decision, "decision")
    tag_list = clean_tags(tags)
    # Embed before taking the write lock: inference can take a second or two.
    vectors = semantic.embed([semantic.memory_text(topic, tag_list, decision)])

    with writing(path) as conn:
        if supersedes is not None:
            _active_memory(conn, supersedes)
        project_id = _project_id(conn, project, create=True)
        stamp = now_iso()
        cursor = conn.execute(
            "INSERT INTO memories (project_id, topic, decision, tags, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, topic, decision, json.dumps(tag_list, ensure_ascii=False), stamp, stamp),
        )
        memory_id = int(cursor.lastrowid or 0)
        if supersedes is not None:
            conn.execute(
                "INSERT INTO edges (source_id, target_id, relation, created_at) "
                "VALUES (?, ?, 'supersedes', ?)",
                (memory_id, supersedes, stamp),
            )
        semantic.store(conn, memory_id, vectors[0] if vectors else None)
        memory = _active_memory(conn, memory_id)

    logger.info("Stored memory #%d in %s: %s", memory.id, project, topic)
    return memory


def update_memory(
    memory_id: int,
    topic: str | None = None,
    decision: str | None = None,
    tags: list[str] | None = None,
    project: str | None = None,
    path: Path | None = None,
) -> Memory:
    """Change only the provided fields of an active memory."""
    if topic is None and decision is None and tags is None and project is None:
        raise InvalidInputError("Provide at least one field to change.")

    with writing(path) as conn:
        current = _active_memory(conn, memory_id)
        project_id = _project_id(conn, project or current.project, create=True)
        conn.execute(
            "UPDATE memories SET project_id = ?, topic = ?, decision = ?, tags = ?, updated_at = ? "
            "WHERE id = ?",
            (
                project_id,
                _require_text(topic, "topic") if topic is not None else current.topic,
                _require_text(decision, "decision") if decision is not None else current.decision,
                json.dumps(clean_tags(tags) if tags is not None else current.tags),
                now_iso(),
                memory_id,
            ),
        )
        memory = _active_memory(conn, memory_id)

    vectors = semantic.embed([semantic.memory_text(memory.topic, memory.tags, memory.decision)])
    if vectors:
        with writing(path) as conn:
            semantic.store(conn, memory_id, vectors[0])
    logger.info("Revised memory #%d", memory_id)
    return memory


def delete_memory(memory_id: int, path: Path | None = None) -> Memory:
    """Soft-delete a memory and drop every graph edge that touches it."""
    with writing(path) as conn:
        memory = _active_memory(conn, memory_id)
        conn.execute("UPDATE memories SET deleted_at = ? WHERE id = ?", (now_iso(), memory_id))
        conn.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?", (memory_id, memory_id)
        )
        semantic.remove(conn, memory_id)
    logger.info("Forgot memory #%d", memory_id)
    return memory


def browse_memories(
    project: str | None,
    tag: str | None = None,
    limit: int = 20,
    offset: int = 0,
    path: Path | None = None,
) -> MemoryPage:
    """List active memories, newest first. ``project=None`` lists every project."""
    where = ["m.deleted_at IS NULL"]
    params: list[Any] = []
    if project is not None:
        where.append("p.name = ?")
        params.append(project)
    if tag:
        where.append("EXISTS (SELECT 1 FROM json_each(m.tags) WHERE json_each.value = ?)")
        params.append(tag.strip().lower())
    clause = " WHERE " + " AND ".join(where)

    with reading(path) as conn:
        total = conn.execute(
            "SELECT count(*) FROM memories m JOIN projects p ON p.id = m.project_id" + clause,
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"{_MEMORY_SELECT}{clause} ORDER BY m.id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
    return MemoryPage(
        project=project, total=total, offset=offset, items=[_summary(r) for r in rows]
    )


def sync_vectors(path: Path | None = None) -> int:
    """Embed every active memory that has no vector yet. Returns how many were added."""
    if not semantic.enabled():
        return 0
    with reading(path) as conn:
        rows = semantic.missing(conn)
    if not rows:
        return 0
    texts = [semantic.memory_text(r["topic"], json.loads(r["tags"]), r["decision"]) for r in rows]
    vectors = semantic.embed(texts)
    if vectors is None:
        return 0
    with writing(path) as conn:
        for row, vector in zip(rows, vectors, strict=True):
            semantic.store(conn, row["id"], vector)
    logger.info("Indexed %d memories for semantic search", len(rows))
    return len(rows)


def search_memories(
    query: str,
    project: str | None,
    limit: int = 5,
    path: Path | None = None,
) -> SearchResult:
    """Hybrid search: FTS5/BM25 keywords fused with vector similarity when available.

    Rankings are merged with reciprocal rank fusion (RRF), which needs no score
    calibration between BM25 and cosine distance.
    """
    query = _require_text(query, "query")
    match = fts_query(query)
    use_semantic = semantic.enabled()
    if match is None and not use_semantic:
        raise InvalidInputError("Query must contain at least one word.")
    if use_semantic:
        sync_vectors(path)

    candidates = max(limit * 4, 20)
    project_filter = "" if project is None else " AND p.name = ?"
    project_params: list[Any] = [] if project is None else [project]

    with reading(path) as conn:
        keyword_ids: list[int] = []
        if match is not None:
            keyword_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT m.id FROM memories_fts f "
                    "JOIN memories m ON m.id = f.rowid JOIN projects p ON p.id = m.project_id "
                    f"WHERE memories_fts MATCH ? AND m.deleted_at IS NULL{project_filter} "
                    "ORDER BY bm25(memories_fts, 3.0, 1.0, 2.0) LIMIT ?",
                    [match, *project_params, candidates],
                )
            ]

        semantic_ids: list[int] = []
        vector_ids = semantic.search(conn, query, k=200) if use_semantic else None
        if vector_ids:
            allowed = {
                row[0]
                for row in conn.execute(
                    "SELECT m.id FROM memories m JOIN projects p ON p.id = m.project_id "
                    f"WHERE m.deleted_at IS NULL{project_filter}",
                    project_params,
                )
            }
            semantic_ids = [i for i in vector_ids if i in allowed][:candidates]

        scores: dict[int, float] = {}
        in_keyword = set(keyword_ids)
        in_semantic = set(semantic_ids)
        for ranked in (keyword_ids, semantic_ids):
            for rank, memory_id in enumerate(ranked, start=1):
                scores[memory_id] = scores.get(memory_id, 0.0) + 1.0 / (RRF_K + rank)

        best = sorted(scores, key=lambda i: scores[i], reverse=True)[:limit]
        hits: list[MemoryHit] = []
        for memory_id in best:
            kind: MatchKind
            if memory_id in in_keyword and memory_id in in_semantic:
                kind = "both"
            elif memory_id in in_keyword:
                kind = "keyword"
            else:
                kind = "semantic"
            memory = _active_memory(conn, memory_id)
            hits.append(
                MemoryHit(**memory.model_dump(), score=round(scores[memory_id], 5), match=kind)
            )

    return SearchResult(
        query=query,
        project=project,
        mode="hybrid" if vector_ids is not None else "keyword",
        results=hits,
    )


# ---------------------------------------------------------------------------
# Knowledge graph
# ---------------------------------------------------------------------------


def link(
    source_id: int,
    target_id: int,
    relation: str,
    description: str | None = None,
    path: Path | None = None,
) -> Edge:
    """Create a directed relationship between two active memories."""
    if relation not in RELATION_TYPES:
        raise InvalidInputError(
            f"Invalid relation '{relation}'. Valid: {', '.join(RELATION_TYPES)}."
        )
    if source_id == target_id:
        raise InvalidInputError("Cannot link a memory to itself.")
    note = description.strip() if description and description.strip() else None

    with writing(path) as conn:
        _active_memory(conn, source_id)
        _active_memory(conn, target_id)
        stamp = now_iso()
        try:
            conn.execute(
                "INSERT INTO edges (source_id, target_id, relation, description, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (source_id, target_id, relation, note, stamp),
            )
        except sqlite3.IntegrityError as exc:
            raise InvalidInputError(f"#{source_id} is already {relation} #{target_id}.") from exc
    logger.info("Linked #%d --%s--> #%d", source_id, relation, target_id)
    return Edge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        description=note,
        created_at=stamp,
    )


def related(memory_id: int, path: Path | None = None) -> Related:
    """Direct neighbours of a memory in both directions."""
    with reading(path) as conn:
        memory = _active_memory(conn, memory_id)
        rows = conn.execute(
            "SELECT e.target_id AS other, 'outgoing' AS direction, e.relation, e.description, "
            "m.topic FROM edges e JOIN memories m ON m.id = e.target_id WHERE e.source_id = ? "
            "UNION ALL "
            "SELECT e.source_id, 'incoming', e.relation, e.description, m.topic "
            "FROM edges e JOIN memories m ON m.id = e.source_id WHERE e.target_id = ?",
            (memory_id, memory_id),
        ).fetchall()
    return Related(
        id=memory.id,
        topic=memory.topic,
        links=[
            RelatedLink(
                id=r["other"],
                topic=r["topic"],
                relation=r["relation"],
                direction=r["direction"],
                description=r["description"],
            )
            for r in rows
        ],
    )


def browse_edges(
    project: str | None, limit: int = 50, offset: int = 0, path: Path | None = None
) -> EdgePage:
    """List graph edges; with a project, only edges whose source belongs to it."""
    join = (
        "FROM edges e JOIN memories m ON m.id = e.source_id JOIN projects p ON p.id = m.project_id"
    )
    clause = "" if project is None else " WHERE p.name = ?"
    params: list[Any] = [] if project is None else [project]
    with reading(path) as conn:
        total = conn.execute(f"SELECT count(*) {join}{clause}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT e.* {join}{clause} ORDER BY e.created_at DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
    return EdgePage(
        project=project,
        total=total,
        offset=offset,
        items=[Edge(**dict(r)) for r in rows],
    )


# ---------------------------------------------------------------------------
# Sessions and project state
# ---------------------------------------------------------------------------


def add_session(
    project: str,
    summary: str,
    tags: list[str] | None = None,
    decisions: list[int] | None = None,
    next_steps: str | None = None,
    phase: str | None = None,
    path: Path | None = None,
) -> Session:
    """Record a work session and update the project's phase and next steps."""
    summary = _require_text(summary, "summary")
    steps = next_steps.strip() if next_steps and next_steps.strip() else None
    decision_ids = list(dict.fromkeys(decisions or []))

    with writing(path) as conn:
        for decision_id in decision_ids:
            _active_memory(conn, decision_id)
        project_id = _project_id(conn, project, create=True)
        stamp = now_iso()
        cursor = conn.execute(
            "INSERT INTO sessions (project_id, summary, next_steps, tags, decisions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                project_id,
                summary,
                steps,
                json.dumps(clean_tags(tags), ensure_ascii=False),
                json.dumps(decision_ids),
                stamp,
            ),
        )
        new_phase = phase.strip() if phase and phase.strip() else None
        conn.execute(
            "INSERT INTO project_state (project_id, phase, next_steps, updated_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT (project_id) DO UPDATE SET "
            "phase = coalesce(excluded.phase, phase), "
            "next_steps = coalesce(excluded.next_steps, next_steps), "
            "updated_at = excluded.updated_at",
            (project_id, new_phase, steps, stamp),
        )
        row = conn.execute(f"{_SESSION_SELECT} WHERE s.id = ?", (cursor.lastrowid,)).fetchone()
    logger.info("Saved session #%d for %s", row["id"], project)
    return _session(row)


def project_context(
    project: str, sessions: int = 3, decisions: int = 5, path: Path | None = None
) -> ProjectContext:
    """Phase, next steps, recent sessions and recent decisions of one project."""
    with reading(path) as conn:
        project_id = _project_id(conn, project, create=False)
        if project_id is None:
            return ProjectContext(
                project=project,
                phase=None,
                next_steps=None,
                total_sessions=0,
                total_memories=0,
                recent_sessions=[],
                recent_decisions=[],
            )
        state = conn.execute(
            "SELECT phase, next_steps FROM project_state WHERE project_id = ?", (project_id,)
        ).fetchone()
        total_sessions = conn.execute(
            "SELECT count(*) FROM sessions WHERE project_id = ?", (project_id,)
        ).fetchone()[0]
        total_memories = conn.execute(
            "SELECT count(*) FROM memories WHERE project_id = ? AND deleted_at IS NULL",
            (project_id,),
        ).fetchone()[0]
        recent_sessions = conn.execute(
            f"{_SESSION_SELECT} WHERE s.project_id = ? ORDER BY s.id DESC LIMIT ?",
            (project_id, sessions),
        ).fetchall()
        recent_decisions = conn.execute(
            f"{_MEMORY_SELECT} WHERE m.project_id = ? AND m.deleted_at IS NULL "
            "ORDER BY m.id DESC LIMIT ?",
            (project_id, decisions),
        ).fetchall()
    return ProjectContext(
        project=project,
        phase=state["phase"] if state else None,
        next_steps=state["next_steps"] if state else None,
        total_sessions=total_sessions,
        total_memories=total_memories,
        recent_sessions=[_session(r) for r in recent_sessions],
        recent_decisions=[_summary(r) for r in recent_decisions],
    )


def browse_sessions(
    project: str | None, limit: int = 10, offset: int = 0, path: Path | None = None
) -> SessionPage:
    """List sessions newest first. ``project=None`` lists every project."""
    clause = "" if project is None else " WHERE p.name = ?"
    params: list[Any] = [] if project is None else [project]
    with reading(path) as conn:
        total = conn.execute(
            f"SELECT count(*) FROM sessions s JOIN projects p ON p.id = s.project_id{clause}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"{_SESSION_SELECT}{clause} ORDER BY s.id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
    return SessionPage(
        project=project, total=total, offset=offset, items=[_session(r) for r in rows]
    )


def list_projects(path: Path | None = None) -> list[ProjectInfo]:
    """Every known project with its counts."""
    with reading(path) as conn:
        rows = conn.execute(
            "SELECT p.name, "
            "(SELECT count(*) FROM memories m WHERE m.project_id = p.id "
            " AND m.deleted_at IS NULL) AS memories, "
            "(SELECT count(*) FROM sessions s WHERE s.project_id = p.id) AS sessions, "
            "st.phase FROM projects p LEFT JOIN project_state st ON st.project_id = p.id "
            "ORDER BY p.name"
        ).fetchall()
    return [
        ProjectInfo(
            name=r["name"], memories=r["memories"], sessions=r["sessions"], phase=r["phase"]
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def get_profile(path: Path | None = None) -> dict[str, Any]:
    """The whole developer profile, keyed by section."""
    with reading(path) as conn:
        rows = conn.execute("SELECT section, value FROM profile ORDER BY section").fetchall()
    return {r["section"]: json.loads(r["value"]) for r in rows}


def set_profile_section(section: str, value: Any, path: Path | None = None) -> dict[str, Any]:
    """Replace one profile section; ``value=None`` removes it. Returns the full profile.

    Each section is capped at PROFILE_SECTION_MAX characters of JSON: whoami
    returns the whole profile, so an unbounded section would flood the
    assistant's context on every call.
    """
    section = _require_text(section, "section").lower()
    serialized = json.dumps(value, ensure_ascii=False)
    if value is not None and len(serialized) > PROFILE_SECTION_MAX:
        raise InvalidInputError(
            f"Profile section too large ({len(serialized)} chars, max {PROFILE_SECTION_MAX})."
        )
    with writing(path) as conn:
        if value is None:
            deleted = conn.execute("DELETE FROM profile WHERE section = ?", (section,)).rowcount
            if not deleted:
                raise NotFoundError(f"Profile section '{section}' not found.")
        else:
            conn.execute(
                "INSERT INTO profile (section, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT (section) DO UPDATE SET value = excluded.value, "
                "updated_at = excluded.updated_at",
                (section, serialized, now_iso()),
            )
    return get_profile(path)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def health(path: Path | None = None) -> Health:
    """Counts, integrity and semantic-index status."""
    settings = get_settings()
    db_path = path or settings.db_path
    with reading(db_path) as conn:

        def count(sql: str) -> int:
            return int(conn.execute(sql).fetchone()[0])

        return Health(
            version=__version__,
            data_dir=str(db_path.parent),
            db_path=str(db_path),
            schema_version=SCHEMA_VERSION,
            integrity=conn.execute("PRAGMA quick_check").fetchone()[0],
            projects=count("SELECT count(*) FROM projects"),
            memories=count("SELECT count(*) FROM memories WHERE deleted_at IS NULL"),
            deleted_memories=count("SELECT count(*) FROM memories WHERE deleted_at IS NOT NULL"),
            edges=count("SELECT count(*) FROM edges"),
            sessions=count("SELECT count(*) FROM sessions"),
            semantic=semantic.status(conn),
            s3_configured=settings.s3_bucket is not None,
        )
