# Orion

MCP server that gives memory, context, and semantic search to AI assistants. First constellation of the universe.

## Transports

- **stdio** — compatible with Claude Desktop, VS Code, Neovim
- **HTTP** (`localhost:9099`) — compatible with opencode and HTTP clients

## Installation

```bash
cd orion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# stdio (Claude Desktop, VS Code, Neovim)
python server.py

# HTTP (opencode, HTTP clients)
python server.py --transport http --port 9099
```

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
