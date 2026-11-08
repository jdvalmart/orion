"""Identify test pollution in the legacy JSON store (left behind by Lupus runs).

Never modifies the source files: it writes ``quarantine.json`` with the IDs of
memories and sessions classified as test data, plus their content for manual
review. ``migrate_json_to_sqlite.py`` skips everything listed there.

Usage:
    python scripts/clean_test_data.py --source data --dry-run
    python scripts/clean_test_data.py --source data
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("clean_test_data")

TEST_TAGS = {"bulk", "performance", "llm", "test", "unicode", "recall", "lupus", "persistence"}
TEST_TOPIC = re.compile(r"^(test|bulk_topic|graph_node|long_input|emoji)")


def is_test_memory(entry: dict[str, Any]) -> bool:
    """Lupus fixtures carry test tags, synthetic topics, or no tags at all.

    Every real memory in the store has tags; the untagged entries are
    adversarial inputs (SQL injection, path traversal, unicode tricks).
    """
    tags = set(entry.get("tags") or [])
    topic = (entry.get("topic") or "").strip()
    return not tags or bool(tags & TEST_TAGS) or not topic or bool(TEST_TOPIC.match(topic))


def is_test_session(entry: dict[str, Any]) -> bool:
    """Same rule for sessions: untagged or tagged as test data."""
    tags = set(entry.get("tags") or [])
    summary = (entry.get("summary") or "").strip()
    return not tags or bool(tags & TEST_TAGS) or not summary or summary == "test_data"


def classify(source: Path) -> dict[str, Any]:
    """Split legacy entries into kept and quarantined."""
    memories = json.loads((source / "memory.json").read_text(encoding="utf-8"))
    sessions_file = source / "sessions.json"
    sessions = (
        json.loads(sessions_file.read_text(encoding="utf-8")).get("history", [])
        if sessions_file.exists()
        else []
    )
    bad_memories = [m for m in memories if is_test_memory(m)]
    bad_sessions = [s for s in sessions if is_test_session(s)]
    return {
        "memories": {
            "total": len(memories),
            "quarantined_ids": [m["id"] for m in bad_memories],
            "entries": bad_memories,
        },
        "sessions": {
            "total": len(sessions),
            "quarantined_ids": [s["id"] for s in bad_sessions],
            "entries": bad_sessions,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=Path("data"))
    parser.add_argument("--dry-run", action="store_true", help="Only print the summary.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    result = classify(args.source)
    for kind in ("memories", "sessions"):
        part = result[kind]
        kept = part["total"] - len(part["quarantined_ids"])
        logger.info(
            "%s: %d total, %d quarantined, %d kept",
            kind,
            part["total"],
            len(part["quarantined_ids"]),
            kept,
        )

    if args.dry_run:
        return
    target = args.source / "quarantine.json"
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s — review it before migrating.", target)


if __name__ == "__main__":
    main()
