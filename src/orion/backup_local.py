"""Local snapshots of orion.db: ``orion-backup`` (run monthly by deploy/systemd/orion-backup.timer).

Uses SQLite's online backup API, so the copy is consistent even while MCP
clients are writing. Keeps the newest ``--keep`` snapshots and deletes older
ones. S3 backups (tools/backup.py) are independent of this.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from orion.config import get_settings
from orion.db import connect

logger = logging.getLogger(__name__)

PREFIX = "orion-"
SUFFIX = ".db"


def default_destination() -> Path:
    """``$ORION_DATA_DIR/backups/snapshots``."""
    return get_settings().backups_dir / "snapshots"


def snapshot(destination: Path | None = None, keep: int = 7) -> Path:
    """Write a verified snapshot and prune old ones. Returns the new file."""
    if keep < 1:
        raise ValueError("keep must be at least 1")
    target_dir = destination or default_destination()
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    target = target_dir / f"{PREFIX}{stamp}{SUFFIX}"
    partial = target.with_suffix(".partial")

    with closing(connect()) as source, closing(sqlite3.connect(partial)) as copy:
        source.backup(copy)
        check = copy.execute("PRAGMA integrity_check").fetchone()[0]
    if check != "ok":
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"Snapshot failed integrity check: {check}")
    partial.replace(target)

    snapshots = sorted(target_dir.glob(f"{PREFIX}*{SUFFIX}"))
    for old in snapshots[:-keep]:
        old.unlink()
    logger.info("Snapshot %s (%d kept)", target, min(len(snapshots), keep))
    return target


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="orion-backup", description="Snapshot the Orion database."
    )
    parser.add_argument(
        "--dest", type=Path, default=None, help="Default: <data dir>/backups/snapshots"
    )
    parser.add_argument("--keep", type=int, default=7, help="Snapshots to keep (default: 7)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    try:
        path = snapshot(args.dest, args.keep)
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        logger.error("Backup failed: %s", exc)
        sys.exit(1)
    sys.stdout.write(f"{path}\n")


if __name__ == "__main__":
    main()
