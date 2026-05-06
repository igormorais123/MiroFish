# Architecture

**Analysis Date:** 2026-04-13
**Last update:** 2026-05-04

## Atualizacao 2026-05-04

O pipeline ganhou uma camada explicita de governanca: relatorio cliente so e entregue se a simulacao produzir evidencia auditavel. Essa camada cruza projeto, grafo, perfis, config, run_state, logs, trace OASIS, diversidade e auditoria de citacoes.

## Pattern Overview

**Overall:** Microservice-style monolith with separation of concerns: frontend (Vue SPA), backend API (Flask), external services (LLM, graph memory, web scraping)

**Key Characteristics:**
- Request-response REST API with long-running async tasks (polling model)
- Server-side state persistence (project, task, simulation context)
- Multi-stage processing pipeline (ontology → graph → simulation → report)
- Independent service components (Graphiti, LLM providers, Apify) via HTTP/REST
- Social simulation engine (OASIS) embedded in backend
- No database persistence (state in JSON, uploads on disk)
- Hard delivery gate and delivery governance before report publication
- Evidence artifacts persisted beside each report

## Layers

**Presentation Layer:**
- Location: `frontend/src/`
- Contains: Vue 3 SPA with components, views, router, store
- Depends on: REST API (`/api/*`), axios HTTP client
- Used by: End users via browser

**API Layer:**
- Location: `backend/app/api/`
- Contains: Flask blueprints (`graph.py`, `simulation.py`, `report.py`, `internal.py`)
- Depends on: Services layer, config, logging
- Responsibilities: HTTP request routing, input validation, CORS, response formatting

**Services Layer:**
- Location: `backend/app/services/`
- Contains: Business logic for each workflow stage
- Key services:
  - `ontology_generator.py` - Analyzes text, generates entity/relation types via LLM
  - `graph_builder.py` - Calls Graphiti to construct knowledge graph
  - `simulation_manager.py` - Orchestrates OASIS simulation execution
  - `simulation_runner.py` - Parallel execution of Twitter/Reddit simulations
  - `report_system_gate.py` - Structural gate for report delivery
  - `delivery_governance.py` - Client vs demo/smoke publishability policy
  - `social_bootstrap.py` - Deterministic first interaction pulse for OASIS
  - `report_agent.py` - Multi-round report generation with evidence audit
  - `apify_enricher.py` - Web scraping and data enrichment
  - `zep_tools.py` - Tools for report agent (search, insight forging, interviews)

**Models/Data Layer:**
- Location: `backend/app/models/`
- Contains: Data classes, state management
  - `project.py` - Project state (files, ontology, graph info)
  - `task.py` - Task tracking (async operation state)

**Utilities/Infrastructure:**
- Location: `backend/app/utils/`
- Contains: HTTP clients, logging, retry logic, token tracking
  - `llm_client.py` - Unified LLM client (OpenAI-compatible, OmniRoute-aware)
  - `graphiti_client.py` - Graphiti REST API wrapper
  - `logger.py` - Centralized logging setup
  - `retry.py` - Retry decorators
  - `token_tracker.py` - LLM token consumption tracking

## Data Flow

**Step 1: Ontology Generation (Interface 1)**

1. User uploads PDF/Markdown files + specifies simulation requirement
2. Frontend calls `POST /api/graph/ontology/generate` (multipart FormData)
3. Backend:
   - Parses files using `FileParser` (PyMuPDF for PDFs)
   - Sends text + requirement to LLM via `LLMClient`
   - LLM generates JSON schema (entity types, relation types, attributes)
   - Stores ontology in `ProjectManager` state
4. Frontend receives `project_id`, `ontology`, `analysis_summary`

**Step 2: Graph Building (Interface 2)**

1. User reviews ontology, optionally runs Apify enrichment
2. Frontend calls `POST /api/graph/build` with `project_id`
3. Backend:
   - Applies Apify enrichment if requested (Google, Instagram, YouTube data)
   - Chunks text using `TextProcessor` (configurable chunk_size, overlap)
   - Calls `GraphBuilderService.build_graph_async()` which spawns background thread
   - Thread calls Graphiti REST API to construct graph incrementally
   - Stores `graph_id`, task status in project state
4. Frontend polls `GET /api/graph/task/{task_id}` until completion
5. Returns knowledge graph with nodes (entities), edges (relations)

**Step 3: Environment Setup & Simulation Config (Interface 2b)**

1. User customizes simulation environment
2. Frontend calls `POST /api/simulation/prepare` with:
   - Enrich options (actor handles, queries, YouTube links)
   - Platform toggles (Twitter, Reddit)
   - Profile mode (lean/full/batch)
3. Backend:
   - Reads entities from Graphiti via `ZepEntityReader`
   - Calls Apify for profile/post enrichment (if enabled)
   - Generates OASIS agent profiles via `OasisProfileGenerator`
   - Generates simulation parameters via `SimulationConfigGenerator`
   - Returns profiles, actions, initial context
4. Frontend displays config summary

**Step 4: Simulation Execution (Interface 3)**

1. User starts simulation with round count
2. Frontend calls `POST /api/simulation/start` with `simulation_id`, rounds
3. Backend:
   - Creates `SimulationState` in `SimulationManager`
   - Spawns parallel processes via `SimulationRunner` (Twitter + Reddit)
   - Each process:
     - Calls OASIS to initialize agents with profiles
     - Runs simulation for N rounds
     - Publishes initial posts
     - Executes a configurable social bootstrap (comments, likes/dislikes, reposts, quotes)
     - Agents take actions (create post, comment, etc.) based on LLM reasoning
     - Memory updated via `ZepGraphMemoryUpdater`
     - Saves round snapshots to disk
4. Frontend polls `GET /api/simulation/{simulation_id}/status` for progress
5. Simulation completes when all rounds finished
6. Frontend/API can query `/api/simulation/{simulation_id}/quality` before report generation

**Step 5: Report Generation (Interface 4)**

1. User clicks "Generate Report" or asks question
2. Frontend calls `POST /api/report/generate` with report intent, graph_id, simulation_id
3. Backend:
   - Runs `report_system_gate.assert_report_system_ready()`
   - Resolves `delivery_governance` so demo/smoke reports are diagnostic-only
   - Returns 409 if evidence/simulation quality is insufficient
   - Initializes `ReportAgent` only after gate context exists
   - Agent executes ReACT loop (Reason → Act → Observe):
     - Calls tools: `search_entities()`, `insight_forge()`, `panorama()`, `interview_agents()`
     - LLM generates report sections (intro, analysis, predictions, etc.)
     - Each section goes through multiple reflection rounds
   - Direct quotes and numeric claims are audited against local evidence
   - `system_gate.json`, `evidence_manifest.json` and `evidence_audit.json` are persisted
   - Logs all actions to `agent_log.jsonl` for debugging
   - Returns report only if status is compatible with delivery rules
4. Frontend displays report and evidence custody; legacy reports are marked non-publicable

**Step 6: Interaction (Interface 5)**

1. User asks question about simulation/agents
2. Frontend calls `POST /api/report/interview` with query, agent_id, report_id
3. Backend:
   - Fetches agent memory from graph
   - Calls OASIS agent with memory context
   - Agent responds based on personality + memory
4. Frontend displays Q&A transcript

**State Management:**
- Server-side: `ProjectManager`, `TaskManager`, `SimulationManager` hold state in memory
- Persistence: State saved to `projects_state.json`, `tasks_state.json`, `simulations_state.json`
- Disk artifacts: Uploaded files → `/uploads`, graph snapshots → `/uploads/simulations/{sim_id}`, reports → `/uploads/reports/{report_id}`
- Client-side: Vue reactive state, router params, local storage for UI state

## Key Abstractions

**Project:**
- Purpose: Container for a complete analysis (files, ontology, graph)
- Examples: `backend/app/models/project.py`
- Pattern: Immutable metadata + mutable state (status, graph_id)

**Task:**
- Purpose: Track async operations (graph building, simulation)
- Examples: `backend/app/models/task.py`
- Pattern: Status enum (created → queued → running → completed/failed)

**SimulationState:**
- Purpose: Encapsulate entire simulation context
- Examples: `backend/app/services/simulation_manager.py` (SimulationState dataclass)
- Pattern: Dataclass with status, round count, platform flags, error handling
- Current behavior: synchronized from runner `run_state.json` to avoid API/report disagreement

**Report System Gate:**
- Purpose: Block report generation when the system has insufficient evidence
- Examples: `backend/app/services/report_system_gate.py`
- Pattern: Fail-closed validation with structured metrics and issues

**Delivery Governance:**
- Purpose: Separate client/publicable delivery from internal diagnostic runs
- Examples: `backend/app/services/delivery_governance.py`
- Pattern: Unknown modes fall back to strict `client`; `demo/smoke` always returns non-publicable policy

**Evidence Audit:**
- Purpose: Prove direct quotes, numeric claims and local evidence support report text
- Examples: `backend/app/utils/report_quality.py`
- Pattern: Extract direct quotes and numeric claims, match against evidence corpus, mark unsupported claims; numeric inference must be labeled

**OasisAgentProfile:**
- Purpose: Agent definition for OASIS simulation
- Examples: `backend/app/services/oasis_profile_generator.py`
- Pattern: Personality traits, actions, memory hooks, platform-specific behaviors

**FilteredEntities:**
- Purpose: Structured graph data for simulation
- Examples: `backend/app/services/zep_entity_reader.py` (FilteredEntities dataclass)
- Pattern: Type-aware entity filtering with edge enrichment

## Entry Points

**API Entry:**
- Location: `backend/run.py`
- Triggers: `npm run backend` or Docker entrypoint
- Responsibilities: Flask app initialization, config validation, CORS setup, blueprint registration

**Frontend Entry:**
- Location: `frontend/src/main.js`
- Triggers: `npm run dev` or built `dist/index.html` in production
- Responsibilities: Vue app creation, router setup, initial render

**Simulation Entry:**
- Location: `backend/app/api/simulation.py` → `POST /api/simulation/start`
- Triggers: User clicks "Start Simulation"
- Responsibilities: Spawn parallel worker processes, manage lifecycle

## Error Handling

**Strategy:** Try-catch-log-return pattern with graceful degradation

**Patterns:**
1. Validation errors → 400 Bad Request with `error` field
2. Resource not found → 404 with descriptive message
3. Server errors → 500 with error traceback (in development)
4. LLM failures → Retry logic (configurable `LLM_MAX_RETRIES`)
5. Graphiti unavailable → Fail fast (retry minimal, 1 attempt by default)
6. Apify failures → Warn and continue (enrichment is optional)
7. Network timeouts → Configurable per-service timeout (LLM 90s, Graphiti 60s)

**Frontend error handling:**
- Axios interceptor catches HTTP errors, logs to console
- Re-raise for view-level handling (modals, notifications)
- Retry logic with exponential backoff for transient failures

## Cross-Cutting Concerns

**Logging:**
- Approach: Centralized `get_logger()` per module
- Output: Console (development), can be redirected to files
- Levels: DEBUG (development), INFO (progress), WARNING (issues), ERROR (failures)
- Special: Report agent logs to `agent_log.jsonl` (detailed action tracking)

**Validation:**
- Approach: Pydantic models for API input/output, manual checks in services
- Config validation: `Config.validate()` called at startup
- File upload: Extension whitelist (`ALLOWED_EXTENSIONS`)
- LLM model names: Alias resolution via `Config.resolve_model_name()`
- Report delivery: hard gate plus delivery governance, quote audit and numeric audit in `report_system_gate.py`, `delivery_governance.py` and `report_quality.py`

**Authentication:**
- Approach: None for user-facing API (open access)
- Service-to-service: `INTERNAL_API_TOKEN` for `/api/internal/v1` endpoints
- CORS: Origin-based filtering (configurable via `CORS_ORIGINS`)

**Performance:**
- Request timeout: Configurable per-service (LLM 90s, Graphiti 60s)
- Async task polling: Frontend polls every N seconds (adaptive based on task type)
- Streaming: Not used (long-running tasks are polled)
- Caching: Apify enrichment cached to disk per project
- Parallel execution: Simulations run Twitter + Reddit in parallel via multiprocessing

---

*Architecture map updated: 2026-05-04*
