"""Local snapshots: consistent copy, rotation, readable result."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from orion import backup_local, store


def test_snapshot_is_a_readable_copy(data_dir: Path) -> None:
    store.add_memory("p", "t", "d")
    path = backup_local.snapshot()
    assert path.parent == data_dir / "backups" / "snapshots"
    with closing(sqlite3.connect(path)) as copy:
        assert copy.execute("SELECT topic FROM memories").fetchall() == [("t",)]


def test_rotation_keeps_newest(tmp_path: Path) -> None:
    store.add_memory("p", "t", "d")
    dest = tmp_path / "snaps"
    dest.mkdir()
    for day in range(1, 6):
        (dest / f"orion-2026-01-0{day}T00-00-00Z.db").write_bytes(b"old")
    new = backup_local.snapshot(dest, keep=3)
    remaining = sorted(p.name for p in dest.iterdir())
    assert len(remaining) == 3
    assert new.name == remaining[-1]
    assert "orion-2026-01-05T00-00-00Z.db" in remaining


def test_keep_must_be_positive() -> None:
    with pytest.raises(ValueError):
        backup_local.snapshot(keep=0)
