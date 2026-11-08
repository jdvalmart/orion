"""Optional semantic search: local ONNX embeddings (fastembed) stored with sqlite-vec.

Installed with ``pip install 'orion[semantic]'``. When the extras are missing
or ``ORION_SEMANTIC=off``, every function here degrades to a no-op and Orion
uses full-text search only.

Vectors are derived data: if a write fails to embed, ``sync`` re-embeds every
memory that lacks a vector on the next search, so the index self-heals instead
of silently drifting like the old ChromaDB index did.
"""

from __future__ import annotations

import importlib.util
import logging
import sqlite3
from functools import lru_cache
from typing import Any

from orion.config import get_settings

logger = logging.getLogger(__name__)


def enabled() -> bool:
    """Whether semantic search is switched on and its dependencies are importable."""
    if get_settings().semantic == "off":
        return False
    return all(importlib.util.find_spec(m) is not None for m in ("sqlite_vec", "fastembed"))


@lru_cache(maxsize=2)
def _model(name: str, cache_dir: str) -> Any:
    from fastembed import TextEmbedding

    logger.info("Loading embedding model %s", name)
    return TextEmbedding(model_name=name, cache_dir=cache_dir)


def embed(texts: list[str]) -> list[list[float]] | None:
    """Embed texts, or return None when semantic search is unavailable or fails."""
    if not texts or not enabled():
        return None
    settings = get_settings()
    try:
        model = _model(settings.embed_model, str(settings.models_dir))
        return [vector.tolist() for vector in model.embed(texts)]
    except Exception as exc:  # noqa: BLE001 — model download/inference can fail many ways; FTS still works
        logger.warning("Embedding failed, falling back to keyword search: %s", exc)
        return None


def memory_text(topic: str, tags: list[str], decision: str) -> str:
    """Text that represents a memory for embedding."""
    return f"{topic}\n{' '.join(tags)}\n{decision}"


def attach(conn: sqlite3.Connection) -> bool:
    """Load sqlite-vec into this connection. Returns False when unavailable."""
    if not enabled():
        return False
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except (AttributeError, sqlite3.Error) as exc:
        logger.warning("Could not load sqlite-vec: %s", exc)
        return False
    return True


def _table_ready(conn: sqlite3.Connection, dim: int) -> None:
    """Create the vector table for the configured model, rebuilding it if the model changed."""
    model = get_settings().embed_model
    conn.execute("CREATE TABLE IF NOT EXISTS semantic_meta (key TEXT PRIMARY KEY, value TEXT)")
    row = conn.execute("SELECT value FROM semantic_meta WHERE key = 'model'").fetchone()
    if row is not None and row[0] != model:
        logger.info("Embedding model changed (%s -> %s); rebuilding vectors", row[0], model)
        conn.execute("DROP TABLE IF EXISTS memory_vectors")
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors USING vec0("
        f"memory_id INTEGER PRIMARY KEY, embedding float[{dim}] distance_metric=cosine)"
    )
    conn.execute("INSERT OR REPLACE INTO semantic_meta (key, value) VALUES ('model', ?)", (model,))


def _has_table(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'memory_vectors'").fetchone()
    return row is not None


def store(conn: sqlite3.Connection, memory_id: int, vector: list[float] | None) -> None:
    """Insert or replace one memory's vector inside the caller's transaction."""
    if vector is None or not attach(conn):
        return
    import sqlite_vec

    try:
        _table_ready(conn, len(vector))
        conn.execute("DELETE FROM memory_vectors WHERE memory_id = ?", (memory_id,))
        conn.execute(
            "INSERT INTO memory_vectors (memory_id, embedding) VALUES (?, ?)",
            (memory_id, sqlite_vec.serialize_float32(vector)),
        )
    except sqlite3.Error as exc:
        logger.warning("Failed to store vector for memory #%d: %s", memory_id, exc)


def remove(conn: sqlite3.Connection, memory_id: int) -> None:
    """Drop a memory's vector (no-op when semantic search is off)."""
    if attach(conn) and _has_table(conn):
        conn.execute("DELETE FROM memory_vectors WHERE memory_id = ?", (memory_id,))


def missing(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Active memories without a vector."""
    if not attach(conn):
        return []
    if not _has_table(conn):
        return conn.execute(
            "SELECT id, topic, decision, tags FROM memories WHERE deleted_at IS NULL"
        ).fetchall()
    return conn.execute(
        "SELECT id, topic, decision, tags FROM memories WHERE deleted_at IS NULL "
        "AND id NOT IN (SELECT memory_id FROM memory_vectors)"
    ).fetchall()


def search(conn: sqlite3.Connection, query: str, k: int) -> list[int] | None:
    """Memory ids ordered by cosine similarity, or None when unavailable."""
    if not attach(conn) or not _has_table(conn):
        return None
    vectors = embed([query])
    if vectors is None:
        return None
    import sqlite_vec

    rows = conn.execute(
        "SELECT memory_id FROM memory_vectors WHERE embedding MATCH ? AND k = ? ORDER BY distance",
        (sqlite_vec.serialize_float32(vectors[0]), k),
    ).fetchall()
    return [row[0] for row in rows]


def status(conn: sqlite3.Connection) -> dict[str, Any]:
    """Semantic index diagnostics for orion_health."""
    if not enabled():
        return {"enabled": False}
    if not attach(conn):
        return {"enabled": False, "error": "sqlite-vec failed to load"}
    indexed = (
        conn.execute("SELECT count(*) FROM memory_vectors").fetchone()[0] if _has_table(conn) else 0
    )
    return {
        "enabled": True,
        "model": get_settings().embed_model,
        "indexed": indexed,
        "missing": len(missing(conn)),
    }
