# Phase 2 — Corrigir Pontos de Travamento Dominantes

**Goal:** Eliminar os 1-2 pontos mais críticos de travamento identificados em DIAGNOSTICO_TRAVAMENTO.md (Phase 1).

## Premissas
- Phase 1 produziu ranking estático. Validação runtime acontece após cada task desta phase.
- Cada task é atômica, com rollback próprio.
- Ordem importa: tasks 1-2 são cherry-picks upstream de baixo risco; 3 em diante tocam código adaptado INTEIA.

## Tasks

### Task 1: Cherry-pick `985f89f` — fix think tags + code fences
**Arquivo:** `backend/app/utils/llm_client.py` (principalmente)
**Comando:** `git cherry-pick 985f89f`
**Risco:** baixo — toca sanitização de response
**Conflito esperado:** `llm_client.py:161` já tem regex para `<think>`, upstream amplia para code fences
**Rollback:** `git revert HEAD`
**UAT:**
- [ ] Simulação com provider MiniMax/GLM não gera 500
- [ ] Tool calls com code fences são parseados corretamente

### Task 2: Cherry-pick `54f1291` — None fallback no report_agent
**Arquivo:** `backend/app/services/report_agent.py`
**Comando:** `git cherry-pick 54f1291`
**Risco:** médio — arquivo muito customizado (Helena Strategos, ReACT reforçado)
**Conflito esperado:** alto na área de tratamento de response
**Plano de conflito:** manter customização INTEIA, adicionar apenas o `if response is None: return fallback`
**Rollback:** `git revert HEAD`
**UAT:**
- [ ] Mata OmniRoute durante geração de relatório: seção recebe fallback, não string vazia

### Task 3: Subir `MAX_TOOL_CALLS_PER_CHAT` 2→3
**Arquivo:** `backend/app/services/report_agent.py:940`
**Mudança:** `MAX_TOOL_CALLS_PER_CHAT = 2` → `MAX_TOOL_CALLS_PER_CHAT = 3`
**Risco:** baixo — só ajusta constante
**Rollback:** `git revert HEAD`
**UAT:**
- [ ] Relatório gerado com mesmo material que antes tinha seção superficial agora cita mais nós
- [ ] Medir: `tool_calls_count` médio por seção sobe

### Task 4: Backoff exponencial com jitter em `llm_client.py`
**Arquivo:** `backend/app/utils/llm_client.py:115`
**Mudança:**
```python
# Antes
time.sleep(min(1 * attempt, 3))
# Depois
import random
base = min(5 * (2 ** (attempt - 1)), 30)
jitter = random.uniform(0, base * 0.3)
time.sleep(base + jitter)
```
**Config:** `LLM_MAX_RETRIES=3` → `LLM_MAX_RETRIES=8` (env var + `config.py:110`)
**Risco:** baixo
**Rollback:** `git revert HEAD`
**UAT:**
- [ ] Mata OmniRoute por 2min: requisição retoma sozinha

### Task 5: Provider fallback chain em `llm_client.py`
**Arquivo:** `backend/app/utils/llm_client.py`
**Mudança:** lista de providers (OmniRoute → DeepSeek direto → Groq/llama), troca em 503/timeout
**Config nova:**
- `LLM_PROVIDERS_CHAIN=omniroute,deepseek,groq` (env var)
- `DEEPSEEK_API_KEY`, `GROQ_API_KEY` opcionais
- `LLM_FALLBACK_ENABLED=true`
**Risco:** médio — toca caminho crítico, precisa teste
**Feature flag:** `LLM_FALLBACK_ENABLED=false` desativa sem código novo
**Rollback:** `LLM_FALLBACK_ENABLED=false` OU `git revert HEAD`
**UAT:**
- [ ] Log mostra `provider_used` em cada chamada
- [ ] OmniRoute 503: próxima chamada usa DeepSeek automaticamente

### Task 6: SQLite chmod antes do spawn
**Arquivo:** `backend/app/services/simulation_runner.py:start_simulation()`
**Mudança:** antes do subprocess, `os.chmod(db_path, 0o666)` para cada `.db` no workdir
**Risco:** baixo
**Rollback:** `git revert HEAD`
**UAT:**
- [ ] Restart de container + start de simulação: sem "readonly database"

### Task 7: Graphiti health check real
**Arquivo:** `backend/app/services/graph_builder.py:wait_for_graph_materialization()`
**Mudança:**
- 10 checks × 10s (atual: timeout menor)
- Validar contagem de nós via `zep_entity_reader.count_entities(group_id)`
- Se 0 nós após timeout: re-enviar chunks originais (1 retry)
- Log estruturado: `{group_id, nodes_expected, nodes_found, attempts, status}`
**Risco:** médio — mexe no caminho crítico de materialização
**Rollback:** `git revert HEAD`
**UAT:**
- [ ] Simulação com material denso: grafo com >= 10 nós garantido
- [ ] Log mostra retry quando primeira materialização falha

## Ordem de commit

Um commit por task. Mensagem:
```
fix(phase-2/<task>): <descrição>

Ref: DIAGNOSTICO_TRAVAMENTO.md ponto #<N>
Upstream: <sha se cherry-pick>
```

## Verificação final

Após todas as tasks:
1. 5 simulações consecutivas com material diferente, sem intervenção manual
2. Kill OmniRoute por 2min durante simulação: sistema retoma
3. Relatório de simulação: overlap textual com upload < 30% (medido por SequenceMatcher)
4. Log JSON: zero entradas `status=error` não tratadas

Se qualquer UAT falhar: rollback da task responsável + investigação específica (então sim, `/gsd-debug`).

## Não fazer nesta phase

- Refactor de `report_agent.py` (2770 linhas) — fica para Phase 8
- Pydantic validation em API — Phase 7
- Cache LRU em `zep_entity_reader` — Phase 4
- Paralelização Apify — Phase 4
- i18n framework completo do upstream — avaliação em Phase 5
