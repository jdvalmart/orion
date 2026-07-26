# Orion

MCP server que da memoria, contexto y búsqueda semántica a asistentes de IA. Primera constelación del universo.

## Transportes

- **stdio** — compatible con Claude Desktop, VS Code, Neovim
- **HTTP** (`localhost:9099`) — compatible con opencode y clientes HTTP

## Instalación

```bash
cd orion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
# stdio (Claude Desktop, VS Code, Neovim)
python server.py

# HTTP (opencode, clientes HTTP)
python server.py --transport http --port 9099
```

## Herramientas

| Tool | Descripción |
|------|------------|
| `remember_decision` | Guarda una decisión de arquitectura/contexto |
| `recall_context` | Recupera decisiones relevantes por keywords |

## Estructura

```
orion/
├── server.py           # FastMCP entrypoint
├── tools/              # Implementaciones de herramientas
│   ├── __init__.py
│   └── memory.py
├── orion_config.py     # Configuración centralizada
├── data/               # Datos persistentes (gitignored)
├── requirements.txt
└── PLAN.md             # Roadmap y decisiones de diseño
```
