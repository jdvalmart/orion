# Orion — Acta de Fundación

**Fecha:** 25 de julio de 2026  
**Autor:** Juan David Valencia Martínez  
**Asistente:** OpenCode (deepseek-v4-pro)

---

## 1. Contexto de la sesión

Esta sesión tuvo tres objetivos:

1. **Actualizar mi perfil profesional** (`perfil.md`, `hoja-de-vida.md`, y portafolio web `portafolio-jdvalmart`) tras un cambio importante: el 1 de junio de 2026 ingresé a **Trajectory Inc.** (empresa canadiense) como AI Developer en el área **Initus**, encargada del backend y la IA corporativa.

2. **Definir una especialización en IA** basada en el análisis de mi bootcamp (MinTIC, 37+ notebooks, 26 sesiones) y mi trabajo actual.

3. **Crear un proyecto que materialice esa especialización** — Orion.

---

## 2. Mi situación actual

### Trabajo
- **AI Developer en Trajectory Inc.** (remoto desde Colombia)
- Área **Initus**: backend + inteligencia artificial
- Construyo y mantengo un **MCP empresarial para Claude** con 140+ herramientas
- Stack: Python, FastAPI, FastMCP, PostgreSQL, ChromaDB, Ollama, Docker
- El MCP conecta a Claude con: meetings, Wrike, BambooHR, GitHub, NetSuite, Google Workspace, BI

### Formación
- **Ingeniería de Software** — Politécnico Grancolombiano (graduado marzo 2026)
- **Diplomado en Ciencias de la Computación** — Politécnico Grancolombiano (2025)
- **Bootcamp IA (Básico + Intermedio)** — Talento Tech, MinTIC (2025-2026)
- **Tecnólogo ADSO** — SENA (2020-2022)

### Proyectos personales
- `portafolio-jdvalmart` — Portafolio web con chatbot RAG (React + FastAPI)
- `pequeletores` — Recomendador de libros infantiles con TF-IDF (React + FastAPI + scikit-learn)
- `book-tracker` — CRUD full-stack de libros (React + FastAPI + PostgreSQL + Docker)

---

## 3. Análisis del bootcamp: fortalezas y brechas

### Lo que ya sé (fortalezas)
- Pipelines ML con scikit-learn (preprocesamiento → entrenamiento → evaluación → tuning)
- Deep Learning: MLP, CNN, RNN, LSTM, GAN, autoencoders
- NLP: TF-IDF, BERT fine-tuning, NER con spaCy y Transformers
- XAI: LIME, SHAP, Grad-CAM, Captum
- Sistemas distribuidos básicos: Kafka, Hadoop, Dask
- Deployment básico: Flask, Docker

### Lo que NO vi en el bootcamp (brechas)
- **Arquitectura de Transformers** a profundidad (solo uso como black-box)
- **LLMs**: prompt engineering, RAG, function calling, agentes
- **Embeddings modernos**: Word2Vec, sentence-transformers, vector stores
- **MLOps real**: CI/CD para ML, model registries, experiment tracking
- **Evaluación de retrieval**: precision@k, recall, MRR, NDCG
- **Cloud deployment**: AWS/GCP/Azure
- **Graph Neural Networks**, AutoML, reinforcement learning avanzado

### Conclusión del análisis
Soy **intermedio sólido en ML clásico y DL**, con buena base en NLP y XAI. La brecha más grande —y la más valiosa para mi trabajo actual— está en **LLMs, RAG, y arquitectura de agentes**. Justo lo que hago todos los días en Trajectory.

---

## 4. Especialización recomendada

**RAG Systems + LLM Infrastructure Engineer**

Razones:
1. Mi empresa ya opera un RAG en producción — tengo el mejor laboratorio posible
2. Combina NLP (que ya sé), infraestructura (que estoy aprendiendo) y LLMs (el futuro)
3. El mercado demanda esto: cada empresa está construyendo su RAG corporativo
4. Stack 100% Python — sin fricción de herramientas

---

## 5. ¿Por qué un MCP personal?

### El problema
Cada sesión con un asistente de IA empieza de cero. No hay memoria de lo que hice ayer, ni de las decisiones de arquitectura de la semana pasada, ni del contexto de mis proyectos. Mi `COMMIT_RULES.md` es lo más cercano a "contexto persistente", pero es estático.

### La oportunidad
En Trajectory construimos un MCP que le da a Claude acceso a toda la información de una empresa. **Yo no tengo eso para mí mismo.** Orion cierra esa brecha.

### La estrategia
En lugar de otro proyecto genérico de portafolio, Orion es una herramienta que:
- **Uso a diario** — crece orgánicamente y se vuelve indispensable
- **Demuestra lo que hago en el trabajo** — pero en código abierto
- **Me diferencia** — muy pocos ingenieros entienden MCP a profundidad
- **Cierra brechas del bootcamp** — RAG, embeddings, LLMs, arquitectura de agentes

---

## 6. Elección del nombre

La discusión del nombre fue un proceso iterativo guiado por criterios claros:
- Debía ser **sci-fi / futurista** (dirección explícita del autor)
- Debía **escalar**: no solo un nombre, sino un **universo de integraciones**
- Debía ser **llamativo y profesional**

### Opciones descartadas

| Nombre | Motivo del rechazo |
|--------|--------------------|
| Cortex | Genérico, suena a producto que quiere parecer inteligente sin decir nada |
| Exocortex | Demasiado académico, inaccesible para no-médicos |
| second-brain | Trillado (Obsidian, Notion, toda herramienta de notas lo usa) |
| Nova | Corto y con punch, pero no permite ecosistema de sub-nombres |
| Quasar | Potente pero sin cohesión para productos derivados |
| Helix, Synapse | No resonaron con el autor |
| Aura, Photon, Helios | Buenas analogías pero no generan un universo de nombres |

### ¿Por qué Orion?

Orion es una constelación — el cazador. Pero una constelación nunca está sola: el cielo se llena. La decisión clave fue pensar en **un ecosistema de productos con nombre propio y propósito propio**:

```
universo/          ← el firmamento (carpeta raíz)
├── orion/         ← MCP principal. El cazador. Busca, encuentra, conecta.
├── vela/          ← Futuro: despliegue, CI/CD, automatización
├── draco/         ← Futuro: guardián de seguridad, auditoría de accesos
├── lyra/          ← Futuro: visualización, dashboards, métricas
├── ara/           ← Futuro: integraciones externas (GitHub, Jira, Slack, etc.)
└── phoenix/       ← Futuro: backup, resurrección de estado
```

**Ventajas del sistema:**
- **Escala infinito**: hay 88 constelaciones oficiales, el namespace nunca se agota
- **Tema unificado**: astronomía real, no inventada, sci-fi legítimo
- **Personalidad**: Orion "caza" datos, Draco "protege", Phoenix "resucita"
- **Profesional**: suena serio sin ser aburrido
- **Disponible**: no existe otro MCP llamado Orion

---

## 7. Arquitectura del proyecto

### Transporte dual desde el día 1
- **stdio**: compatible con Claude Desktop, VS Code, Neovim
- **HTTP** (`localhost:9099`): compatible con opencode y clientes HTTP

En el trabajo usamos HTTP para multi-usuario. Orion es single-user local pero mantiene ambos transportes para máxima compatibilidad.

### Decisiones de diseño de la Fase 1

| Decisión | Justificación |
|----------|--------------|
| **JSON plano**, no SQLite | Para <100 entradas, JSON es más simple y portable. Migrar cuando escale |
| **Keywords**, no embeddings | Prioridad: esqueleto funcional en 1-2 sesiones. Interfaz no cambia en Fase 2 |
| **Sin autenticación** | Single-user local. Auth cuando se necesite multi-usuario |
| **Dual-transport** | Compatibilidad máxima con todas las herramientas del ecosistema |

### Fases del proyecto

```
Fase 1 — Fundación (AHORA)
├── Servidor MCP mínimo (FastMCP)
├── 2 herramientas: remember_decision, recall_context
├── Almacenamiento JSON plano
└── Búsqueda por keywords

Fase 2 — RAG semántico
├── ChromaDB como vector store
├── sentence-transformers para embeddings
├── Búsqueda semántica real sobre código y docs
└── Misma interfaz, mejor backend

Fase 3 — Knowledge Graph
├── Grafo de conceptos interconectados
├── Herramientas: link_concepts, find_related
└── La IA entiende relaciones, no solo keywords

Fase 4 — Session Memory
├── Resúmenes automáticos de sesiones
├── Contexto persistente entre días
└── La IA recuerda lo que hicimos ayer

Futuro — Nuevas constelaciones
├── Vela — deploy automático
├── Draco — auditoría de accesos
├── Lyra — dashboards y visualización
└── Ara — integraciones externas
```

---

## 8. Lo que voy a aprender con Orion

### Técnico

| Área | Punto de partida | Destino |
|------|-----------------|---------|
| **MCP** | Consumidor (uso Claude con MCP ajeno) | Creador (construyo mi propio servidor desde cero) |
| **RAG** | Teoría del bootcamp (TF-IDF básico) | Implementación real: embeddings, vector store, reranker |
| **LLMs** | Consumo de API externa | Integración local con Ollama, embeddings locales |
| **Arquitectura** | Monolitos (FastAPI simple) | Servicios desacoplados (MCP + RAG como procesos) |
| **Evaluación** | No cubierto en el bootcamp | Métricas de retrieval: precision@k, recall, MRR, NDCG |
| **DevOps** | Básico (Docker, Railway) | systemd, health checks, circuit breakers, warmup |
| **Python** | Intermedio | FastMCP, async patterns, decoradores, type hints avanzados |

### Conceptual
- **De consumidor a creador de infraestructura** — no solo uso herramientas de IA, las construyo
- **Pensar en productos, no en proyectos** — Orion tiene nombre, ecosistema, y está diseñado para crecer
- **Documentar decisiones de diseño** — cada elección técnica tiene un "por qué" escrito
- **Open-source como carta de presentación** — mi trabajo habla por sí mismo

---

## 9. Reglas de trabajo

Estas reglas fueron establecidas en esta sesión y aplican a todo el desarrollo de Orion y del universo:

### Regla 1 — Sin commits automáticos (PROHIBIDO)

Nunca ejecutar `git commit`, `git add`, `git push` ni ninguna mutación del repositorio. Los commits los hace Juan manualmente. El asistente solo redacta el mensaje de commit en el chat siguiendo las reglas de `COMMIT_RULES.md`.

### Regla 2 — Planificación antes de escribir código

Antes de tocar cualquier archivo, el asistente debe presentar un plan con:
- Qué va a hacer (objetivo concreto)
- Por qué lo hace de esa forma (lógica y alternativas consideradas)
- Archivos que va a modificar o crear
- Riesgos o trade-offs que ve

**No se escribe código hasta que Juan apruebe explícitamente el plan.**

### Regla 3 — Pedagogía y pensamiento crítico

- Explicar siempre la lógica detrás de cada decisión técnica. Juan quiere entender el **por qué**, no solo el **qué**.
- Ser crítico con el código: si hay una mejor forma de hacer algo, señalarlo y discutirlo.
- Corregir a Juan si propone algo que va contra buenas prácticas o contra las propias reglas.

### Regla 4 — COMMIT_RULES.md como estándar vivo

Leer `/home/jdvalmart/Documentos/GitHub/COMMIT_RULES.md` al inicio de cada sesión. Si durante el trabajo se identifica una mejora en las reglas (estructura de commits, nuevos tipos, claridad, etc.), proponerla para que el documento evolucione hacia un estándar cada vez más profesional.

### Regla 5 — Comunidad OpenCode

Las reglas aquí definidas aplican para todo el equipo que trabaja con OpenCode en este proyecto.

---

## 10. Flujo de trabajo con Git

### Ramas
```
main          ← siempre deployable, siempre limpia
feature/*     ← una rama por feature/fix
```

Nada de `develop`, `staging`, ni `release/*`. Feature branch → PR → merge a main.

### Pull Requests (aunque trabajes solo)

1. `git checkout -b feature/orion-memory-tools`
2. Trabajar, commits atómicos
3. `git push -u origin feature/orion-memory-tools`
4. `gh pr create --title "..." --body "..."`
5. `gh pr merge --squash`

### Cada proyecto es un repo independiente

- `universo/orion` → `github.com/jdvalmart/orion`
- `pequeletores` → `github.com/jdvalmart/pequeletores`
- etc.

---

## 11. Archivos de la sesión modificados o creados

### Modificados (actualización de perfil)
| Archivo | Cambio |
|---------|--------|
| `perfil.md` | Nuevo rol AI Developer en Trajectory, MCP 140+ tools, enfoque backend/AI |
| `hoja-de-vida.md` | Misma info en formato CV, nueva experiencia |
| `portafolio-jdvalmart/frontend/src/i18n/en.ts` | Hero, about, timeline, stats actualizados |
| `portafolio-jdvalmart/frontend/src/i18n/es.ts` | Ídem en español |
| `portafolio-jdvalmart/frontend/src/data/timeline.ts` | Trajectory Jun 2026, descripción MCP |
| `portafolio-jdvalmart/frontend/src/data/projects.ts` | Nuevo proyecto MCP Corporativo |
| `portafolio-jdvalmart/frontend/src/data/certifications.ts` | Añadida Ing. de Software |
| `portafolio-jdvalmart/frontend/src/data/fallback-responses.json` | Chatbot actualizado |
| `portafolio-jdvalmart/frontend/src/components/Skills.tsx` | MCP añadido, AI/Backend primero |
| `portafolio-jdvalmart/frontend/src/pages/Cv.tsx` | Experiencia Trajectory, datos corregidos |
| `portafolio-jdvalmart/frontend/src/pages/About.tsx` | Meta tags actualizados |
| `portafolio-jdvalmart/frontend/src/pages/Home.tsx` | Meta tags actualizados |

### Creados (proyecto Orion)
```
universo/orion/
├── ACTA.md              ← este documento
├── PLAN.md              ← plan técnico de la Fase 1
├── README.md            ← documentación de uso
├── server.py            ← FastMCP entrypoint, dual-transport
├── orion_config.py      ← configuración centralizada
├── requirements.txt     ← dependencias
├── .gitignore
├── tools/
│   ├── __init__.py
│   └── memory.py        ← remember_decision + recall_context
└── data/                ← gitignored
```

---

*Documento fundacional del proyecto Orion. Leer antes de cualquier contribución.*
