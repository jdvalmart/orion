"""S3 backup tools — cloud backup/restore for Orion memory and graph data.

Phase 1 deliverable: First AWS integration using boto3 SDK.
"""

import logging
from datetime import UTC, datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app import mcp
from orion_config import GRAPH_FILE, MEMORY_FILE

logger = logging.getLogger(__name__)


def _get_s3_client():
    return boto3.client("s3")


def _make_key(prefix: str, filename: str) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{prefix}/{ts}/{filename}"


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)
def backup_to_s3(bucket: str, prefix: str = "orion-backup") -> str:
    """Back up memory and graph data to an S3 bucket.

    Uploads memory.json and graph.json with timestamped keys.
    Requires AWS credentials configured via environment variables
    (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION).

    Args:
        bucket: S3 bucket name.
        prefix: Key prefix inside the bucket (default: "orion-backup").
    """
    s3 = _get_s3_client()
    uploaded: list[str] = []
    failed: list[str] = []

    for label, path in [("memory", MEMORY_FILE), ("graph", GRAPH_FILE)]:
        if not path.exists():
            logger.info("Skipping %s: file not found", label)
            continue

        key = _make_key(prefix, path.name)
        try:
            s3.upload_file(
                str(path),
                bucket,
                key,
                ExtraArgs={"ContentType": "application/json"},
            )
            uploaded.append(f"s3://{bucket}/{key}")
            logger.info("Uploaded %s → s3://%s/%s", label, bucket, key)
        except (BotoCoreError, ClientError) as exc:
            failed.append(f"{label}: {exc}")
            logger.error("Failed to upload %s: %s", label, exc)

    if not uploaded and not failed:
        return "No data files found to back up."

    lines = [f"Backed up {len(uploaded)} file(s):"]
    lines.extend(f"  {u}" for u in uploaded)
    if failed:
        lines.append(f"Failed {len(failed)}:")
        lines.extend(f"  {f}" for f in failed)

    return "\n".join(lines)


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
    },
)
def restore_from_s3(bucket: str, prefix: str = "orion-backup") -> str:
    """Restore memory and graph data from the most recent S3 backup.

    Downloads the latest memory.json and graph.json and overwrites
    local files. Requires AWS credentials.

    Args:
        bucket: S3 bucket name.
        prefix: Key prefix inside the bucket (default: "orion-backup").
    """
    s3 = _get_s3_client()
    restored: list[str] = []
    failed: list[str] = []

    for local_path in [MEMORY_FILE, GRAPH_FILE]:
        try:
            response = s3.list_objects_v2(
                Bucket=bucket,
                Prefix=f"{prefix}/",
            )
        except (BotoCoreError, ClientError) as exc:
            failed.append(f"{local_path.name}: {exc}")
            logger.error("Failed to list S3 objects: %s", exc)
            continue

        contents = response.get("Contents", [])
        matching = [
            obj for obj in contents if obj["Key"].endswith(local_path.name)
        ]
        if not matching:
            failed.append(f"{local_path.name}: no backup found in s3://{bucket}/{prefix}/")
            continue

        latest = max(matching, key=lambda o: o["LastModified"])
        try:
            s3.download_file(bucket, latest["Key"], str(local_path))
            restored.append(str(local_path))
            logger.info("Restored %s ← s3://%s/%s", local_path.name, bucket, latest["Key"])
        except (BotoCoreError, ClientError) as exc:
            failed.append(f"{local_path.name}: {exc}")
            logger.error("Failed to download %s: %s", local_path.name, exc)

    if not restored and not failed:
        return "No backups found in S3."

    lines = [f"Restored {len(restored)} file(s):"]
    lines.extend(f"  {r}" for r in restored)
    if failed:
        lines.append(f"Failed {len(failed)}:")
        lines.extend(f"  {f}" for f in failed)

    return "\n".join(lines)
