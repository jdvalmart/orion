"""Import the legacy JSON store (memory, graph, sessions, whoami) into orion.db.

- Keeps original IDs so existing references (graph edges, session
  ``decisions_made``) stay valid.
- Skips everything listed in ``quarantine.json`` (see clean_test_data.py).
- Drops graph edges whose endpoints do not exist.
- Assigns each memory and session to a project, inferred from its tags or text.
- Idempotent: rows that already exist are left untouched.

Usage:
    python scripts/migrate_json_to_sqlite.py --source data --dry-run
    python scripts/migrate_json_to_sqlite.py --source data [--db PATH]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from orion.db import connect, now_iso
from orion.projects import DEFAULT_PROJECT, normalize
from orion.store import clean_tags

logger = logging.getLogger("migrate")

PROJECT_ROOTS = [Path.home() / "Proyectos", Path.home() / "Proyectos" / "universo"]


def known_projects() -> list[str]:
    """Folder names under the usual workspace roots, longest first.

    Names shorter than four characters (e.g. "ai") are ignored: they match
    ordinary words in summaries far too often.
    """
    names = {
        normalize(p.name)
        for root in PROJECT_ROOTS
        if root.is_dir()
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and len(p.name) >= 4
    }
    return sorted(names, key=len, reverse=True)


def infer_project(tags: list[str], text: str, known: list[str]) -> str:
    """First known project found in the tags, then in the text; otherwise 'general'."""
    normalized_tags = {t.lower() for t in tags}
    for name in known:
        if name in normalized_tags:
            return name
    lowered = text.lower()
    for name in known:
        if re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", lowered):
            return name
    return DEFAULT_PROJECT


def _load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _project_id(conn: sqlite3.Connection, name: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO projects (name, created_at) VALUES (?, ?)", (name, now_iso())
    )
    return int(conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()[0])


def migrate(source: Path, db_path: Path | None, dry_run: bool) -> dict[str, Any]:
    """Run the import and return a report."""
    quarantine = _load(source / "quarantine.json", {})
    skip_memories = set(quarantine.get("memories", {}).get("quarantined_ids", []))
    skip_sessions = set(quarantine.get("sessions", {}).get("quarantined_ids", []))
    if not quarantine:
        logger.warning("No quarantine.json found: test data will be imported too.")

    known = known_projects()
    memories = [m for m in _load(source / "memory.json", []) if m["id"] not in skip_memories]
    sessions_store = _load(source / "sessions.json", {})
    sessions = [s for s in sessions_store.get("history", []) if s["id"] not in skip_sessions]
    memory_ids = {m["id"] for m in memories}
    edges = _load(source / "graph.json", [])
    valid_edges = [
        e
        for e in edges
        if e["source_id"] in memory_ids
        and e["target_id"] in memory_ids
        and e["source_id"] != e["target_id"]
    ]
    profile = _load(source / "whoami.json", {})

    memory_projects = {
        m["id"]: infer_project(m.get("tags", []), f"{m['topic']} {m['decision']}", known)
        for m in memories
    }
    session_projects = {
        s["id"]: infer_project(s.get("tags", []), s["summary"], known) for s in sessions
    }
    report = {
        "memories": len(memories),
        "memories_skipped": len(skip_memories),
        "edges": len(valid_edges),
        "edges_dropped": len(edges) - len(valid_edges),
        "sessions": len(sessions),
        "sessions_skipped": len(skip_sessions),
        "profile_sections": len(profile),
        "memories_by_project": dict(Counter(memory_projects.values()).most_common()),
        "sessions_by_project": dict(Counter(session_projects.values()).most_common()),
    }
    if dry_run:
        return report

    conn = connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        for m in memories:
            created = m.get("created_at") or now_iso()
            conn.execute(
                "INSERT OR IGNORE INTO memories "
                "(id, project_id, topic, decision, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    m["id"],
                    _project_id(conn, memory_projects[m["id"]]),
                    m["topic"].strip(),
                    m["decision"].strip(),
                    json.dumps(clean_tags(m.get("tags")), ensure_ascii=False),
                    created,
                    created,
                ),
            )
        for e in valid_edges:
            conn.execute(
                "INSERT OR IGNORE INTO edges "
                "(source_id, target_id, relation, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    e["source_id"],
                    e["target_id"],
                    e["relation"],
                    e.get("description"),
                    e.get("created_at") or now_iso(),
                ),
            )
        for s in sessions:
            decisions = [d for d in s.get("decisions_made", []) if d in memory_ids]
            conn.execute(
                "INSERT OR IGNORE INTO sessions "
                "(id, project_id, summary, tags, decisions, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    s["id"],
                    _project_id(conn, session_projects[s["id"]]),
                    s["summary"].strip(),
                    json.dumps(clean_tags(s.get("tags")), ensure_ascii=False),
                    json.dumps(decisions),
                    s.get("created_at") or now_iso(),
                ),
            )
        master = sessions_store.get("master", {})
        phase = (master.get("current_phase") or "").strip() or None
        steps = (master.get("next_steps") or "").strip() or None
        if phase or steps:
            conn.execute(
                "INSERT OR IGNORE INTO project_state (project_id, phase, next_steps, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (_project_id(conn, DEFAULT_PROJECT), phase, steps, now_iso()),
            )
        for section, value in profile.items():
            conn.execute(
                "INSERT OR IGNORE INTO profile (section, value, updated_at) VALUES (?, ?, ?)",
                (section, json.dumps(value, ensure_ascii=False), now_iso()),
            )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=Path("data"))
    parser.add_argument("--db", type=Path, default=None, help="Default: $ORION_DATA_DIR/orion.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    report = migrate(args.source, args.db, args.dry_run)
    logger.info(json.dumps(report, indent=2, ensure_ascii=False))
    if not args.dry_run:
        logger.info("Migration complete. Run `orion_health` to verify the counts.")


if __name__ == "__main__":
    main()
