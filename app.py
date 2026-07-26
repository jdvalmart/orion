"""Orion — FastMCP server instance and tool registration."""

from fastmcp import FastMCP

mcp = FastMCP(
    "Orion",
    instructions="MCP server for developer memory and context. "
    "Use remember_decision to store architectural choices, "
    "recall_context to search by semantic similarity (TF-IDF), "
    "revise_decision to update entries, forget_decision to delete, "
    "browse_memories to list everything, and whoami for Juan's profile.",
)

from tools import memory, whoami  # noqa: E402, F401
