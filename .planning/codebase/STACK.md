# Technology Stack

**Analysis Date:** 2026-04-13

## Languages

**Primary:**
- Python 3.11–3.12 - Backend (Flask, OASIS simulation, LLM integration)
- JavaScript (ES6+) - Frontend (Vue.js 3 runtime)
- Node.js 18+ - Frontend build tooling

**Secondary:**
- Bash - Deployment scripts, Docker entrypoint
- SQL - Optional (no persistent DB detected; state persisted to disk/JSON)

## Runtime

**Environment:**
- Python 3.12 (Docker) / 3.11–3.12 (development)
- Node.js 20+ (frontend, build-time)
- Docker 20.10+ (containerization)

**Package Manager:**
- Python: `uv` (managed via pyproject.toml), fallback `pip`
- JavaScript: `npm` (lockfile: `package-lock.json` present in root and frontend/)

## Frameworks

**Core:**
- Flask 3.0.0+ - HTTP API framework, request handling, CORS
- Vue.js 3.5.24 - Frontend component framework, reactive UI
- Vite 7.2.4 - Frontend build tool, dev server with HMR

**Testing:**
- pytest 8.0.0+ - Python test runner
- pytest-asyncio 0.23.0+ - Async test support

**Build/Dev:**
- @vitejs/plugin-vue 6.0.1 - Vue SFC compilation in Vite
- concurrently 9.1.2 - Parallel npm script execution (dev mode)

## Key Dependencies

**Critical:**
- openai 1.0.0+ - LLM client (OpenAI-compatible API)
- camel-ai 0.2.78 - CAMEL agent framework
- camel-oasis 0.2.5 - OASIS social simulation engine
- flask-cors 6.0.0 - Cross-origin resource sharing
- pydantic 2.0.0 - Data validation, configuration management

**Infrastructure:**
- python-dotenv 1.0.0 - Environment variable loading
- PyMuPDF 1.24.0+ - PDF parsing and text extraction
- charset-normalizer 3.0.0+ - Text encoding detection
- chardet 5.0.0+ - Character encoding detection (fallback)
- requests - HTTP client (used in llm_client.py for LLM calls instead of OpenAI SDK)

**Frontend:**
- axios 1.13.2+ - HTTP client for API communication
- d3 7.9.0+ - Graph visualization (knowledge graph rendering)
- vue-router 4.6.3 - Client-side routing

**Internal (Colmeia scripts):**
- apify_client (custom wrapper) - Web scraping and enrichment (Instagram, YouTube, Google SERP)

## Configuration

**Environment:**
- `.env` file at project root (not committed)
- `.env.example` for reference
- Key vars: `LLM_API_KEY`, `OMNIROUTE_URL`, `GRAPHITI_BASE_URL`, `APIFY_TOKEN`

**Build:**
- `pyproject.toml` - Python project metadata, dependencies, build backend (hatchling)
- `requirements.txt` - Pinned Python dependencies (fallback)
- `frontend/vite.config.js` - Frontend dev server, proxy rules, Vue plugin
- `frontend/package.json` - Frontend dependencies, build scripts
- `docker-compose.yml` - Service orchestration (development/testing)

## Platform Requirements

**Development:**
- Python 3.11+ (3.12 recommended for Windows compatibility with WMI deadlock fix in run.py)
- Node.js 18+ (20+ recommended)
- uv package manager
- Git
- Docker (optional, for containerized dev)

**Production:**
- Docker runtime (multi-stage build: Node 20 → Python 3.12-slim)
- nginx reverse proxy (embedded in Dockerfile)
- Port 80 (frontend + API via nginx)
- 50MB max upload (configured in Flask)

---

*Stack analysis: 2026-04-13*
