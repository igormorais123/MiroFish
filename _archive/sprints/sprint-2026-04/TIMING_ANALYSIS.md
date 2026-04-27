# Análise de Tempo por Etapa — Pipeline Mirofish (Codex GPT-5.5)

Gerado: 2026-04-25 (após 4 runs de produção observados)

## Breakdown observado

Etapas reportadas pelo backend via `/run-preset` task progress:

| Etapa | Marker | 5.4-mini Igor | 5.5 #1 Igor | 5.5 #2 Igor (cache) | Julgamento PDF |
|---|---|---|---|---|---|
| 0→18% | Projeto + Ontologia | n/d | 1m00s | 49s | 1m10s |
| 18→55% | Graphiti + Sim setup | n/d | 2m37s | 2m48s | **8m26s** |
| 55→70% | Geração de perfis | 16m00s | 4m13s | 3m37s | 3m31s |
| 70→85% | Simulação OASIS | 12m00s | 2m25s | 2m02s | n/d |
| 85→100% | Relatório | 9m13s | **14m51s** | 6m49s | n/d |
| **Total** | | **~43min** | **25m06s** | **16m05s** | em curso |

## Gargalos identificados

### 1. **Graphiti SEMPRE retorna zero nós → 100s mortos por run** ⚠️ CRÍTICO

Logs mostram em TODOS os runs:
```
ERROR mirofish.graphiti: Graphiti zero nos apos 10x10s
INFO  mirofish.simulation: Fallback LLM extraiu N entidades
```

- 100 segundos perdidos esperando Graphiti popular o grafo (10 retries × 10s)
- Cai pro fallback LLM, que leva mais 41-284s
- **Fallback once levou 4m44s (284156ms)** — outlier do retry interno do LLM
- **Fix proposta:** reduzir polling para 3×5s (15s), ou desabilitar Graphiti se zero nodes consistentemente. Investigar por que Graphiti não está indexando — provavelmente OPENAI_BASE_URL/embedder broken no container.

### 2. **Geração de perfis em série (55→70%)** — 4min com 5.5

Provavelmente 30 chamadas LLM sequenciais, uma por perfil. Cada chamada:
- Subprocess `codex exec` spawn: ~5-15s overhead morto
- Chamada API real: ~5-10s
- Total por perfil: ~15-25s × 30 = 7-12min teóricos

Vimos 4min porque modelo 5.5 é mais rápido + algumas chamadas foram cacheadas.

**Fix:** paralelizar com `ThreadPoolExecutor(max_workers=4-6)`. O Codex CLI tolera múltiplas instâncias. Ganho esperado: 4× → ~1min.

### 3. **Simulação OASIS truncando 168→10 ações** — desperdício

```
INFO mirofish.simulation_runner: Rodadas truncadas: 168 -> 10 (max_rounds=10)
```

OASIS gera 168 ações mas só usa 10. Isso é 16× desperdício de chamadas LLM.

**Fix:** parametrizar `max_rounds` no OASIS antes da geração, não depois. Investigar se é bug ou config (provavelmente `MAX_ROUNDS_OVERRIDE` no preset não está chegando ao runner).

### 4. **Relatório (85→100%): 15min no run #1, 7min no run #2** — gargalo + cache forte

A mesma seção LLM no run #2 caiu pela metade. Provavelmente `ReportAgent` gera N seções sequencialmente:
- Run #1: cache frio = 15min (cada seção 2-4min)
- Run #2: cache de prefixo do servidor ChatGPT = 7min

**Fix A — paralelizar seções:** `ReportAgent.SECTIONS` provavelmente roda em loop. Trocar por `concurrent.futures` (5 seções → 5× speedup teórico, ~3min).

**Fix B — cache manual de prefixo:** identificar prompt comum (system + ontologia) e mandar via `cache_control` se Codex CLI suportar. Talvez não suporte; nesse caso só paralelizar.

### 5. **Subprocess overhead do Codex CLI** — ~5-15s por chamada

Cada `codex exec` no Windows com .cmd faz spawn shell + auth + load profile. Isso é tempo morto antes da API.

Pipeline tem ~50-100 chamadas LLM no total. 100×8s = **13 min só de overhead morto**.

**Fix definitivo (maior ganho):** trocar `subprocess` por **persistent worker**:
- Opção A: `codex --serve` ou similar (verificar se Codex CLI suporta modo daemon)
- Opção B: implementar pool de workers Codex que ficam "esperando" prompt via stdin
- Opção C: descobrir endpoint OpenAI direto da OAuth ChatGPT Pro (pode existir, basta investigar `~/.codex-pro/auth.json`)

## Plano de ataque ordenado por impacto

| # | Mudança | Etapa atacada | Ganho estimado |
|---|---|---|---|
| 1 | Reduzir Graphiti polling para 3×5s OU desabilitar | 18→55% | -85s/run |
| 2 | Paralelizar perfis (ThreadPool 6 workers) | 55→70% | -3min |
| 3 | Paralelizar seções do relatório | 85→100% | -7min |
| 4 | Persistent Codex worker | tudo | -10min (50% total) |
| 5 | Fix `max_rounds` no OASIS antes da gen | 70→85% | menor mas evita tokens caros |

**Cenário otimista pós-fix:** pipeline cair de 25min → ~6-8min para payload novo, ~3-4min com cache.

## Hipótese cache — confirmada com nuance

| Run | Payload | Tempo | Caches relevantes |
|---|---|---|---|
| 5.4-mini #1 | Igor 7d (1º do dia) | 43min | nenhum |
| 5.5 #1 | Igor 7d (2º com mesmo conteúdo) | 25min | **prefix cache ChatGPT do mini** |
| 5.5 #2 | Igor 7d (3º idêntico) | 16min | cache mini + 5.5 |

**Conclusão:** o "5.5 mais rápido que mini" foi inflado pelo cache de prefixo do ChatGPT entre runs idênticos. O ganho real do 5.5 é provavelmente menor (~10-20%, não 42%). Os runs Julgamento (PDF novo) e Sergipe (5 docs novos) vão dar a medida limpa, sem contaminação de cache.
