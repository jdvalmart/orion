"""Store-level behaviour: ids, search, graph integrity, sessions, profile, concurrency."""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path

import pytest

from orion import store


def test_ids_are_never_reused_after_delete() -> None:
    first = store.add_memory("p", "a", "first")
    second = store.add_memory("p", "b", "second")
    store.delete_memory(second.id)
    third = store.add_memory("p", "c", "third")
    assert third.id == second.id + 1
    assert first.id < second.id


def test_keyword_search_ranks_topic_matches_and_filters_project() -> None:
    store.add_memory("pacioli", "database", "Use SQLite with WAL mode", ["sqlite"])
    store.add_memory("pacioli", "frontend", "React with Vite")
    store.add_memory("mishkan", "database", "Postgres via SQLAlchemy")

    result = store.search_memories("database sqlite", "pacioli")
    assert [hit.topic for hit in result.results] == ["database"]
    assert result.results[0].project == "pacioli"
    assert result.mode == "keyword"

    everywhere = store.search_memories("database", None)
    assert {hit.project for hit in everywhere.results} == {"pacioli", "mishkan"}


def test_search_matches_accents_and_prefixes() -> None:
    store.add_memory("p", "facturación", "Integración con la DIAN")
    assert store.search_memories("facturacion", "p").results
    assert store.search_memories("integra", "p").results


def test_search_rejects_queries_without_words() -> None:
    with pytest.raises(store.InvalidInputError):
        store.search_memories("!!! ???", "p")


def test_deleted_memories_disappear_from_search_and_listing() -> None:
    memory = store.add_memory("p", "cache", "Use Redis")
    store.delete_memory(memory.id)
    assert store.search_memories("redis", "p").results == []
    assert store.browse_memories("p").total == 0
    with pytest.raises(store.NotFoundError):
        store.delete_memory(memory.id)


def test_update_changes_only_given_fields_and_reindexes() -> None:
    memory = store.add_memory("p", "auth", "Sessions in cookies", ["auth"])
    updated = store.update_memory(memory.id, decision="JWT with refresh tokens")
    assert updated.topic == "auth"
    assert updated.tags == ["auth"]
    assert store.search_memories("refresh", "p").results[0].id == memory.id
    assert store.search_memories("cookies", "p").results == []


def test_tags_are_normalised_and_filterable() -> None:
    store.add_memory("p", "t", "d", [" Python ", "python", "FastAPI", ""])
    page = store.browse_memories("p", tag="fastapi")
    assert page.total == 1
    assert page.items[0].tags == ["python", "fastapi"]


def test_graph_rejects_unknown_ids_and_cascades_on_forget() -> None:
    a = store.add_memory("p", "a", "A")
    b = store.add_memory("p", "b", "B")
    with pytest.raises(store.NotFoundError):
        store.link(a.id, 9999, "depends_on")
    store.link(a.id, b.id, "depends_on", "A needs B")
    with pytest.raises(store.InvalidInputError):
        store.link(a.id, b.id, "depends_on")

    assert store.related(b.id).links[0].direction == "incoming"
    store.delete_memory(b.id)
    assert store.related(a.id).links == []
    assert store.browse_edges(None).total == 0


def test_supersedes_creates_edge() -> None:
    old = store.add_memory("p", "orm", "Raw SQL")
    new = store.add_memory("p", "orm", "SQLAlchemy 2", supersedes=old.id)
    links = store.related(new.id).links
    assert [(link.id, link.relation) for link in links] == [(old.id, "supersedes")]


def test_sessions_feed_project_context() -> None:
    decision = store.add_memory("p", "a", "A")
    store.add_session("p", "Set up repo", phase="Phase 0", next_steps="Write API")
    store.add_session("p", "Built API", decisions=[decision.id], next_steps="Frontend")
    store.add_session("other", "Unrelated")

    context = store.project_context("p")
    assert context.phase == "Phase 0"
    assert context.next_steps == "Frontend"
    assert context.total_sessions == 2
    assert [s.summary for s in context.recent_sessions] == ["Built API", "Set up repo"]
    assert context.recent_decisions[0].id == decision.id

    with pytest.raises(store.NotFoundError):
        store.add_session("p", "x", decisions=[9999])


def test_unknown_project_has_empty_context_and_is_not_created() -> None:
    context = store.project_context("nope")
    assert context.total_memories == 0
    assert store.list_projects() == []


def test_profile_sections() -> None:
    store.set_profile_section("Summary", "Backend developer")
    profile = store.set_profile_section("skills", {"languages": ["python"]})
    assert profile == {"summary": "Backend developer", "skills": {"languages": ["python"]}}
    assert store.set_profile_section("summary", None) == {"skills": {"languages": ["python"]}}
    with pytest.raises(store.NotFoundError):
        store.set_profile_section("missing", None)


def _writer(data_dir: str, worker: int, count: int) -> None:
    os.environ["ORION_DATA_DIR"] = data_dir
    os.environ["ORION_SEMANTIC"] = "off"
    for index in range(count):
        store.add_memory("load", f"w{worker}-{index}", "concurrent write")


def test_concurrent_processes_do_not_lose_writes(data_dir: Path) -> None:
    store.health()  # create the schema up front
    context = multiprocessing.get_context("spawn")
    workers = [
        context.Process(target=_writer, args=(str(data_dir), worker, 100)) for worker in range(3)
    ]
    for process in workers:
        process.start()
    for process in workers:
        process.join(timeout=120)
        assert process.exitcode == 0

    page = store.browse_memories("load", limit=100)
    assert page.total == 300
    health = store.health()
    assert health.memories == 300
    assert health.integrity == "ok"


def test_stopwords_and_short_words_do_not_prefix_match() -> None:
    store.add_memory("p", "conventions", "Commit message rules")
    assert store.fts_query("con la") is None
    assert store.search_memories("cobros con tarjeta", "p").results == []


def test_profile_section_size_is_capped() -> None:
    with pytest.raises(store.InvalidInputError):
        store.set_profile_section("big", "x" * (store.PROFILE_SECTION_MAX + 1))
    assert store.get_profile() == {}
