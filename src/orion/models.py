"""Pydantic models returned by tools (FastMCP turns them into structured output)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Scope = Literal["project", "all"]
MatchKind = Literal["keyword", "semantic", "both"]


class Memory(BaseModel):
    """A stored decision."""

    id: int
    project: str
    topic: str
    decision: str
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class MemoryHit(Memory):
    """A memory returned by a search, with its relevance."""

    score: float = Field(description="Reciprocal-rank-fusion score; higher is more relevant.")
    match: MatchKind


class MemorySummary(BaseModel):
    """Compact listing entry (no decision body, to save context tokens)."""

    id: int
    project: str
    topic: str
    tags: list[str] = Field(default_factory=list)
    created_at: str


class SearchResult(BaseModel):
    """Result of recall_context."""

    query: str
    project: str | None = Field(description="Project searched, or null when scope is 'all'.")
    mode: Literal["keyword", "hybrid"]
    results: list[MemoryHit]


class MemoryPage(BaseModel):
    """A page of memories from browse_memories."""

    project: str | None
    total: int
    offset: int
    items: list[MemorySummary]


class Edge(BaseModel):
    """A directed relationship between two memories."""

    source_id: int
    target_id: int
    relation: str
    description: str | None = None
    created_at: str


class RelatedLink(BaseModel):
    """One neighbour of a memory in the knowledge graph."""

    id: int
    topic: str
    relation: str
    direction: Literal["outgoing", "incoming"]
    description: str | None = None


class Related(BaseModel):
    """All direct neighbours of a memory."""

    id: int
    topic: str
    links: list[RelatedLink]


class EdgePage(BaseModel):
    """A page of graph edges."""

    project: str | None
    total: int
    offset: int
    items: list[Edge]


class Session(BaseModel):
    """A recorded work session."""

    id: int
    project: str
    summary: str
    next_steps: str | None = None
    tags: list[str] = Field(default_factory=list)
    decisions: list[int] = Field(default_factory=list)
    created_at: str


class SessionPage(BaseModel):
    """A page of sessions."""

    project: str | None
    total: int
    offset: int
    items: list[Session]


class ProjectContext(BaseModel):
    """Everything an assistant needs to resume work on a project."""

    project: str
    phase: str | None
    next_steps: str | None
    total_sessions: int
    total_memories: int
    recent_sessions: list[Session]
    recent_decisions: list[MemorySummary]


class ProjectInfo(BaseModel):
    """A project and its counts."""

    name: str
    memories: int
    sessions: int
    phase: str | None


class Health(BaseModel):
    """Diagnostics for the running server and its store."""

    version: str
    data_dir: str
    db_path: str
    schema_version: int
    integrity: str
    projects: int
    memories: int
    deleted_memories: int
    edges: int
    sessions: int
    semantic: dict[str, Any]
    s3_configured: bool
