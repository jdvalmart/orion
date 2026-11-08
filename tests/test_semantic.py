"""Hybrid search with real embeddings. Skipped unless the model is already downloaded.

Point ORION_TEST_MODELS_DIR at a folder that holds the fastembed model
(by default ~/.local/share/orion/models) to run these.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from orion import semantic, store

MODELS = Path(os.environ.get("ORION_TEST_MODELS_DIR", Path.home() / ".local/share/orion/models"))

pytestmark = pytest.mark.skipif(
    not MODELS.is_dir() or not any(MODELS.iterdir()),
    reason="embedding model not downloaded",
)


@pytest.fixture(autouse=True)
def semantic_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORION_SEMANTIC", "auto")
    monkeypatch.setenv("ORION_MODELS_DIR", str(MODELS))
    if not semantic.enabled():
        pytest.skip("semantic extras not installed")


def test_semantic_match_without_shared_keywords() -> None:
    store.add_memory("p", "payments", "Wompi handles card and PSE checkout")
    store.add_memory("p", "styling", "Tailwind with a warm palette")
    result = store.search_memories("cobros con tarjeta de crédito", "p", limit=1)
    assert result.mode == "hybrid"
    assert result.results[0].topic == "payments"
    assert result.results[0].match == "semantic"


def test_missing_vectors_are_backfilled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORION_SEMANTIC", "off")
    store.add_memory("p", "queue", "Background jobs with a task queue")
    monkeypatch.setenv("ORION_SEMANTIC", "auto")
    assert store.health().semantic["missing"] == 1
    store.search_memories("jobs", "p")
    assert store.health().semantic["missing"] == 0


def test_forget_removes_vector() -> None:
    memory = store.add_memory("p", "cache", "Redis for sessions")
    store.delete_memory(memory.id)
    assert store.health().semantic["indexed"] == 0
