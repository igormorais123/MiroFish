# Codebase Concerns

**Analysis Date:** 2026-04-13
**Last update:** 2026-05-04

## Mitigacoes aplicadas em 2026-05-04

- Relatorio fora do sistema: mitigado por `report_system_gate.py`, auditoria de citacoes e status `publishable`.
- Simulacao monologica com apenas `CREATE_POST`: mitigada por metricas de diversidade e bloqueio por trace OASIS.
- Desacordo entre `SimulationRunner` e `SimulationManager`: mitigado por sincronizacao de `run_state`.
- Relatorios antigos sem evidencia: mitigados por classificacao `legacy_unverified`.
- Falta de visibilidade do gate: mitigada pela etapa 3 e cadeia de custodia na etapa 4.
- Dependencia do LLM escolher interacoes espontaneamente: reduzida pelo pulso social inicial configuravel.
- Baixa cobertura de contratos criticos: reduzida para 70 testes backend passando.

Risco residual importante: ainda falta rodada real longa com LLM ativo para confirmar que o conjunto contrato comportamental + pulso OASIS + gate gera relatorio publicavel em caso novo.

## Tech Debt

**Bare Exception Handling in JSON Parsing:**
- Issue: Multiple `except:` clauses with no exception type specified in `simulation_config_generator.py` lines 502 and 508, catching all exceptions including SystemExit and KeyboardInterrupt
- Files: `backend/app/services/simulation_config_generator.py` (lines 502-509)
- Impact: Makes debugging difficult, hides critical errors, prevents proper signal handling during shutdown
- Fix approach: Replace bare `except:` with `except Exception:` to allow system exceptions to propagate normally

**Large Monolithic Services:**
- Issue: Service classes exceed 2700+ lines (report_agent, simulation_runner, simulation API) creating high cyclomatic complexity
- Files: 
  - `backend/app/services/report_agent.py` (2770 lines)
  - `backend/app/services/simulation_runner.py` (1874 lines)
  - `backend/app/api/simulation.py` (2736 lines)
- Impact: Difficult to test, maintain, and reason about; high chance of introducing bugs during changes
- Fix approach: Extract methods into smaller service classes, create service layer abstractions, split API routes into multiple blueprints
- Update 2026-05-04: parte da governanca foi extraida para `report_system_gate.py` e `social_bootstrap.py`; `report_agent.py`, `simulation_runner.py` e `simulation.py` seguem grandes.

**File Handle Not Using Context Manager:**
- Issue: Manual file opening at `simulation_runner.py` line 427 without `with` statement; handle stored in class variable for later closing
- Files: `backend/app/services/simulation_runner.py` (lines 427, 450-451)
- Impact: Risk of resource leak if exception occurs before handle is properly closed or stored; subprocess redirection may fail to flush
- Fix approach: Refactor to use context manager or ensure file handle is properly cleaned up even on exception paths

**Hardcoded Windows-Specific Path:**
- Issue: Apify enricher contains hardcoded Windows user path that will fail on other systems
- Files: `backend/app/services/apify_enricher.py` (line 24)
- Impact: Cannot run enrichment on non-Windows machines; breaks deployment on Linux/Mac VPS
- Fix approach: Use environment variable to locate Colmeia scripts path, with fallback configuration

**Missing Input Validation:**
- Issue: Query parameters and request bodies lack comprehensive validation/sanitization
- Files: `backend/app/api/simulation.py`, `backend/app/api/report.py`, `backend/app/api/graph.py` (multiple lines)
- Impact: Potential for unexpected behavior if malformed requests are sent; no upper bounds checking on limits parameter
- Fix approach: Add request validation decorators, implement Pydantic models for request validation, add range checks on numeric parameters

## Known Bugs

**Simulation Process UTF-8 Handling on Windows:**
- Symptoms: Potential encoding issues when OASIS libraries read/write files with non-ASCII characters
- Files: `backend/app/services/simulation_runner.py` (lines 430-433)
- Trigger: Running simulations with Brazilian Portuguese agent names/content on Windows
- Workaround: Set PYTHONUTF8=1 and PYTHONIOENCODING=utf-8 (already done in code)
- Note: Workaround is in place but fragile - depends on env var persistence

**Race Condition in Budget Guard:**
- Symptoms: Apify budget limit may be exceeded if multiple concurrent enrichment requests execute simultaneously
- Files: `backend/app/services/apify_enricher.py` (lines 88, 93-104)
- Trigger: Concurrent calls to `build_enrichment_block()` from multiple simulation configs
- Workaround: None - currently single-threaded execution only
- Impact: Can exceed Apify monthly budget without warning

## Security Considerations

**INTERNAL_API_TOKEN Not Required:**
- Risk: If INTERNAL_API_TOKEN is not set, internal endpoints are completely open
- Files: `backend/app/api/internal.py` (lines 232-235)
- Current mitigation: Logs warning if token not configured, but doesn't block access
- Recommendations: 
  - Require INTERNAL_API_TOKEN to be non-empty (raise on startup if missing in production)
  - Generate random default token on first startup if none provided
  - Add rate limiting on internal endpoints

**Request Data Not Validated:**
- Risk: Query parameters like `limit`, `offset`, `from_line` not validated for reasonable ranges
- Files: `backend/app/api/simulation.py` (lines 1906-1910, 1952-1953), `backend/app/api/report.py` (lines 372-373, 797, 879)
- Impact: Potential for:
  - OOM on large `limit` values (requesting millions of records)
  - SQL injection if backend later uses raw queries
  - DoS via resource exhaustion
- Recommendations:
  - Add max bounds: limit <= 10000, offset <= 1000000
  - Validate integer types with type checking
  - Consider implementing pagination cursor tokens instead of offset

**API Response Exposes Configuration Details:**
- Risk: `/internal/health` endpoint returns LLM_BASE_URL and GRAPHITI_BASE_URL to unauthenticated requests
- Files: `backend/app/api/internal.py` (lines 245-258)
- Impact: Reveals internal infrastructure to potential attackers
- Recommendations:
  - Require token authentication even for health checks
  - Only expose minimal health status (up/down) to unauthenticated users

**Subprocess Shell Command Construction:**
- Risk: Command constructed with Python interpreter and script path - currently safe but uses `cmd` list (good)
- Files: `backend/app/services/simulation_runner.py` (lines 415-423)
- Current state: Safe (uses list, not shell=True), but fragile
- Recommendations:
  - Validate all command arguments before subprocess execution
  - Log full command being executed for audit trails
  - Consider using `shlex` for any user-controlled arguments

## Performance Bottlenecks

**Report Agent Performs Sequential Tool Calls:**
- Problem: ReportAgent makes individual LLM calls for each tool invocation rather than batching
- Files: `backend/app/services/report_agent.py` (complex with multiple self._llm_client.create_message calls)
- Cause: ReACT pattern with reflection requires sequential reasoning
- Current impact: 30-60 second report generation time
- Improvement path: 
  - Implement parallel tool execution where possible
  - Cache tool results across report sections
  - Pre-compute common queries once per simulation
- Update 2026-05-04: risco de qualidade foi reduzido por gate/auditoria; performance sequencial continua pendente.

**No Caching for Entity Reader:**
- Problem: ZepEntityReader queries graph on every request without caching
- Files: `backend/app/services/zep_entity_reader.py` (every method makes fresh API call)
- Current impact: Duplicate requests to Graphiti for same entity data within short timeframe
- Improvement path:
  - Add in-memory LRU cache with configurable TTL
  - Implement cache invalidation on graph updates
  - Consider Redis for distributed cache if deployed

**Apify Enrichment Not Parallelized:**
- Problem: Sequential Google SERP → Instagram → YouTube requests per entity
- Files: `backend/app/services/apify_enricher.py` (build_enrichment_block iterates serially)
- Cause: API client blocking I/O, no async/concurrent implementation
- Current impact: Enrichment for 10 entities takes ~30-60 seconds
- Improvement path:
  - Use asyncio to parallelize Apify requests
  - Implement request batching to Apify API
  - Add circuit breaker for budget protection

## Fragile Áreas

**Signal Handler Registration in Flask Debug Mode:**
- Files: `backend/app/services/simulation_runner.py` (lines 1400-1464)
- Why fragile: Complex logic to detect Flask debug mode vs reloader process; environment variable-dependent
- Safe modification:
  - Add unit tests for each condition branch
  - Document exact behavior with each env var combination
  - Test on both development and production Flask modes
- Test coverage: Logic for `is_debug_mode` and `is_reloader_process` not tested

**Process Termination Cross-Platform:**
- Files: `backend/app/services/simulation_runner.py` (lines 827-880)
- Why fragile: 
  - Windows uses `taskkill` command (external dependency)
  - Unix uses `os.killpg()` (process group dependent on start_new_session flag)
  - Multiple fallback paths with different timeout behaviors
- Safe modification:
  - Mock subprocess.run and os.killpg in tests
  - Test both graceful and force termination paths
  - Verify process tree cleanup on both platforms
- Test coverage: No tests for process termination logic

**File Handle Management for Subprocess Logs:**
- Files: `backend/app/services/simulation_runner.py` (lines 427, 450-451, 569, 575)
- Why fragile:
  - File handle stored in class-level dict keyed by simulation_id
  - Closing happens only in cleanup_all_simulations() or monitor thread
  - If simulation crashes before monitor thread closes handle, leak occurs
  - No try-finally to guarantee closure
- Safe modification:
  - Refactor to use try-finally or context managers
  - Add explicit close on exception paths
  - Track handle state to prevent double-close
- Test coverage: File handle lifecycle not tested

**Simulation State JSON Concurrent Access:**
- Files: `backend/app/services/simulation_runner.py` (multiple read/write to state.json)
- Why fragile: No locking mechanism for concurrent state.json access
- Current risk:
  - Monitor thread reads while API writes state
  - Multiple API requests could race on updates
  - IPC client simultaneously reads status
- Safe modification:
  - Implement file-level locking using fcntl (Unix) or msvcrt (Windows)
  - Or use in-memory dictionary with lock, flush periodically
- Test coverage: No tests for concurrent state mutations

## Scaling Limits

**Single Simulation Process Per ID:**
- Current capacity: Limited by system resources (CPU, memory) for subprocess
- Limit: Cannot horizontally scale simulations beyond one machine
- Scaling path:
  - Implement job queue (Celery/RQ) for background simulations
  - Use subprocess pooling with worker processes
  - Move to distributed architecture with simulation workers

**Memory for Graph in Memory:**
- Current capacity: Entire Zep graph entities loaded into memory via ZepEntityReader
- Limit: Graph with 100k+ entities may exceed available RAM
- Scaling path:
  - Implement pagination/streaming for large graphs
  - Use database cursor patterns instead of loading all entities
  - Add memory-mapped file support for large datasets

**LLM Timeout at 90 Seconds:**
- Current capacity: Requests exceeding 90 seconds fail
- Limit: Large report generation or complex ontology inference may timeout
- Scaling path:
  - Implement async job model with polling
  - Add streaming responses for long-running tasks
  - Increase timeout with user warning about cost implications

## Dependencies at Risk

**Python-Specific Imports Without Type Hints:**
- Risk: Code dynamically loads apify_client from hardcoded Windows path
- Files: `backend/app/services/apify_enricher.py` (lines 24-34)
- Impact: Type checking tools cannot validate; IDE autocompletion fails
- Migration plan:
  - Make apify_client a proper pip dependency
  - Add type hints: `from apify_client import ApifyClient`
  - Remove sys.path manipulation

**OpenAI Client with Hardcoded Model Names:**
- Risk: Model names like "haiku-tasks", "sonnet-tasks", "opus-tasks" are custom aliases requiring OmniRoute
- Files: `backend/app/config.py` (lines 48-57, 114-118)
- Impact: Cannot run without OmniRoute configured; fallback to OpenAI may fail with unknown model
- Migration plan:
  - Add validation that resolved model exists before sending requests
  - Implement model existence check on startup
  - Add fallback chain: requested → alias → OmniRoute → OpenAI

**Zep Cloud Hard Dependency:**
- Risk: ZepEntityReader and ZepGraphMemoryManager assume Zep is always available
- Files: `backend/app/services/zep_entity_reader.py`, `backend/app/services/zep_graph_memory_updater.py`
- Impact: No fallback if Zep is down; graph building fails completely
- Migration plan:
  - Implement abstract entity reader interface
  - Add keyword-based fallback entity reader
  - Graceful degradation when Zep unavailable

## Missing Critical Features

**No Simulation Pause/Resume:**
- Problem: Simulations cannot be paused mid-run; only stop (which terminates everything)
- Blocks: Long-running simulations cannot be interrupted for inspection without losing progress

**No Result Export:**
- Problem: Simulation results cannot be exported to CSV/JSON for external analysis
- Blocks: Integration with external BI tools; data sharing with non-technical stakeholders

**No Rollback Capability:**
- Problem: Graph updates are immediate; no version control or rollback
- Blocks: Cannot recover from erroneous enrichment or generation

**No Rate Limiting on APIs:**
- Problem: No per-user or per-IP rate limiting
- Blocks: Susceptible to abuse/DoS; Apify budget vulnerable to rapid concurrent requests

## Test Coverage Gaps

**API Endpoints Not Tested:**
- What's not tested: All endpoints in `simulation.py`, `report.py`, `graph.py`, `internal.py`
- Files: `backend/app/api/` (entire module)
- Risk: Regressions in happy path and error handling paths go undetected
- Priority: **High** - affects all user-facing functionality
- Update 2026-05-04: novos contratos de service layer foram testados; rotas ainda precisam de testes com Flask client.

**Service Layer Logic Not Tested:**
- What's not tested: SimulationRunner, SimulationManager, ReportAgent, ApifyEnricher
- Files: `backend/app/services/` (most modules)
- Risk: Complex logic with side effects (file I/O, process management) has no verification
- Priority: **High** - critical for stability
- Update 2026-05-04: `simulation_data_reader`, `simulation_manager`, `report_quality`, artefatos de relatorio e `social_bootstrap` agora tem cobertura direta.

**Configuration Validation Not Tested:**
- What's not tested: Config.validate() and env var handling
- Files: `backend/app/config.py`
- Risk: Missing required configs only caught at runtime, not startup
- Priority: **Medium** - reduces early error detection

**Error Handling Paths Not Tested:**
- What's not tested: Exception cases in simulation runner, API error responses
- Files: `backend/app/services/simulation_runner.py`, `backend/app/api/`
- Risk: Error recovery paths may silently fail or behave unexpectedly
- Priority: **High** - affects reliability

**Process Termination Not Tested:**
- What's not tested: Windows taskkill, Unix killpg, timeout behavior
- Files: `backend/app/services/simulation_runner.py` (lines 827-880)
- Risk: Zombie processes or incomplete cleanup on termination
- Priority: **High** - can exhaust system resources

**Frontend API Integration Not Tested:**
- What's not tested: API interceptors, retry logic, error handling
- Files: `frontend/src/api/` (all modules)
- Risk: Frontend error handling masks backend issues; retry logic may cause duplicate operations
- Priority: **Medium** - affects UX reliability

---

*Concerns audit updated: 2026-05-04*
