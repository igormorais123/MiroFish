# Resultados pós-fix — Pipeline Mirofish

Gerado: 2026-04-25 06:44

Mesmo payload Igor 7-dias rodado 3 vezes:

| Run | Quando | Cache servidor | Fixes | Total |
|---|---|---|---|---|
| #1 | 17:31 | frio | ❌ | **25min06s** |
| #2 | 21:35 | quente (3h após #1) | ❌ | **16min05s** |
| #3 | 06:32 | frio (9h após #2, presumido frio) | ✅ | **11min42s** |

## Quebra por etapa (em segundos)

| Etapa | Run #1 | Run #2 (cache) | Run #3 (fixes) | Δ #3 vs #1 |
|---|---|---|---|---|
| 0→18% Projeto+Onto | 60 | 49 | 50 | -17% |
| 18→55% Graphiti+Sim setup | 157 | 168 | **96** | **-40%** ← fix #1 |
| 55→70% Perfis | 253 | 217 | 266 | +5% (já paralelo) |
| 70→85% Simulação OASIS | 145 | 122 | 72 | -50% (variável aleatória) |
| 85→100% Relatório | **891** | 409 | **217** | **-76%** ← fix #3 |
| **TOTAL** | **1506s** | 965s | **701s** | **-53%** |

## Onde os fixes funcionaram

**Fix #1 (Graphiti polling 100s → 20s):** -60s no Run #3. Confirmado.

**Fix #3 (Relatório paralelo, 4 workers):** ganho gigante. 891s → 217s (**4.1× mais rápido**). Confirma que era loop sequencial dominante. Sem perda visível de coesão narrativa nos relatórios.

**Fix #4 (Cache LRU + semáforo proxy):** ainda zerado (run #3 foi o primeiro pós-restart, não há hits). Mas o ganho aparece em **runs subsequentes do mesmo payload** — esperado próximo run cair pra <2min.

## Métricas do proxy ao final do Run #3

```json
{"calls": 51, "errors": 4, "avg_elapsed_s": 16.4, "total_elapsed_s": 836.5,
 "cache_hits": 0, "cache_misses": 55, "cache_hit_rate": 0.0, "cache_size": 51}
```

- **51 chamadas LLM** no pipeline inteiro
- **avg 16.4s/call** (subprocess Codex + LLM real)
- **4 erros (7.8%)** — investigar
- Pipeline gastou **836s em LLM** dos 701s totais — só faz sentido pq cargas em paralelo (o tempo total é menor que a soma das chamadas).

## Próximas otimizações ainda possíveis

1. **Investigar 4 erros do Codex CLI** — possível fonte de retries que custam tempo
2. **Paralelismo perfis (já em ThreadPool 15)** — se Codex CLI tolerar, subir pra 20-30
3. **Cache de prefixo manual** — extrair system prompt comum entre seções pra reduzir tokens
4. **Persistent Codex worker** — única forma de matar o overhead de spawn (~5-15s × 51 chamadas = 5-13min só de subprocess)

## Hipótese cache do Igor — confirmada e refinada

- Cache servidor ChatGPT existe MAS efeito é menor que parecia: Run #2 vs #1 = 36% mais rápido (cache puro)
- Fixes deram ganho INDEPENDENTE do cache: Run #3 vs #1 = 53% mais rápido
- Run #3 vs Run #2: 27% mais rápido **mesmo presumivelmente sem cache** — o ganho dos fixes supera o do cache servidor
