"""The FastMCP server instance and tool registration."""

from __future__ import annotations

import importlib.util

from fastmcp import FastMCP

from orion import __version__
from orion.config import get_settings

INSTRUCTIONS = """\
Orion is the developer's long-term memory, organised by project.
The project is inferred from the workspace; pass `project` explicitly when the
client has no workspace (e.g. a desktop chat) or to work on another project.

- At the start of a session call `recall_session` to restore phase, next steps
  and recent work.
- Before making or proposing an architectural decision, search with
  `recall_context` (use scope="all" to look across projects).
- Store each meaningful decision with `remember_decision` (what and why).
  If it replaces an older one, pass `supersedes`.
- At the end of a session call `remember_session` with a summary and next steps.
- `whoami` returns the developer's profile.
"""

mcp = FastMCP("Orion", instructions=INSTRUCTIONS, version=__version__)

from orion.tools import admin, graph, memory, profile, session  # noqa: E402, F401 — registers tools

if get_settings().s3_bucket and importlib.util.find_spec("boto3") is not None:
    from orion.tools import backup  # noqa: F401 — registers S3 tools only when configured
