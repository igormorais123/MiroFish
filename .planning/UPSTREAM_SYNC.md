# Upstream Sync — 666ghj/MiroFish → INTEIA fork

**Data análise:** 2026-04-18
**Fork point:** `08688a8` (commit base comum)
**Upstream HEAD:** `fa0f651` (upstream/main)
**Commits upstream não mergeados:** 145

## Sumário executivo

Upstream avançou bastante desde o fork. **Vários commits resolvem problemas ativos do INTEIA** — principalmente output superficial, travamentos e performance. Fazer sync AGORA evita reimplementar o que já existe.

## Commits que atacam problemas reportados por Igor

### Output superficial / repete upload

| Commit | Impacto |
|---|---|
| `0a59bac` | Mínimo **3 tool calls por capítulo** (era 2) — força ReACT a consultar grafo |
| `e004fe8` | Permite até **5 tool calls por capítulo** quando dados insuficientes |
| `dc0a926` | Prompts dedicados para **geração de previsão futura** |
| `7601d78` | Melhora extração de quotes de entrevistas |
| `25aa4f7` | Strict separation entre tool calls e final answers |
| `54f1291` | Handle None do LLM com fallback (evita travar silenciosamente) |
| `ddd9ff2` | Tradução consistente de quotes para idioma do relatório |

### Pipeline que trava

| Commit | Impacto |
|---|---|
| `985f89f` | **Fix 500 error** em `<think>` tags + code fences de modelos MiniMax/GLM |
| `390c120` | Detecção automática de encoding em arquivos não-UTF-8 |
| `40f7035` | Override de env vars no `.env` (resolve fragilidade de config) |
| `08ec856` | Enforce max 10 agents (proteção contra OOM) |
| `08ec856` | Validação de max_agents parameter |

### Performance / escalabilidade

| Commit | Impacto |
|---|---|
| `da6548e` | **Paginação de nodes/edges** — resolve "Memory for Graph in Memory" de CONCERNS.md |
| `085aa6b` | GraphPanel drag não reinicia simulação (UX + CPU) |

### Features novas

| Commit | Impacto |
|---|---|
| `0efd935` | **Docker oficial upstream** (Dockerfile + docker-compose + .dockerignore) |
| `e6da45e` + `b4fe7f2` + `e25d2e3` | **Sistema de histórico de projetos** com modal de detalhes |
| `56b8bab` | Platform display name mapping no ZepGraphMemoryUpdater |
| `49847c5` | Display de número de seção no Step5Interaction |
| `ae1f38c` + `709a0d7` | Rendering markdown melhorado (listas aninhadas, <br>) |

### Segurança

| Commit | Impacto |
|---|---|
| `223b283` | Upgrade axios, rollup, picomatch (3 high severity CVEs) |
| `7c7c7a2` | Pin axios contra supply chain |
| `f240490` | Valida Accept-Language header |

### i18n framework (indireto PT-BR)

Upstream criou sistema i18n completo (chinês ↔ inglês). **Oportunidade:** adicionar PT-BR como terceiro locale em vez de patches manuais.

- `65df257` — upgrade vue-i18n v9→v11
- `5072a2e` — Step4Report i18n
- `e79569a` — report_agent i18n
- `24e9bee` — zep_tools i18n
- `0e55e4c` — config generator + profile generator i18n
- `7c07237` — locale em background threads via thread-local
- `da2490e` — protege JSON field values de language instruction
- `97aa583` — ontology names ficam PascalCase independente do idioma

## Conflitos prováveis com customizações INTEIA

Alto risco de conflito (customizado no fork):
- `report_agent.py` — INTEIA tem Helena Strategos, sanitização XML, ReACT reforçado
- `zep_tools.py` — INTEIA tem `_translate_facts_batch`
- `graph_builder.py` — INTEIA tem mapa de tradução FEARS→TEME
- `README.md` — INTEIA reescrito em PT-BR
- `llm_client.py` — INTEIA adicionou Helena Strategos signature
- `frontend/src/api/*` — INTEIA tem interceptors

Baixo risco:
- `Dockerfile` novo — pode adotar direto
- Paginação de grafo (`da6548e`) — adição pura
- Fixes de segurança deps — adição pura
- Sistema de histórico — adição pura

## Estratégia de sync recomendada

1. **Branch isolada:** `git checkout -b sync/upstream-2026-04-18 origin/main`
2. **Cherry-pick em ondas** (não merge direto de 145 commits):
   - Onda A (baixo risco, alto valor): segurança + paginação + docker + histórico de projetos
   - Onda B (conflito médio): fixes do report_agent que atacam output superficial (`0a59bac`, `e004fe8`, `dc0a926`, `25aa4f7`, `985f89f`, `54f1291`)
   - Onda C (conflito alto): framework i18n — avaliar se vale adotar o sistema completo ou manter patches PT-BR
3. **Teste em cada onda:** simulação end-to-end no VPS staging
4. **Merge no main:** fast-forward após UAT
5. **Rollback documentado:** `git revert -m 1 <merge-sha>`

## Próximos passos imediatos

- [ ] Onda A executável AGORA (patches puros, sem conflito com INTEIA)
- [ ] Onda B exige análise manual de cada arquivo do report_agent (re-aplicar Helena Strategos + XML sanitization em cima)
- [ ] Onda C requer decisão de produto: adotar i18n framework ou manter patches
- [ ] Validar se fix `985f89f` explica algum dos travamentos reportados por Igor

## Evidência ainda a coletar

- Quais modelos LLM o INTEIA está usando no VPS? Se houver MiniMax/GLM, o `985f89f` é fix crítico
- Quantas seções do relatório atual têm 0 tool calls? Medir em relatório recente
- Encoding dos uploads dos usuários INTEIA (sempre UTF-8 ou aparece CP1252 do Windows?)
