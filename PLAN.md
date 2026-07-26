# Orion — Fase 1: Fundación

## Objetivo
Servidor MCP mínimo funcional con transporte dual (stdio + HTTP) y 2 herramientas de memoria.

## Estructura
```
orion/
├── server.py                  # FastMCP entrypoint, dual-transport
├── tools/
│   ├── __init__.py
│   └── memory.py              # remember_decision, recall_context
├── orion_config.py            # paths, defaults
├── data/                      # gitignored, datos persistentes
│   └── memory.json            # almacén simple de decisiones
├── requirements.txt           # fastmcp, pydantic
├── README.md
└── .gitignore
```

## Herramientas (Fase 1)

| Tool | Input | Output | Lógica |
|------|-------|--------|--------|
| `remember_decision` | topic, decision, tags (opt) | Confirmación | Guarda en data/memory.json con timestamp. JSON plano. |
| `recall_context` | query | Top-N decisiones | Búsqueda por keywords. Fase 2 migra a RAG con embeddings. |

## Decisiones de diseño

- **JSON plano en vez de SQLite**: premature optimization. Para <100 entradas es suficiente. Migrar cuando escale.
- **Búsqueda por keywords en vez de embeddings**: priorizamos tener el esqueleto corriendo rápido. La interfaz de la tool no cambiará en Fase 2.
- **Dual-transport desde día 1**: compatibilidad máxima con opencode (HTTP), Claude Desktop (stdio), VS Code y Neovim.
- **Sin auth**: single-user local. Auth se agrega cuando se necesite multi-usuario.

## Fases futuras

- Fase 2: RAG semántico (ChromaDB + sentence-transformers)
- Fase 3: Knowledge graph de conceptos
- Fase 4: Session memory con resúmenes automáticos
- Futuro: Vela (deploy), Draco (auditoría), Lyra (dashboards), Ara (integraciones)
