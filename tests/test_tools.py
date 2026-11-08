"""MCP surface: tool list, structured output, errors, project resolution, prompt, resource."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

pytestmark = pytest.mark.anyio

EXPECTED_TOOLS = {
    "remember_decision",
    "recall_context",
    "revise_decision",
    "forget_decision",
    "browse_memories",
    "link_concepts",
    "find_related",
    "browse_graph",
    "remember_session",
    "recall_session",
    "browse_sessions",
    "list_projects",
    "whoami",
    "update_profile",
    "orion_health",
}


async def test_tools_are_listed_with_output_schemas(client: Client) -> None:
    tools = {tool.name: tool for tool in await client.list_tools()}
    assert set(tools) == EXPECTED_TOOLS
    assert tools["recall_context"].output_schema is not None
    assert tools["forget_decision"].annotations is not None
    assert tools["forget_decision"].annotations.destructive_hint is True


async def test_round_trip_with_structured_output(client: Client) -> None:
    stored = await client.call_tool(
        "remember_decision",
        {"topic": "db", "decision": "SQLite", "tags": ["storage"], "project": "demo"},
    )
    assert stored.structured_content is not None
    assert stored.structured_content["project"] == "demo"

    found = await client.call_tool("recall_context", {"query": "sqlite", "project": "demo"})
    assert found.structured_content is not None
    assert found.structured_content["results"][0]["id"] == stored.structured_content["id"]


async def test_legacy_comma_separated_tags_are_accepted(client: Client) -> None:
    stored = await client.call_tool(
        "remember_decision", {"topic": "t", "decision": "d", "tags": "a, b", "project": "x"}
    )
    assert stored.structured_content is not None
    assert stored.structured_content["tags"] == ["a", "b"]


async def test_errors_are_reported_as_tool_errors(client: Client) -> None:
    result = await client.call_tool("forget_decision", {"id": 42}, raise_on_error=False)
    assert result.is_error
    assert "not found" in result.content[0].text  # type: ignore[union-attr]

    invalid = await client.call_tool(
        "link_concepts",
        {"source_id": 1, "target_id": 2, "relation": "owns"},
        raise_on_error=False,
    )
    assert invalid.is_error


async def test_project_defaults_to_general(client: Client) -> None:
    stored = await client.call_tool("remember_decision", {"topic": "t", "decision": "d"})
    assert stored.structured_content is not None
    assert stored.structured_content["project"] == "general"


async def test_project_from_environment(client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORION_PROJECT", "Mi Proyecto")
    stored = await client.call_tool("remember_decision", {"topic": "t", "decision": "d"})
    assert stored.structured_content is not None
    assert stored.structured_content["project"] == "mi-proyecto"


async def test_project_from_git_working_directory(
    client: Client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "Pacioli"
    (repo / ".git").mkdir(parents=True)
    (repo / "backend").mkdir()
    monkeypatch.chdir(repo / "backend")
    context = await client.call_tool("recall_session", {})
    assert context.structured_content is not None
    assert context.structured_content["project"] == "pacioli"


async def test_session_cycle(client: Client) -> None:
    await client.call_tool(
        "remember_session",
        {"summary": "Did X", "next_steps": "Do Y", "phase": "Beta", "project": "demo"},
    )
    context = await client.call_tool("recall_session", {"project": "demo"})
    assert context.structured_content is not None
    assert context.structured_content["next_steps"] == "Do Y"
    assert context.structured_content["phase"] == "Beta"


async def test_profile_tools(client: Client) -> None:
    await client.call_tool("update_profile", {"section": "summary", "value": "Dev"})
    profile = await client.call_tool("whoami", {})
    assert profile.structured_content is not None
    assert profile.structured_content == {"summary": "Dev"} or profile.data == {"summary": "Dev"}


async def test_resource_and_prompt(client: Client) -> None:
    await client.call_tool("remember_session", {"summary": "Kickoff", "project": "demo"})
    resource = await client.read_resource("orion://project/demo/context")
    assert '"Kickoff"' in resource[0].text  # type: ignore[union-attr]

    prompt = await client.get_prompt("start_session", {"project": "demo"})
    assert "Kickoff" in prompt.messages[0].content.text  # type: ignore[union-attr]


async def test_health(client: Client) -> None:
    health = await client.call_tool("orion_health", {})
    assert health.structured_content is not None
    assert health.structured_content["integrity"] == "ok"
    assert health.structured_content["semantic"] == {"enabled": False}
