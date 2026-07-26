# Orion — Session Context

This file is injected into every opencode session via the `instructions` config.
Update it at the end of each session.

## Current Status

- **Phase**: Fase 4 — Session Memory (IN PROGRESS)
- **Phase 1**: Foundation — 6 memory tools + whoami (DONE)
- **Phase 2**: RAG — ChromaDB ONNX embeddings (DONE)
- **Phase 3**: Knowledge Graph — link, find, browse (DONE)
- **Phase 4**: Session Memory — hybrid architecture (NOW)
- **Total tools**: 12
- **Next**: Telescopium (test suite)

## Project Architecture

```
orion/
├── server.py           # CLI entrypoint (argparse + mcp.run())
├── app.py              # FastMCP instance + tool registration
├── tools/
│   ├── memory.py       # remember, recall, revise, forget, browse_memories
│   ├── whoami.py       # Juan's professional profile
│   ├── graph.py        # link_concepts, find_related, browse_graph
│   └── session.py      # remember_session, recall_session, browse_sessions
├── orion_config.py     # Paths, logging, ChromaDB config
├── data/               # Persistent storage (gitignored)
├── logs/               # Runtime diagnostics (gitignored)
├── docs/
│   ├── ACTA.md         # Founding act + roadmap
│   ├── DEVELOPER.md    # AI assistant rules
│   └── SESSION_CONTEXT.md  # This file
└── requirements.txt
```

## Development Rules

See `docs/DEVELOPER.md` for the complete AI assistant work rules.
Key points: plan before code, teach and explain, never commit, everything in English,
document every module and model.

## Connection

- **OpenCode Desktop/TUI**: reads `~/.config/opencode/opencode.json` (global)
- **Claude Desktop**: configure `claude_desktop_config.json` to run `server.py`
- **HTTP mode**: `curl -X POST http://localhost:9099/mcp`
