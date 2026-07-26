"""Orion — FastMCP server instance and tool registration."""

from fastmcp import FastMCP

mcp = FastMCP(
    "Orion",
    instructions="MCP server for developer memory and context. "
    "Use remember_decision to store architectural choices, "
    "recall_context to search by semantic similarity (ChromaDB), "
    "revise_decision to update entries, forget_decision to delete, "
    "browse_memories to list everything, and whoami for Juan's profile. "
    "Use link_concepts, find_related, and browse_graph for the knowledge graph. "
    "Use recall_session at the start of every session and "
    "remember_session at the end to maintain context across sessions.",
)

from tools import graph, memory, session, whoami  # noqa: F401, E402 — decorator side-effects
