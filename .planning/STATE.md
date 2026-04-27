# STATE — MiroFish INTEIA

## Current
- **Milestone:** v1.2 — Motor Confiável
- **Phases completas:** 1, 2, 3 (parcial — QC + 3 cenários), 4 (perf -53%), 5 (Onda A), 6, 7, 8
- **Status:** deploy contínuo ativo no VPS kvm4, volume-mounted para hot-patch
- **Última sessão (2026-04-27):** Phase 3 entregou QC overlap + gate editorial + Helena 3 cenários probabilísticos. Proxy LLM blindado contra MemoryError (Waitress + MAX_CONTENT_LENGTH 8MB).

## v1.2 Phase Status

### Phase 1 — Diagnóstico ✅
- `DIAGNOSTICO_TRAVAMENTO.md`: 7 pontos ranqueados, análise estática

### Phase 2 — Fix Pipeline ✅ (6/7 tasks live)
- Task 1 (think/code-fence): já existia
- Task 2 (None fallback): já existia
- Task 3 (MAX_TOOL_CALLS_PER_CHAT 2→3): ✅ live
- Task 4 (backoff 5-30s, MAX_RETRIES=8): ✅ live
- Task 5 (provider fallback chain, opt-in): ✅ live (precisa DEEPSEEK_API_KEY para ativar)
- Task 6 (SQLite chmod): ✅ live
- Task 7 (Graphiti health check 10x10s): ✅ live

### Phase 5 — Upstream Sync Onda A ✅
- 2 commits mergeados: `7c7c7a2` (pin axios), `223b283` (fix 3 high-sev CVEs)
- 143 commits upstream restantes documentados em UPSTREAM_SYNC.md (ondas B, C)

### Phase 6 — PT-BR ✅
- BUG FIX: `_translate_if_english` usava assinatura antiga do chat() — toda tradução falhava silenciosamente
- `_RELATION_TRANSLATION` com 35 verbos EN→PT aplicado em edge.name/fact_type

### Phase 7 — Segurança ✅
- `utils/pagination.py` com bounds 10k/1M (evita OOM)
- Clamp aplicado em `/api/simulation/actions` e `/api/graph/projects`
- `/api/internal/v1/health/public` sem token (retorna só up/down)
- `apify_enricher.py` path Windows → env var `COLMEIA_SCRIPTS_PATH`

### Phase 8 — Persistência ✅
- Volume docker `/opt/mirofish/backend/app:/app/backend/app:ro` no compose
- Patches no host refletem no container (só precisa restart)
- Fim do ciclo "código servidor diverge do repo"

## Pending (v1.2)
- Phase 3: Qualidade do Relatório (precisa medição runtime de overlap)
- Phase 4: Performance <30min (precisa benchmark)
- Phase 5 Ondas B+C (143 commits upstream restantes, alta customização)
- Phase 9: Poder Preditivo (precisa simulação real)
- Phase 10: Testes Críticos (P3, trabalho contínuo)

## Decisions
- 2026-04-18: Diagnóstico real sobrescreve plano antigo
- 2026-04-18: Phase 1 é diagnóstico estático (VPS disponível mas runtime de 2h por simulação inviável na sessão)
- 2026-04-18: Phase 2 deploy via docker cp + restart, depois consolidado via volume mount (Phase 8)
- 2026-04-18: Upstream Onda A (só security deps) mergeado; Ondas B/C adiadas — conflito alto em arquivos muito customizados (report_agent.py, zep_tools.py)
- 2026-04-18: LLM_FALLBACK_ENABLED=false default — ativar precisa chaves DeepSeek/Groq
- 2026-04-18: Volume mount em modo `:ro` — protege contra bugs que escrevam no próprio código

## Completed
- v1.0: Sistema funcional
- v1.1 Phase 1-3: Toolbar + Graphiti graph_id + API custos
- v1.2 Phases 1, 2, 5 (A), 6, 7, 8
