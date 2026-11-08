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

- **Everything in English.** Code, docstrings, log messages, tool output labels, UI strings, and commit messages. The only exception is data stored in JSON files, which may reflect the user's language.
- Type hints on every function signature.
- Pydantic models for domain data. No raw `dict` for persistent entities that have a known schema.
- `logging` with levels — never `print()`.
- No unnecessary comments. The code explains itself; comments explain *why*, not *what*.
- FastMCP tools use the `@mcp.tool()` decorator — never the `register_tools(mcp)` wrapper pattern.

## 6. Quality checks (mandatory before commit)

Every change must pass these checks without errors:

```bash
ruff check src tests scripts   # linting
ruff format src tests scripts  # formatting (applies automatically)
mypy                           # type checking (configured in pyproject.toml)
pytest -q                      # tests — always against a temp data dir, never real data
```

Install the package with every extra once:

```bash
uv pip install -e '.[semantic,s3,dev]'
```

No blind exceptions (`except Exception`) unless accompanied by a `# noqa: BLE001` comment explaining why the broad catch is intentional (e.g., embedding failures, where keyword search must keep working).

## 7. Documentation standards

Every module must be documented at the top with a docstring explaining its purpose. Every Pydantic model must have a docstring. Every tool must document all parameters using Google-style Args docstrings. There are no exceptions — undocumented code is unfinished code.

## 8. Architecture boundaries

- `src/orion/app.py` — FastMCP instance and instructions. Tool imports register tools.
- `src/orion/server.py` — CLI entrypoint (`orion`). Transport selection and HTTP auth.
- `src/orion/tools/` — thin async MCP wrappers, one file per tool group. No SQL here.
- `src/orion/store.py` — all reads and writes. Pure functions over SQLite, testable without MCP.
- `src/orion/db.py` — connections, transactions (`writing()` / `reading()`), schema migrations.
- `src/orion/semantic.py` — optional embeddings (fastembed + sqlite-vec). Must degrade to no-op.
- `src/orion/projects.py` — project resolution (argument → env → MCP roots → git cwd → general).
- `src/orion/config.py` — environment settings and logging. No business logic.
- Data lives in `$ORION_DATA_DIR` (default `~/.local/share/orion`), never inside the repo.
- Schema changes are new entries in `db.MIGRATIONS`; never edit an applied migration.

## 9. Session workflow

Every session must follow this pattern to maintain context across restarts:

**At the START of every session:**
1. Read `docs/SESSION_CONTEXT.md` (injected automatically by opencode `instructions` config).
2. Call `recall_session` via Orion to get the project's phase, next steps and recent history.

**At the END of every session:**
1. Call `remember_session` with a concise summary, `next_steps` and, if it changed, `phase`.
2. Update `docs/SESSION_CONTEXT.md` to reflect the new phase, tool count, and next steps.

## 10. Documentation files

- `README.md` — public: install, usage, connection guide.
- `docs/ACTA.md` — single internal document: founding context, architecture, roadmap, work rules, git workflow.
- `docs/DEVELOPER.md` — this file. AI assistant work rules.
- `docs/SESSION_CONTEXT.md` — injected each session. Updated at session end.
- No new `.md` files without explicit approval.
