# Roadmap — MiroFish INTEIA

## Milestone: v1.1 — Relatório Premium + Qualidade (COMPLETE)

### Phase 1: Relatório Premium — Impressão, Compartilhamento e Custos
**Status:** complete

### Phase 2: Correção Graphiti — Materialização de Nós
**Status:** complete

### Phase 3: API de Custos Real — Token Tracking Backend
**Status:** complete

---

## Milestone: v1.2 — Motor Confiável (ATIVO)

> Diagnóstico real (Igor, 2026-04-18): pipeline não completa, output superficial que repete o upload, demora excessiva, fork defasado vs upstream `666ghj/MiroFish`. PLANO_CORRECAO_MIROFISH.md de 2026-04-10 e CONCERNS.md de 2026-04-13 continuam válidos, mas abaixo dos problemas de produto.

### Phase 1: Diagnóstico do Pipeline que Trava (P0)
**Goal:** Identificar exatamente onde, quando e por que a simulação para. Sem hipótese, sem fix.
**Status:** pending
**Scope:**
- Rodar simulação controlada end-to-end (material conhecido, 20 agentes, 40 rodadas)
- Instrumentar cada etapa: upload → GraphRAG → perfis → simulação → relatório → Helena
- Capturar: timestamp, latência, tokens, provider, status de cada chamada LLM
- Cross-reference com logs de `simulation_runner.py`, Graphiti, OmniRoute, Zep
- Produto: `DIAGNOSTICO_TRAVAMENTO.md` com tabela de pontos de falha + frequência
**Depends on:** nenhum
**UAT:**
- [ ] Pelo menos 3 execuções com material diferente, registrando ponto exato de parada
- [ ] Documento classifica cada travamento: LLM timeout, Graphiti silencioso, subprocess zumbi, deadlock, etc.
- [ ] Sem fix — só diagnóstico

### Phase 2: Corrigir o Ponto de Parada Dominante (P0)
**Goal:** Fix cirúrgico nos 1-2 pontos que mais travam (segundo Phase 1).
**Status:** pending
**Scope:** depende do resultado de Phase 1. Hipóteses atuais:
- LLM Fallback Multi-Provider (se OmniRoute for o SPOF): providers em cadeia (OmniRoute/mirofish-smart → BestFREE → DeepSeek → Groq)
- Graphiti health check real: 10 checks x 10s, re-envio se 0 nós
- Subprocess termination: taskkill/killpg correto, file handles em context manager
- SQLite chmod 666 antes do spawn
- Retry 8x com backoff 5-30s + jitter
**Depends on:** Phase 1
**UAT:**
- [ ] 5 simulações consecutivas completam sem intervenção manual
- [ ] Kill OmniRoute por 2min: sistema retoma sozinho

### Phase 3: Qualidade do Relatório — Não Repetir o Upload (P0)
**Goal:** Relatório traz insight novo, não é paráfrase do material de entrada.
**Status:** pending
**Scope:**
- Auditar `report_agent.py`: quantas chamadas usam ferramentas de grafo vs quantas só geram texto livre
- Medir overlap textual entre relatório final e material de upload (alerta se >30%)
- Forçar ReACT a consultar `panorama_search` e `insight_forge` antes de qualquer seção
- Gate editorial: rejeitar seções sem citação do grafo ou sem número/dado específico
- Section 5 (Helena Strategos): obrigar probabilidades calibradas, não narrativa
- Contra-agentes (devil's advocate): 2-3 agentes contrários ao cenário dominante em `oasis_profile_generator.py`
**Depends on:** Phase 2
**UAT:**
- [ ] Relatório cita >=10 nós do grafo por seção
- [ ] Overlap com upload <30% medido por similaridade textual
- [ ] Helena entrega 3 cenários com probabilidade (não só análise descritiva)
- [ ] Pelo menos 1 cenário contrário ao viés do input

### Phase 4: Performance — Upload a Relatório em <30min (P1)
**Goal:** Tempo total cai de ~2h para <30min com 20 agentes.
**Status:** pending
**Scope:**
- Medir breakdown real: GraphRAG (X min) + perfis (X min) + simulação (X min) + relatório (X min)
- Paralelizar Apify enrichment via asyncio em `apify_enricher.py`
- Cache LRU em `zep_entity_reader.py` (TTL configurável)
- Cache de system prompt por agente (delta de mensagens)
- Investigar gargalo em `run_parallel_simulation.py` L1268 (OASIS já tem semaphore=30)
- Rodadas padrão: validar 40 vs 120 em qualidade de relatório
**Depends on:** Phase 2
**UAT:**
- [ ] Execução completa em <30min com material típico
- [ ] Relatório em <20s (atual 30-60s)
- [ ] Breakdown de tempo por etapa documentado

### Phase 5: Sync com MiroFish Upstream (P1)
**Goal:** Trazer novidades de `666ghj/MiroFish` sem quebrar adaptações INTEIA.
**Status:** pending
**Scope:**
- `git remote add upstream https://github.com/666ghj/MiroFish.git && git fetch upstream`
- Diff estruturado: `git log --oneline fork_point..upstream/main`
- Classificar cada commit upstream: (a) merge direto, (b) merge com adaptação PT-BR, (c) rejeitar (conflito com INTEIA)
- Merge em branch `sync/upstream-YYYY-MM-DD`, testar, push
- Documentar em `UPSTREAM_SYNC.md` o que foi importado e por quê
**Depends on:** Phase 2 (base estável antes de mexer)
**UAT:**
- [ ] Branch sync testada localmente e no VPS staging
- [ ] Adaptações PT-BR preservadas (grafo, Helena, relatório)
- [ ] Rollback documentado: `git revert <merge-commit>`

### Phase 6: Português Total (P1)
**Goal:** Zero texto em inglês no produto final.
**Status:** partial (2.2 e 2.3 do PLANO já feitos)
**Scope:**
- Graphiti: env var `GRAPHITI_SYSTEM_PROMPT` forçando extração PT-BR
- `graph_builder.get_graph_data()`: aplicar mapa de tradução ao retornar edges
- Validar `_translate_facts_batch()` em `zep_tools.py` em simulação real
- Validar prompt ReACT em `report_agent.py`
**Depends on:** nenhum (paralelo a Phase 1-5)
**UAT:**
- [ ] Visualização do grafo sem relações em inglês (FEARS→TEME, IMPLEMENTS→IMPLEMENTA)
- [ ] Relatório final sem citações em inglês

### Phase 7: Segurança Básica (P2)
**Goal:** Fechar buracos listados em CONCERNS.md.
**Status:** pending
**Scope:**
- `INTERNAL_API_TOKEN` obrigatório em produção (raise on startup se vazio)
- `/internal/health` público retorna apenas up/down (não expor LLM_BASE_URL)
- Validação de request: `limit <= 10000`, `offset <= 1000000`, type checking
- Path hardcoded Windows em `apify_enricher.py` L24 → env var `COLMEIA_SCRIPTS_PATH`
**Depends on:** nenhum (paralelo)
**UAT:**
- [ ] Startup falha em produção sem `INTERNAL_API_TOKEN`
- [ ] `limit=999999` retorna 400, não OOM
- [ ] Deploy em Linux funciona sem path Windows

### Phase 8: Persistência + CI (P2)
**Goal:** Patches no servidor não se perdem em restart. Código servidor = repo GitHub.
**Status:** pending
**Scope:**
- `deploy/docker-compose.vps.yaml`: montar `/app/backend` como volume
- Git hook ou CI: push após correção → docker-compose rebuild
- Documentar rollback
**Depends on:** Phase 2
**UAT:**
- [ ] Restart de container preserva patches
- [ ] `git log` no VPS = `git log` no GitHub

### Phase 9: Poder Preditivo — Calibração Real (P2)
**Goal:** Sair de simulação narrativa para previsão calibrada.
**Status:** pending
**Scope:**
- Diversidade intra-grupo: grupos >100K → 3 sub-agentes (favorável/neutro/contrário)
- Benchmark retrospectivo: simular eleição DF 2022 (Ibaneis vs Leandro Grass) vs resultado real
- Métricas de convergência: entropia Shannon em `backend/app/utils/convergence.py`
**Depends on:** Phase 3, 4
**UAT:**
- [ ] Benchmark DF 2022 com erro <20% vs real
- [ ] Simulação para automaticamente quando entropia estabiliza

### Phase 10: Testes Críticos (P3)
**Goal:** Cobertura nos caminhos frágeis identificados em CONCERNS.md.
**Status:** pending
**Scope:**
- API endpoints: `simulation.py`, `report.py`, `graph.py`, `internal.py`
- Service layer: `SimulationRunner`, `ReportAgent`, `ApifyEnricher`
- Process termination cross-platform
- File handle lifecycle
**Depends on:** Phase 2-4
**UAT:**
- [ ] Pytest suite >= 60% cobertura em `services/`
- [ ] CI roda testes em push

---

## Ordem de execução

1. **Phase 1** (diagnóstico) → **Phase 2** (fix do travamento) — sequência crítica
2. **Phase 3** (qualidade do output) paralelo a **Phase 6** (PT-BR)
3. **Phase 4** (performance) + **Phase 5** (upstream sync)
4. **Phase 7** (segurança) + **Phase 8** (persistência)
5. **Phase 9** (predição) + **Phase 10** (testes) — valor de longo prazo
