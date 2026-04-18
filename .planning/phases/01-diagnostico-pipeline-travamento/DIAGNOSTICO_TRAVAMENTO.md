# Diagnóstico — Pontos de Travamento do Pipeline

**Data:** 2026-04-18
**Autor:** Efesto (análise estática)
**Método:** Leitura dirigida de `llm_client.py`, `report_agent.py`, `simulation_runner.py`, `graph_builder.py`, `apify_enricher.py` + cross-reference com CONCERNS.md e commits upstream.

> Phase 1 do roadmap previa diagnóstico com runtime. Como o VPS não está acessível desta sessão, produzi diagnóstico estático baseado em evidência de código. Vale como ponto de partida — validar com runtime é parte da Phase 1 ainda.

## Ranking de pontos prováveis de parada (por probabilidade × impacto)

### 1. LLM timeout curto + retry fraco (CONFIRMADO — CRÍTICO)

**Evidência:**
- `backend/app/config.py:109` — `LLM_TIMEOUT_SECONDS = 90` (hardcoded default)
- `backend/app/config.py:110` — `LLM_MAX_RETRIES = 3`
- `backend/app/utils/llm_client.py:115` — `time.sleep(min(1 * attempt, 3))` — backoff capado em 3s

**Consequência:** 3 tentativas × 3s backoff = ~15s total antes de desistir. OmniRoute cai por 2min → sistema morre silenciosamente. Sem fallback de provider.

**Sintoma para Igor:** "pipeline sempre para em algo" — quando OmniRoute oscila, qualquer etapa que chama LLM (GraphRAG, perfis, simulação, relatório) aborta.

**Fix cirúrgico:** backoff 5-30s com jitter, 8 tentativas, fallback de provider (ver Phase 2 do roadmap).

### 2. report_agent sem fallback para None do LLM (CONFIRMADO — MÉDIO)

**Evidência:**
- `backend/app/services/report_agent.py:1484` — retorna `final_answer` sem validar se é None
- Upstream `54f1291`: "handle None responses from LLM during content generation and enforce fallback behavior"

**Consequência:** LLM retorna None (timeout, erro 500) → relatório grava string vazia e segue → seção em branco no output final.

**Sintoma para Igor:** "às vezes superficial" — algumas seções ficam vazias porque a chamada falhou silenciosamente.

**Fix:** adotar commit upstream `54f1291` (baixo risco de conflito com Helena Strategos).

### 3. MAX_TOOL_CALLS_PER_CHAT = 2 (PROVÁVEL — ALTO)

**Evidência:**
- `backend/app/services/report_agent.py:940` — `MAX_TOOL_CALLS_PER_CHAT = 2`
- `MAX_TOOL_CALLS_PER_SECTION = 5` (linha 934)
- `min_tool_calls = 3` (linha 1360)

**Consequência:** ReACT é forçado a fazer 3-5 tool calls por seção, mas o LLM só pode invocar 2 por chat. Isso causa mais rodadas de chat (mais latência) e às vezes o LLM retorna Final Answer cedo com dados insuficientes, recebe o prompt de "insuficiente" (L1459), e reescreve em cima do mesmo contexto — gerando texto que parece o material de upload.

**Sintoma para Igor:** "repete o documento de upload sem trazer novo" — LLM fallbackeia para conhecimento do prompt quando não consegue extrair do grafo em poucas calls.

**Fix:** avaliar subir `MAX_TOOL_CALLS_PER_CHAT` para 3-5 e ver se reduz a rejeição de Final Answer.

### 4. `<think>` tags + code fences não limpos (PROVÁVEL — MÉDIO)

**Evidência:**
- `llm_client.py:161` — `re.sub(r'<think>[\s\S]*?</think>', '', content)` limpa só think tags
- Upstream `985f89f`: "fix 500 error caused by `<think>` tags and markdown code fences in content field from reasoning models like MiniMax/GLM"

**Consequência:** se OmniRoute roteia para MiniMax/GLM e o conteúdo vem com code fences, o parsing do tool_call falha → 500 no backend → pipeline para.

**Sintoma para Igor:** "para em algo" intermitente (depende do provider que OmniRoute escolhe).

**Fix:** adotar commit upstream `985f89f`.

### 5. Graphiti sem health check real (CONFIRMADO — ALTO)

**Evidência:**
- Commit histórico `5dba50b`: "fix: Graphiti graph_id propagation to Neo4j" (remediou)
- Commit histórico `bcb2d2b`: "fix: sanitizar XML de tool_call em Section 2"
- CONCERNS.md: "Graphiti falha silenciosamente — nós nunca materializam"

**Consequência:** quando Graphiti não materializa nós, `panorama_search` e `insight_forge` retornam vazio. Relatório fallbackeia para texto livre.

**Sintoma para Igor:** "superficial, repete upload" — sem grafo, relatório = paráfrase do LLM sobre o upload.

**Fix:** health check com contagem real de nós, retry de envio se zero (Phase 2 do roadmap).

### 6. SQLite "readonly database" em restart (CONFIRMADO — MÉDIO)

**Evidência:** PLANO_CORRECAO_MIROFISH.md seção 1.3 (lista como problema conhecido, sem fix aplicado).

**Consequência:** restart de simulação quebra ao reabrir DBs com permissão errada.

**Sintoma para Igor:** "para em algo" em segunda simulação do dia (após container reiniciar).

**Fix:** `os.chmod(0o666)` antes do spawn do subprocess.

### 7. File handle sem context manager (CONFIRMADO — BAIXO)

**Evidência:** CONCERNS.md seção "Fragile Áreas" + `simulation_runner.py:427, 450-451`.

**Consequência:** leak de file descriptors em crash, logs truncados.

**Sintoma:** raro, mas contribui para instabilidade em execuções longas.

**Fix:** refactor com try-finally ou context manager.

## Recomendação de Phase 2

**Aplicar nesta ordem (ganho máximo por esforço mínimo):**

1. Cherry-pick `985f89f` (fix think/code-fence) — 5 min
2. Cherry-pick `54f1291` (None fallback) — 5 min
3. Subir `MAX_TOOL_CALLS_PER_CHAT` 2→3 + teste A/B — 10 min
4. `llm_client.py`: backoff 5-30s + jitter + 8 retries — 30 min
5. `llm_client.py`: provider fallback chain — 1h
6. `simulation_runner.py`: chmod SQLite — 15 min
7. `graph_builder.py`: health check real — 30 min

**Total estimado:** ~3h de trabalho focado.

## Evidência ainda a coletar (precisa VPS)

- [ ] Logs de OmniRoute: frequência de 503/timeout nos últimos 7 dias
- [ ] Provider que OmniRoute está roteando na prática (MiniMax? DeepSeek? Claude?)
- [ ] Relatório recente: quantas seções têm `tool_calls_count == 0`
- [ ] Arquivos de upload típicos: encoding (UTF-8? CP1252?)
- [ ] `simulation_runner.py` state.json: concorrência real observada
