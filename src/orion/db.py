"""SQLite storage: connection handling, transactions and schema migrations.

Why SQLite instead of JSON files + ChromaDB:
- Several MCP clients (OpenCode, Claude Desktop, Claude Code) run their own
  Orion process against the same data. WAL mode plus ``BEGIN IMMEDIATE``
  serialises writers across processes, so no update is silently lost.
- Writes are atomic: a crash mid-write can no longer truncate the store.
- ``AUTOINCREMENT`` ids are never reused, even after deletions.
- The full-text index (FTS5) lives in the same file and is kept in sync by
  triggers inside the same transaction, so it cannot drift.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from orion.config import get_settings

logger = logging.getLogger(__name__)

RELATION_TYPES = ("depends_on", "relates_to", "alternative_to", "supersedes")

_RELATIONS_SQL = ", ".join(f"'{r}'" for r in RELATION_TYPES)

# Each migration is a list of single statements so it can run inside one
# explicit transaction (``executescript`` would commit implicitly).
MIGRATIONS: list[list[str]] = [
    [
        """
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            topic TEXT NOT NULL CHECK (length(trim(topic)) > 0),
            decision TEXT NOT NULL CHECK (length(trim(decision)) > 0),
            tags TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        )
        """,
        "CREATE INDEX memories_by_project ON memories (project_id, deleted_at, id)",
        """
        CREATE VIRTUAL TABLE memories_fts USING fts5 (
            topic, decision, tags,
            content='memories', content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        )
        """,
        """
        CREATE TRIGGER memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts (rowid, topic, decision, tags)
            VALUES (new.id, new.topic, new.decision, new.tags);
        END
        """,
        """
        CREATE TRIGGER memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts (memories_fts, rowid, topic, decision, tags)
            VALUES ('delete', old.id, old.topic, old.decision, old.tags);
        END
        """,
        """
        CREATE TRIGGER memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts (memories_fts, rowid, topic, decision, tags)
            VALUES ('delete', old.id, old.topic, old.decision, old.tags);
            INSERT INTO memories_fts (rowid, topic, decision, tags)
            VALUES (new.id, new.topic, new.decision, new.tags);
        END
        """,
        f"""
        CREATE TABLE edges (
            source_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
            relation TEXT NOT NULL CHECK (relation IN ({_RELATIONS_SQL})),
            description TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY (source_id, target_id, relation),
            CHECK (source_id <> target_id)
        )
        """,
        "CREATE INDEX edges_by_target ON edges (target_id)",
        """
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            summary TEXT NOT NULL CHECK (length(trim(summary)) > 0),
            next_steps TEXT,
            tags TEXT NOT NULL DEFAULT '[]',
            decisions TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX sessions_by_project ON sessions (project_id, id)",
        """
        CREATE TABLE project_state (
            project_id INTEGER PRIMARY KEY REFERENCES projects(id),
            phase TEXT,
            next_steps TEXT,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE profile (
            section TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
    ],
]

SCHEMA_VERSION = len(MIGRATIONS)


def now_iso() -> str:
    """Current UTC time as an ISO-8601 string (the format stored in every table)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _open(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")
    if conn.execute("PRAGMA journal_mode = WAL").fetchone()[0].lower() != "wal":
        logger.warning("SQLite WAL mode unavailable for %s", path)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] >= SCHEMA_VERSION:
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Re-read inside the lock: another process may have migrated meanwhile.
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        for index in range(version, SCHEMA_VERSION):
            for statement in MIGRATIONS[index]:
                conn.execute(statement)
            conn.execute(f"PRAGMA user_version = {index + 1}")
            logger.info("Applied schema migration %d", index + 1)
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open the Orion database, applying pending migrations."""
    conn = _open(path or get_settings().db_path)
    try:
        _migrate(conn)
    except BaseException:
        conn.close()
        raise
    return conn


@contextmanager
def reading(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Connection for read-only work (WAL readers never block writers)."""
    conn = connect(path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def writing(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Connection holding the write lock for the whole block, committed on success."""
    conn = connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")
    finally:
        conn.close()
