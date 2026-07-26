# Orion

MCP server that gives memory, context, and semantic search to AI assistants. First constellation of the universe.

## Installation

```bash
cd orion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Connect your MCP client

Orion runs as a subprocess. Configure your client to launch it.

### OpenCode

Add to your `.opencode/opencode.jsonc`:

```jsonc
{
  "mcp": {
    "orion": {
      "type": "local",
      "command": [".venv/bin/python", "server.py"],
      "enabled": true
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "orion": {
      "command": "/path/to/orion/.venv/bin/python",
      "args": ["/path/to/orion/server.py"]
    }
  }
}
```

### VS Code / Neovim

Configure your MCP extension to run `python server.py` from the orion directory using stdio transport.

### HTTP mode

```bash
python server.py --transport http --port 9099
```

Then connect any HTTP-compatible client to `http://localhost:9099/mcp`.

## Tools

| Tool | Description |
|------|------------|
| `remember_decision` | Store an architectural decision or context with topic, decision, and optional tags |
| `recall_context` | Search past decisions by keyword match |

## Structure

```
orion/
├── server.py           # CLI entrypoint (argparse + mcp.run())
├── app.py              # FastMCP instance + tool registration
├── tools/
│   ├── __init__.py
│   └── memory.py       # remember_decision, recall_context
├── orion_config.py     # Paths, defaults, logging setup
├── data/               # Persistent storage (gitignored)
├── docs/
│   └── ACTA.md         # Founding act, roadmap, and work rules
├── requirements.txt
└── .gitignore
```
