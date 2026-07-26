# Developer Guide

This file defines how the AI assistant must work on Orion. It must be read at the start of every session, alongside `COMMIT_RULES.md`.

## 1. Plan first, code after

Before writing or modifying any file, present a plan with:

- What you will do (concrete objective)
- Why you chose that approach (logic and alternatives considered)
- Files you will modify or create
- Risks or trade-offs

**Do not write code until the plan is explicitly approved.**

## 2. Teach, don't just execute

- Explain the reasoning behind every technical decision. Juan wants to understand *why*, not just *what*.
- If you build something, walk through how it works — architecture, data flow, edge cases.
- Be critical: if there is a better way, point it out and discuss it.
- Correct Juan if he proposes something that goes against best practices or the project's own rules.

## 3. Learning by doing

Juan learns by building real things. Prefer concrete examples over abstract explanations. When introducing a new concept or library, show it working in Orion's codebase — not in a hypothetical snippet. Every change is a learning opportunity.

## 4. No automatic commits

Never run `git commit`, `git add`, `git push`, or any repository mutation. Only provide commit messages in chat following `COMMIT_RULES.md`.

## 5. Code conventions

- Code, docstrings, and commit messages in English.
- Type hints on every function signature.
- Pydantic models for domain data. No raw `dict` for persistent entities.
- `logging` with levels — never `print()`.
- No unnecessary comments. The code explains itself; comments explain *why*, not *what*.
- FastMCP tools use the `@mcp.tool()` decorator, not the wrapper pattern.

## 6. Architecture boundaries

- `app.py` — FastMCP instance only. Tool imports have a side-effect of registering tools via decorators.
- `server.py` — CLI entrypoint only. `argparse` + `mcp.run()`.
- `tools/` — tool implementations. One file per tool group. Imports `mcp` from `app`.
- `data/` — persistent storage. Gitignored. JSON flat files in Phase 1.
- `orion_config.py` — paths, constants, logging setup. No business logic.

## 7. Documentation

- `README.md` — public: install, usage, connection guide.
- `docs/ACTA.md` — single internal document: founding context, architecture, roadmap, work rules, git workflow.
- No new `.md` files without explicit approval.
