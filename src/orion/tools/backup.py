"""S3 backup and restore of the whole Orion database.

Only registered when ``ORION_S3_BUCKET`` is set and boto3 is installed
(``pip install 'orion[s3]'``). The bucket comes from configuration, never from
a tool argument, so a prompt-injected assistant cannot send the memory store
to an arbitrary bucket.
"""

from __future__ import annotations

import logging
import sqlite3
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastmcp.exceptions import ToolError

from orion.app import mcp
from orion.config import get_settings
from orion.db import SCHEMA_VERSION, connect
from orion.tools import DESTRUCTIVE, WRITE

logger = logging.getLogger(__name__)

_OBJECT_NAME = "orion.db"


def _snapshot(destination: Path) -> None:
    """Consistent copy of the live database, safe while other processes write."""
    with closing(connect()) as source, closing(sqlite3.connect(destination)) as target:
        source.backup(target)


def _bucket() -> tuple[str, str]:
    settings = get_settings()
    if settings.s3_bucket is None:
        raise ToolError("ORION_S3_BUCKET is not configured.")
    return settings.s3_bucket, settings.s3_prefix


@mcp.tool(annotations=WRITE)
def backup_to_s3() -> dict[str, Any]:
    """Upload a consistent snapshot of the Orion database to the configured S3 bucket."""
    bucket, prefix = _bucket()
    key = f"{prefix}/{datetime.now(UTC).strftime('%Y-%m-%dT%H-%M-%SZ')}/{_OBJECT_NAME}"
    with tempfile.TemporaryDirectory() as tmp:
        snapshot = Path(tmp) / _OBJECT_NAME
        _snapshot(snapshot)
        size = snapshot.stat().st_size
        try:
            boto3.client("s3").upload_file(str(snapshot), bucket, key)
        except (BotoCoreError, ClientError) as exc:
            raise ToolError(f"Upload failed: {exc}") from exc
    logger.info("Backed up Orion to s3://%s/%s", bucket, key)
    return {"uri": f"s3://{bucket}/{key}", "bytes": size}


def _latest_key(bucket: str, prefix: str) -> dict[str, Any]:
    paginator = boto3.client("s3").get_paginator("list_objects_v2")
    latest: dict[str, Any] | None = None
    for page in paginator.paginate(Bucket=bucket, Prefix=f"{prefix}/"):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(f"/{_OBJECT_NAME}") and (
                latest is None or obj["LastModified"] > latest["LastModified"]
            ):
                latest = obj
    if latest is None:
        raise ToolError(f"No backups found in s3://{bucket}/{prefix}/")
    return latest


@mcp.tool(annotations=DESTRUCTIVE)
def restore_from_s3(confirm: bool = False) -> dict[str, Any]:
    """Replace the local database with the most recent S3 backup.

    Without confirm=true it only reports which backup would be restored. The
    current database is always copied to the local backups folder first.

    Args:
        confirm: Must be true to actually overwrite the local database.
    """
    bucket, prefix = _bucket()
    try:
        latest = _latest_key(bucket, prefix)
    except (BotoCoreError, ClientError) as exc:
        raise ToolError(f"Listing backups failed: {exc}") from exc

    found = {
        "uri": f"s3://{bucket}/{latest['Key']}",
        "last_modified": latest["LastModified"].isoformat(),
        "bytes": latest["Size"],
    }
    if not confirm:
        return {"would_restore": found, "note": "Call again with confirm=true to restore."}

    settings = get_settings()
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    safety_copy = settings.backups_dir / f"pre-restore-{stamp}.db"

    with tempfile.TemporaryDirectory() as tmp:
        downloaded = Path(tmp) / _OBJECT_NAME
        try:
            boto3.client("s3").download_file(bucket, latest["Key"], str(downloaded))
        except (BotoCoreError, ClientError) as exc:
            raise ToolError(f"Download failed: {exc}") from exc

        with closing(sqlite3.connect(downloaded)) as candidate:
            check = candidate.execute("PRAGMA quick_check").fetchone()[0]
            version = candidate.execute("PRAGMA user_version").fetchone()[0]
        if check != "ok" or version > SCHEMA_VERSION:
            raise ToolError(f"Backup rejected (integrity={check}, schema={version}).")

        _snapshot(safety_copy)
        with closing(sqlite3.connect(downloaded)) as source, closing(connect()) as live:
            source.backup(live)

    logger.warning("Restored Orion from %s (previous copy: %s)", found["uri"], safety_copy)
    return {"restored": found, "previous_copy": str(safety_copy)}
