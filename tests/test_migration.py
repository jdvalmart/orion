"""Legacy JSON import: quarantine, dangling edges, project inference, idempotency."""

from __future__ import annotations

import json
from pathlib import Path

import clean_test_data
import migrate_json_to_sqlite
import pytest

from orion import store


@pytest.fixture
def legacy(tmp_path: Path) -> Path:
    source = tmp_path / "legacy"
    source.mkdir()
    memories = [
        {"id": 1, "topic": "profile", "decision": "AI developer", "tags": ["profile"]},
        {"id": 2, "topic": "test_data", "decision": "x", "tags": ["llm", "test"]},
        {"id": 3, "topic": "'; DROP TABLE decisions; --", "decision": "x", "tags": []},
        {"id": 4, "topic": "mishkan-stack", "decision": "FastAPI", "tags": ["mishkan"]},
        {"id": 5, "topic": "ledger", "decision": "Pacioli ledger rules", "tags": ["accounting"]},
    ]
    for memory in memories:
        memory["created_at"] = "2026-09-01T00:00:00Z"
    (source / "memory.json").write_text(json.dumps(memories))
    (source / "graph.json").write_text(
        json.dumps(
            [
                {"source_id": 4, "target_id": 5, "relation": "relates_to"},
                {"source_id": 2, "target_id": 4, "relation": "depends_on"},
                {"source_id": 99999, "target_id": 1, "relation": "depends_on"},
            ]
        )
    )
    (source / "sessions.json").write_text(
        json.dumps(
            {
                "master": {"current_phase": "Fase 4", "next_steps": ""},
                "history": [
                    {
                        "id": 1,
                        "summary": "Pacioli phase 1",
                        "tags": ["pacioli"],
                        "decisions_made": [5, 2],
                        "created_at": "2026-09-02T00:00:00Z",
                    },
                    {
                        "id": 2,
                        "summary": "test_data",
                        "tags": ["lupus"],
                        "created_at": "2026-09-03T00:00:00Z",
                    },
                ],
            }
        )
    )
    (source / "whoami.json").write_text(json.dumps({"name": "Juan", "role": "Developer"}))
    return source


def test_quarantine_and_migration(legacy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(migrate_json_to_sqlite, "known_projects", lambda: ["mishkan", "pacioli"])
    result = clean_test_data.classify(legacy)
    assert result["memories"]["quarantined_ids"] == [2, 3]
    assert result["sessions"]["quarantined_ids"] == [2]
    (legacy / "quarantine.json").write_text(json.dumps(result))

    report = migrate_json_to_sqlite.migrate(legacy, None, dry_run=False)
    assert report["memories"] == 3
    assert report["edges"] == 1
    assert report["edges_dropped"] == 2
    assert report["memories_by_project"] == {"general": 1, "mishkan": 1, "pacioli": 1}

    assert store.browse_memories("mishkan").items[0].id == 4
    assert store.related(4).links[0].id == 5
    context = store.project_context("pacioli")
    assert context.recent_sessions[0].decisions == [5]
    assert store.project_context("general").phase == "Fase 4"
    assert store.get_profile() == {"name": "Juan", "role": "Developer"}

    # New memories continue after the highest imported id.
    assert store.add_memory("general", "t", "d").id == 6

    again = migrate_json_to_sqlite.migrate(legacy, None, dry_run=False)
    assert again["memories"] == 3
    assert store.health().memories == 4
