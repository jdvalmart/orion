# Orion — Session Context

This file is injected into every opencode session via the `instructions` config.
Update it at the end of each session.

## Current Status

- **Version**: 5.0.0 — SQLite storage, per-project memory (DONE)
- **Phases 1–4**: Foundation, RAG, Knowledge Graph, Session Memory (DONE)
- **Phase 5**: Hardening — single SQLite store (WAL, FTS5, optional sqlite-vec),
  projects, structured output, HTTP token auth, config-only S3 bucket, tests (DONE)
- **Total tools**: 15 (+2 S3 tools when `ORION_S3_BUCKET` is set)
- **Data**: `~/.local/share/orion/orion.db` — legacy JSON migrated, test pollution quarantined
- **Next**: optional — enable semantic search in Lupus runs; CI workflow for orion + lupus

## Project Architecture

```
orion/
├── src/orion/
│   ├── server.py       # CLI entrypoint (`orion`), transports, HTTP auth
│   ├── app.py          # FastMCP instance + instructions + tool registration
│   ├── config.py       # ORION_* environment settings, logging
│   ├── db.py           # SQLite connections, transactions, migrations
│   ├── store.py        # All reads/writes (memories, graph, sessions, profile)
│   ├── semantic.py     # Optional embeddings (fastembed + sqlite-vec)
│   ├── projects.py     # Project resolution
│   ├── models.py       # Pydantic output models
│   └── tools/          # memory, graph, session, profile, admin, backup
├── scripts/            # clean_test_data.py, migrate_json_to_sqlite.py
├── tests/              # pytest — always against a temp data dir
└── docs/
```

## Development Rules

See `docs/DEVELOPER.md` for the complete AI assistant work rules.
Key points: plan before code, teach and explain, never commit, everything in English,
document every module and model.

## Connection

- **Command for every stdio client**: `/home/jdvalmart/Proyectos/universo/orion/.venv/bin/orion`
- **OpenCode**: `"orion": {"type": "local", "command": ["<path>/.venv/bin/orion"]}`
- **Claude Desktop / Claude Code**: `"command": "<path>/.venv/bin/orion"` (no args)
- **HTTP mode**: `ORION_TOKEN=... orion --transport http` — bearer token required off-loopback
