# Codebase Structure

**Analysis Date:** 2026-04-13
**Last update:** 2026-05-04

## Atualizacao 2026-05-04

A estrutura passou a incluir a camada de governanca da consultoria por simulacao:

- `report_system_gate.py` bloqueia relatorio sem simulacao/evidencia suficiente.
- `social_bootstrap.py` planeja o pulso social inicial auditavel.
- `report_quality.py` audita citacoes diretas e renderiza bloco de evidencia.
- `simulation_data_reader.py` mede diversidade semantica, agentes, plataformas e trace OASIS.
- Step 3 e Step 4 no frontend agora fazem parte da governanca, nao apenas da exibicao.

## Directory Layout

```
mirofish-inteia/
├── backend/                          # Python Flask backend
│   ├── app/
│   │   ├── __init__.py              # Flask app factory
│   │   ├── config.py                # Centralized configuration (env vars, defaults)
│   │   ├── api/                     # Flask blueprints (HTTP endpoints)
│   │   │   ├── __init__.py          # Blueprint registration
│   │   │   ├── graph.py             # /api/graph/* (ontology, graph building)
│   │   │   ├── simulation.py        # /api/simulation/* (preparation, execution, quality)
│   │   │   ├── report.py            # /api/report/* (generation, interaction, artifacts)
│   │   │   └── internal.py          # /api/internal/v1/* (internal service API)
│   │   ├── models/                  # Data classes, state management
│   │   │   ├── project.py           # Project state, persistence
│   │   │   └── task.py              # Task tracking for async operations
│   │   ├── services/                # Business logic, workflow engines
│   │   │   ├── ontology_generator.py       # Step 1: LLM-based ontology design
│   │   │   ├── graph_builder.py            # Step 2a: Graphiti graph construction
│   │   │   ├── apify_enricher.py           # Step 2 integration: Web scraping
│   │   │   ├── oasis_profile_generator.py  # Step 2b: Agent profile generation
│   │   │   ├── simulation_config_generator.py # Step 2c: Simulation parameters
│   │   │   ├── zep_entity_reader.py        # Graph entity filtering and enrichment
│   │   │   ├── llm_entity_extractor.py     # Entity type extraction from text
│   │   │   ├── text_processor.py           # Text chunking, preprocessing
│   │   │   ├── simulation_manager.py       # Step 3: Simulation orchestration
│   │   │   ├── simulation_runner.py        # Step 3: Parallel OASIS execution
│   │   │   ├── simulation_ipc.py           # Inter-process communication for runners
│   │   │   ├── simulation_data_reader.py   # Read simulation output, diversity and OASIS trace
│   │   │   ├── social_bootstrap.py         # Initial social pulse planning
│   │   │   ├── report_system_gate.py       # Structural report delivery gate
│   │   │   ├── report_agent.py             # Step 4: gated report generation
│   │   │   ├── zep_tools.py                # Report agent tools (search, insight, interview)
│   │   │   ├── zep_graph_memory_updater.py # Update graph with simulation memory
│   │   │   └── __init__.py
│   │   ├── utils/                   # Infrastructure, HTTP clients, helpers
│   │   │   ├── llm_client.py        # Unified LLM client (OpenAI/OmniRoute compatible)
│   │   │   ├── graphiti_client.py   # REST client for Graphiti Server
│   │   │   ├── logger.py            # Logging setup and management
│   │   │   ├── file_parser.py       # PDF, Markdown, TXT parsing
│   │   │   ├── token_tracker.py     # LLM token usage tracking
│   │   │   ├── retry.py             # Retry decorators and logic
│   │   │   ├── report_quality.py    # Direct quote/evidence audit
│   │   │   └── __init__.py
│   │   └── __pycache__              # Python compiled cache (ignored in git)
│   ├── autoresearch/                # Auto-research/optimization tools (experimental)
│   │   ├── cli.py                   # CLI entry point for auto-research
│   │   ├── engine.py                # Research execution engine
│   │   ├── cost_guard.py            # Budget management
│   │   ├── git_ops.py               # Git integration for experiments
│   │   ├── experiment_log.py        # Experiment tracking
│   │   ├── targets/                 # Optimization targets
│   │   │   ├── base.py              # Base target class
│   │   │   ├── frontend_perf.py     # Frontend performance optimization
│   │   │   ├── genetic_copy.py      # Genetic algorithm copy optimization
│   │   │   ├── hookify_rules.py     # Hookify rules optimization
│   │   │   ├── skill_prompt.py      # Skill prompt optimization
│   │   │   └── __init__.py
│   │   ├── corpora/                 # Training data for optimization
│   │   ├── results/                 # Optimization results
│   │   └── __init__.py
│   ├── scripts/                     # Utility scripts
│   │   ├── action_logger.py         # Log simulation actions
│   │   └── enrich_project.py        # CLI for Apify enrichment
│   ├── tests/                       # Test suite
│   ├── run.py                       # Backend entry point
│   ├── pyproject.toml               # Python project metadata, dependencies
│   ├── requirements.txt             # Pinned dependencies (fallback)
│   ├── .python-version              # Python version for uv
│   └── uploads/                     # File storage (created at runtime)
│       ├── simulations/             # Simulation output snapshots
│       └── reports/                 # Generated reports
│
├── frontend/                        # Vue.js 3 frontend
│   ├── src/
│   │   ├── main.js                  # Vue app entry point
│   │   ├── App.vue                  # Root Vue component
│   │   ├── api/                     # Axios client and API methods
│   │   │   ├── index.js             # Axios instance, request/response interceptors
│   │   │   ├── graph.js             # /api/graph/* method wrappers
│   │   │   ├── simulation.js        # /api/simulation/* method wrappers
│   │   │   └── report.js            # /api/report/* method wrappers
│   │   ├── router/
│   │   │   └── index.js             # Vue Router configuration, routes
│   │   ├── store/
│   │   │   └── pendingUpload.js     # Reactive state for pending file uploads
│   │   ├── views/                   # Page-level components
│   │   │   ├── Home.vue             # Landing page, project creation
│   │   │   ├── MainView.vue         # Workflow main page (Steps 1–2)
│   │   │   ├── Process.vue          # [Deprecated] Legacy process view
│   │   │   ├── SimulationView.vue   # Step 2b: Simulation config UI
│   │   │   ├── SimulationRunView.vue # Step 3: Live simulation progress
│   │   │   ├── ReportView.vue       # Step 4: Report display
│   │   │   └── InteractionView.vue  # Step 5: Agent Q&A interface
│   │   ├── components/              # Reusable UI components
│   │   │   ├── Step1GraphBuild.vue  # Workflow step 1 UI
│   │   │   ├── Step2EnvSetup.vue    # Workflow step 2a UI
│   │   │   ├── Step3Simulation.vue  # Workflow step 3 UI + quality gate
│   │   │   ├── Step4Report.vue      # Workflow step 4 UI + evidence custody
│   │   │   ├── Step5Interaction.vue # Workflow step 5 UI
│   │   │   ├── GraphPanel.vue       # Knowledge graph visualization (D3)
│   │   │   └── HistoryDatabase.vue  # Project history view
│   │   ├── assets/                  # Static images, logos
│   │   │   └── logo/
│   │   └── styles/                  # [If present] Global CSS
│   ├── public/                      # Static files (copied to dist/ on build)
│   │   └── icon.png
│   ├── index.html                   # HTML template (entry point)
│   ├── vite.config.js               # Vite dev server config, Vue plugin, API proxy
│   ├── package.json                 # Frontend dependencies, build scripts
│   ├── package-lock.json            # Lockfile for npm
│   ├── dist/                        # Built frontend (created on `npm run build`)
│   └── node_modules/                # Installed npm packages (gitignored)
│
├── deploy/                          # Deployment configurations
│   └── [deployment-specific files]
│
├── tools/                           # Utility scripts (if present)
├── static/                          # Static assets
│
├── .github/                         # GitHub workflows/metadata
├── .gstack/                         # GStack automation config
├── .planning/                       # GSD planning documents
│   └── codebase/                    # Codebase analysis (this directory)
│       ├── STACK.md                 # Technology stack
│       ├── INTEGRATIONS.md          # External services
│       ├── ARCHITECTURE.md          # System architecture
│       └── STRUCTURE.md             # This file
│
├── .env                             # Environment variables (gitignored, local-only)
├── .env.example                     # Template for .env
├── .gitignore                       # Git ignore rules
├── docker-compose.yml               # Docker service orchestration
├── Dockerfile                       # Multi-stage Docker build
├── .dockerignore                    # Docker build ignore rules
│
├── package.json                     # Root npm scripts (setup, dev, build)
├── package-lock.json                # Root npm lockfile
│
├── README.md                        # Project documentation
├── README-EN.md                     # English version of README
├── LICENSE                          # AGPL-3.0 license
│
├── PRD_MIROFISH_INTEIA_V2.md        # Product Requirements Document
├── BACKLOG_TECNICO_*.md             # Technical backlog
├── PLANO_ADAPTACAO_*.md             # Adaptation plan (fork changes)
├── LENIA_MIROFISH_INTEGRACAO.md     # Integration with Lenia (electoral system)
├── MAPEAMENTO_PT-BR.md              # Portuguese-BR translation mapping
│
└── [Supporting files and scripts]
```

## Directory Purposes

**backend/app/api:**
- Purpose: HTTP request handlers (Flask blueprints)
- Contains: Route definitions, request parsing, response formatting
- Key files: `graph.py` (Steps 1–2), `simulation.py` (Steps 2–3), `report.py` (Step 4), `internal.py` (service API)

**backend/app/services:**
- Purpose: Workflow engines and business logic
- Contains: Ontology generation, graph building, simulation orchestration, report generation
- Key files: Each service is a single workflow step or utility (see diagram in ARCHITECTURE.md)
- Delivery-governance files: `report_system_gate.py`, `simulation_data_reader.py`, `social_bootstrap.py`, `report_agent.py`

**backend/app/models:**
- Purpose: Data classes and state management
- Contains: Project, Task, SimulationState dataclasses with persistence logic
- Key files: `project.py`, `task.py`

**backend/app/utils:**
- Purpose: Infrastructure and HTTP clients
- Contains: LLM client (OpenAI/OmniRoute), Graphiti client, logging, file parsing
- Key files: `llm_client.py`, `graphiti_client.py`, `logger.py`
- Report evidence helper: `report_quality.py`

**frontend/src/views:**
- Purpose: Page-level components (one per major workflow step)
- Contains: Vue components that manage workflow progress
- Key files: MainView.vue (Steps 1–2 summary), SimulationRunView.vue (Step 3 progress), ReportView.vue (Step 4), InteractionView.vue (Step 5)

**frontend/src/components:**
- Purpose: Reusable UI components for workflow steps
- Contains: Step-specific UI panels, graph visualization, history
- Key files: Step1GraphBuild.vue through Step5Interaction.vue

**frontend/src/api:**
- Purpose: Axios HTTP client and API method wrappers
- Contains: API method definitions (`generateOntology()`, `buildGraph()`, `startSimulation()`, etc.)
- Key files: `index.js` (axios setup), `graph.js`, `simulation.js`, `report.js`

**backend/uploads/:**
- Purpose: Runtime file storage (created at first run)
- Contains: Uploaded documents, simulation snapshots, generated reports
- Structure: `simulations/{sim_id}/`, `reports/{report_id}/`
- Audit artifacts: `reports/{report_id}/system_gate.json`, `evidence_manifest.json`, `evidence_audit.json`

## Key File Locations

**Entry Points:**
- `backend/run.py` - Backend server startup, config validation
- `frontend/src/main.js` - Vue app initialization
- `backend/app/__init__.py` - Flask app factory (create_app)

**Configuration:**
- `backend/app/config.py` - Centralized config (env vars, defaults)
- `frontend/vite.config.js` - Frontend dev server proxy, plugin setup
- `docker-compose.yml` - Service orchestration for Docker
- `.env.example` - Environment variable template

**Core Logic:**
- `backend/app/services/ontology_generator.py` - LLM-based ontology design
- `backend/app/services/graph_builder.py` - Graphiti graph construction
- `backend/app/services/simulation_manager.py` - Simulation orchestration
- `backend/app/services/report_agent.py` - Report generation with gate/audit artifacts
- `backend/app/services/report_system_gate.py` - Structural delivery gate
- `backend/app/services/social_bootstrap.py` - Deterministic social interaction bootstrap

**Testing:**
- `backend/tests/` - Test suite, 70 tests passing on 2026-05-04

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `llm_client.py`, `graph_builder.py`)
- Vue components: `PascalCase.vue` (e.g., `GraphPanel.vue`, `Step1GraphBuild.vue`)
- JavaScript utilities: `camelCase.js` (e.g., `pendingUpload.js`)

**Directories:**
- Python: `snake_case` (e.g., `app/`, `services/`, `utils/`)
- Frontend: `lowercase` (e.g., `views/`, `components/`, `api/`)

**Functions/Methods:**
- Python: `snake_case()` (e.g., `build_graph_async()`, `get_entity_with_context()`)
- JavaScript: `camelCase()` (e.g., `generateOntology()`, `requestWithRetry()`)

**Classes/Types:**
- Python: `PascalCase` (e.g., `OntologyGenerator`, `SimulationState`, `FilteredEntities`)
- JavaScript: `PascalCase` for Vue components, lowercase for utilities

**Constants:**
- Python: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CHUNK_SIZE`, `ALLOWED_EXTENSIONS`)
- JavaScript: `camelCase` or `UPPER_SNAKE_CASE` (mixed convention)

## Where to Add New Code

**New Feature (Example: Add a new enrichment source):**
- Primary code: `backend/app/services/apify_enricher.py` (add new profile, API calls)
- API endpoint: `backend/app/api/simulation.py` (add enrichment parameter)
- Frontend: `frontend/src/components/Step2EnvSetup.vue` (add UI for new source)
- Tests: `backend/tests/test_apify_enricher.py`

**New Component/Module (Example: Add AI conversation history feature):**
- Implementation: `backend/app/services/chat_history_manager.py` (new service)
- API: `backend/app/api/report.py` (new endpoint `/api/report/history`)
- Frontend view: `frontend/src/views/ChatHistoryView.vue`
- Frontend API client: `frontend/src/api/report.js` (add `getChatHistory()` method)

**Utilities (Example: Add a new metric calculator):**
- Shared helpers: `backend/app/utils/metrics.py` (new utility module)
- Import in services: `from ..utils.metrics import calculate_engagement_score`

**API Endpoint (Example: Add new graph query):**
- Handler: `backend/app/api/graph.py` (add `@graph_bp.route()`)
- Service: Create or extend service in `backend/app/services/`
- Client: `frontend/src/api/graph.js` (add wrapper function)

## Special Directories

**backend/uploads/:**
- Purpose: File storage for uploaded documents, simulations, reports
- Generated: Yes (created at first request)
- Committed: No (gitignored)

**frontend/dist/:**
- Purpose: Production build output
- Generated: Yes (`npm run build` in frontend/)
- Committed: No (gitignored, built in Docker)

**backend/.venv/ or .venv/:**
- Purpose: Python virtual environment (if using venv instead of uv)
- Generated: Yes
- Committed: No (gitignored)

**frontend/node_modules/:**
- Purpose: npm dependencies
- Generated: Yes (`npm install`)
- Committed: No (gitignored)

**backend/autoresearch/:**
- Purpose: Experimental auto-research/optimization tools
- Generated: No
- Committed: Yes (but may be WIP/unused)

**backend/scripts/:**
- Purpose: CLI utility scripts (not part of main app)
- Generated: No
- Committed: Yes
- Examples: `enrich_project.py` (CLI for enrichment)

---

*Structure map updated: 2026-05-04*
