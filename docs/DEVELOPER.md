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

## 6. Documentation standards

Every module must be documented at the top with a docstring explaining its purpose. Every Pydantic model must have a docstring. Every tool must document all parameters using Google-style Args docstrings. There are no exceptions — undocumented code is unfinished code.

## 7. Architecture boundaries

- `app.py` — FastMCP instance only. Tool imports trigger `@mcp.tool()` decorator side-effects.
- `server.py` — CLI entrypoint only. `argparse` + `mcp.run()`.
- `tools/` — tool implementations. One file per tool group. Imports `mcp` from `app`.
- `data/` — persistent storage. Gitignored. JSON flat files in Phase 1.
- `logs/` — runtime diagnostics. Gitignored. Rotated via `RotatingFileHandler`.
- `orion_config.py` — paths, constants, logging setup. No business logic.

## 8. Session workflow

Every session must follow this pattern to maintain context across restarts:

**At the START of every session:**
1. Read `docs/SESSION_CONTEXT.md` (injected automatically by opencode `instructions` config).
2. Call `recall_session` via Orion to get the accumulated master context and recent history.

**At the END of every session:**
1. Call `remember_session` with a concise summary of what was accomplished.
2. Update `docs/SESSION_CONTEXT.md` to reflect the new phase, tool count, and next steps.

## 9. Documentation files

- `README.md` — public: install, usage, connection guide.
- `docs/ACTA.md` — single internal document: founding context, architecture, roadmap, work rules, git workflow.
- `docs/DEVELOPER.md` — this file. AI assistant work rules.
- `docs/SESSION_CONTEXT.md` — injected each session. Updated at session end.
- No new `.md` files without explicit approval.
