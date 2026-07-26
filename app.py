"""Orion — FastMCP server instance and tool registration."""

from fastmcp import FastMCP

mcp = FastMCP(
    "Orion",
    instructions="MCP server for developer memory and context. "
    "Use remember_decision to store architectural choices and "
    "recall_context to search past decisions by keyword.",
)

from tools import memory  # noqa: E402, F401 — triggers @mcp.tool() decorators
