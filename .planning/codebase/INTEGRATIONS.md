# External Integrations

**Analysis Date:** 2026-04-13
**Last update:** 2026-05-04

## APIs & External Services

**LLM / Model APIs:**
- OpenAI (or compatible) - Primary inference for ontology, report generation, entity extraction
  - SDK/Client: `openai` package (v1.0.0+), but code uses `requests` directly for OmniRoute compatibility
  - Auth: `LLM_API_KEY` (env var), optional fallback `OMNIROUTE_API_KEY`
  - Config: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`
  - Models: `haiku-tasks` (agents), `sonnet-tasks` (reports/ontology), `opus-tasks` (Helena Strategos)

- OmniRoute (INTEIA internal gateway) - Cost-optimized LLM routing
  - Gateway URL: `OMNIROUTE_URL` (env var)
  - Auth: `OMNIROUTE_API_KEY`
  - Endpoint: `/v1/chat/completions` (OpenAI-compatible)

**Knowledge Graph / Memory:**
- Graphiti Server - Temporal memory graph backend
  - Client: `GraphitiClient` (`backend/app/utils/graphiti_client.py`)
  - Base URL: `GRAPHITI_BASE_URL` (default: `http://localhost:8003`)
  - Timeout: `GRAPHITI_TIMEOUT` (default: 60s)
  - REST endpoints: `/graphs/{graph_id}/nodes`, `/graphs/{graph_id}/edges`, `/graphs/{graph_id}/query`

**OASIS Local Simulation Databases:**
- SQLite files generated per simulation/platform in `backend/uploads/simulations/{simulation_id}/`
- Expected files: `twitter_simulation.db`, `reddit_simulation.db`
- Key tables for audit: `trace`, `post`, `comment`, `like`, `dislike`, `follow`
- Used by: `simulation_data_reader.py`, `run_parallel_simulation.py`, report gate
- Purpose: prove that social actions were persisted by OASIS, not invented by the report layer

**Web Scraping & Enrichment:**
- Apify - Data enrichment from web (Google SERP, Instagram, YouTube)
  - Client: Custom `ApifyClient` wrapper (`backend/app/services/apify_enricher.py`)
  - Auth: `APIFY_TOKEN` (loaded from `C:/Users/IgorPC/Colmeia/scripts/apify_client.py`)
  - Profiles: `lean` (low cost), `full` (complete), `batch` (municipal scale)
  - Sources: Google SERP, Instagram profiles/posts/tagged, YouTube comments
  - Budget guard: Prevents overspend (90–95% threshold configurable)
  - Cache: Disk-based cache to avoid reprocessing

## Data Storage

**Databases:**
- Not detected - No persistent SQL/NoSQL database configured
- State is persisted to disk as JSON files

**File Storage:**
- Local filesystem at `backend/uploads/`
  - Subdirectories: `simulations/`, `reports/`
  - Max upload size: 50MB (`Config.MAX_CONTENT_LENGTH`)
  - Allowed file types: PDF, Markdown, TXT (`Config.ALLOWED_EXTENSIONS`)
  - Report audit artifacts: `system_gate.json`, `evidence_manifest.json`, `evidence_audit.json`

**In-Memory State:**
- Server-side project/task state stored in memory during session
- Persisted to disk as JSON (`projects_state.json`, `tasks_state.json`)
- Used for context between API calls without large frontend-backend transfers

**Caching:**
- Apify enrichment: Disk cache (`_cache_path` in `apify_enricher.py`)
- No Redis or Memcached detected

## Authentication & Identity

**Auth Provider:**
- Custom/None - No user authentication system detected
- Service-to-service: `INTERNAL_API_TOKEN` (env var) for internal API calls

**CORS Configuration:**
- `CORS_ORIGINS` env var (default: `*`)
- Restricted to `/api/*` routes in production

## Monitoring & Observability

**Error Tracking:**
- Not detected - No Sentry, Rollbar, or similar configured

**Logs:**
- File-based: `backend/app/utils/logger.py` (Python logging)
- Uses standard Python `logging` module with custom setup
- Log output: Console (development), can be redirected to files
- Report Agent logs: `reports/{report_id}/agent_log.jsonl` (JSONL format, detailed action tracking)

**Debugging:**
- Flask debug mode enabled via `FLASK_DEBUG` env var (default: True)
- Werkzeug debugger available in development

## CI/CD & Deployment

**Hosting:**
- Docker (primary method)
- VPS deployment via docker-compose
- Supports GitHub Container Registry (ghcr.io/666ghj/mirofish)

**CI Pipeline:**
- Not detected - No GitHub Actions, GitLab CI, or similar configured
- Manual Docker build required

**Deployment:**
- Multi-stage Docker build:
  1. Frontend stage: Node 20 + Vite (builds to `frontend/dist`)
  2. Python stage: Python 3.12-slim + nginx + uv
  3. nginx reverse proxy serves frontend + proxies `/api/*` to Flask backend (port 5001)
- Entry point: `/app/start.sh` (launches Flask backend in background, then nginx)
- Exposed port: 80 (HTTP only in compose, requires reverse proxy for HTTPS)

## Environment Configuration

**Required env vars:**
- `LLM_API_KEY` or `OMNIROUTE_API_KEY` - LLM authentication (mandatory)
- `GRAPHITI_BASE_URL` - Graph memory service URL (mandatory)
- `INTERNAL_API_TOKEN` - Internal service communication (recommended)

**Optional env vars:**
- `LLM_BASE_URL` - Default: `https://api.openai.com/v1`
- `LLM_MODEL_NAME` - Default: `gpt-4o-mini` (OpenAI) or `haiku-tasks` (OmniRoute)
- `LLM_TIMEOUT_SECONDS` - Default: 90
- `LLM_MAX_RETRIES` - Default: 3
- `OMNIROUTE_URL` - OmniRoute gateway base URL (if using OmniRoute)
- `GRAPHITI_TIMEOUT` - Default: 60
- `OASIS_DEFAULT_MAX_ROUNDS` - Default: 10 (simulation rounds)
- `FLASK_DEBUG` - Default: True
- `FLASK_HOST` - Default: 0.0.0.0
- `FLASK_PORT` - Default: 5001
- `APIFY_TOKEN` - Apify account token (for enrichment, optional)
- `REPORT_MIN_ACTIONS` - minimum real actions before report delivery
- `REPORT_REQUIRE_COMPLETED_SIMULATION` - require completed `run_state`
- `REPORT_REQUIRE_SOURCE_TEXT` - require project/source text evidence
- `REPORT_FAIL_ON_UNSUPPORTED_QUOTES` - fail closed on unsupported direct quotes
- `REPORT_MIN_DISTINCT_2` - minimum semantic diversity
- `REPORT_MIN_AGENT_ACTIVITY_ENTROPY` - minimum agent participation diversity
- `REPORT_MIN_BEHAVIOR_ENTROPY` - minimum OASIS behavioral diversity
- `REPORT_REQUIRE_ACTION_TYPE_DIVERSITY` - require more than one useful action type

**Simulation config additions:**
- `social_dynamics.bootstrap_enabled`
- `social_dynamics.bootstrap_max_actions`
- `social_dynamics.twitter_bootstrap_action_mix`
- `social_dynamics.reddit_bootstrap_action_mix`

**Secrets location:**
- `.env` file (root of project, not committed)
- Environment variables in container runtime
- Windows: Colmeia scripts path `C:/Users/IgorPC/Colmeia/scripts/apify_client.py` (contains Apify integration)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

---

*Integration map updated: 2026-05-04*
