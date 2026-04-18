# Plano de Correção MiroFish-INTEIA — Helena Strategos

**Data:** 2026-04-10
**Objetivo:** Transformar MiroFish de protótipo instável em motor de previsão confiável
**Prioridade:** P0 → P1 → P2 → P3

---

## FASE 1: Estabilidade (P0) — Parar de quebrar

### 1.1 LLM Fallback Multi-Provider
**Problema:** OmniRoute é SPOF — quando cai, TODO o sistema para
**Solução:** LLMClient com lista de providers e fallback automático
**Arquitetura:**
```
Provider 1: OmniRoute/mirofish-smart (custo $0)
    ↓ falha
Provider 2: OmniRoute/BestFREE (custo $0)
    ↓ falha
Provider 3: DeepSeek direto (custo ~$0.001/req)
    ↓ falha
Provider 4: Groq/llama gratuito (custo $0)
```
**Arquivo:** backend/app/utils/llm_client.py
**Mudança:** _request_with_retry() tenta provider 1, se 503/timeout tenta provider 2, etc.
**Estimativa:** 1 hora

### 1.2 Retry com Exponential Backoff Real
**Problema:** 3 retries com 1-3s de delay não sobrevive a downtime de 2min do OmniRoute
**Solução:** 8 retries, backoff 5-30s, jitter aleatório
**Arquivo:** backend/app/utils/llm_client.py
**Mudança:** Já parcialmente feito — persistir no docker-compose.vps.yaml
**Estimativa:** 15 min

### 1.3 SQLite Permissions Fix
**Problema:** Restart de simulação causa "readonly database"
**Solução:** Criar DBs com chmod 666 + verificar permissão antes de start
**Arquivo:** backend/services/simulation_runner.py, start_simulation()
**Mudança:** Adicionar os.chmod() nos .db files antes de spawn do subprocess
**Estimativa:** 15 min

### 1.4 Graphiti Health Check + Retry
**Problema:** Graphiti falha silenciosamente — nós nunca materializam
**Solução:** (a) Aumentar wait_for_materialization para 10 checks x 10s, (b) Verificar contagem de nós via busca semântica real, (c) Re-enviar mensagens se 0 nós após timeout
**Arquivo:** backend/services/graph_builder.py, wait_for_graph_materialization()
**Estimativa:** 30 min

---

## FASE 2: Português Total (P1) — Tudo em PT-BR

### 2.1 Graphiti System Prompt em PT-BR
**Problema:** Graphiti extrai entidades em inglês (FEARS, ADVOCATES, etc.)
**Solução:** Configurar system prompt do Graphiti para extrair em PT-BR
**Arquivo:** Container zep-graphiti, configuração de modelo
**Mudança:** Adicionar env var GRAPHITI_SYSTEM_PROMPT ou patch no código
**Estimativa:** 30 min

### 2.2 Tradução Automática de Facts
**Problema:** Facts retornados pela busca semântica em inglês
**Solução:** ✅ Já implementado — _translate_facts_batch() no zep_tools.py
**Status:** Testado, aguardando validação na próxima simulação

### 2.3 Prompt ReACT Reforçado
**Problema:** Agente ReACT cola citações em inglês no relatório
**Solução:** ✅ Já implementado — regra 3 reforçada no report_agent.py
**Status:** Testado, aguardando validação

### 2.4 Nomes de Relações em PT-BR
**Problema:** Grafo mostra FEARS, IMPLEMENTS em vez de TEME, IMPLEMENTA
**Solução:** ✅ Mapa de tradução adicionado ao graph_builder.py
**Mudança adicional:** Aplicar tradução no get_graph_data() ao retornar edges
**Estimativa:** 15 min

---

## FASE 3: Velocidade (P2) — De 2h para 20min

### 3.1 Reduzir Rodadas Padrão
**Problema:** 168 rodadas = ~12h com 20 agentes
**Solução:** ✅ Já implementado — prompt ajustado para 24-72h (40 rodadas típico)
**Validação:** Comparar qualidade relatório 40 vs 120 rodadas

### 3.2 Paralelizar Chamadas LLM por Rodada
**Problema:** env.step() chama LLM sequencialmente para cada agente
**Solução:** OASIS já tem semaphore=30. Verificar se o gargalo é no LLM provider ou no framework
**Arquivo:** scripts/run_parallel_simulation.py, linhas 1268-1269
**Investigação:** Medir tempo de cada chamada LLM vs tempo total da rodada
**Estimativa:** 2 horas (investigação + otimização)

### 3.3 Cache de Contexto por Agente
**Problema:** Cada rodada re-envia todo o perfil + histórico do agente
**Solução:** Implementar cache de system prompt por agente (apenas delta de novas mensagens)
**Complexidade:** Alta — depende do OASIS framework
**Estimativa:** 4 horas

---

## FASE 4: Poder Preditivo (P2) — De simulação para previsão

### 4.1 Contra-Agentes (Falsificação)
**Problema:** Agentes confirmam o cenário do input (viés de confirmação)
**Solução:** Auto-gerar 2-3 agentes contrários ao cenário dominante
**Implementação:** No oasis_profile_generator.py, após gerar perfis, criar perfis "devil's advocate"
**Estimativa:** 1 hora

### 4.2 Diversidade Intra-Grupo
**Problema:** 1 agente = 1 grupo inteiro (classe média = 1 pessoa)
**Solução:** Para grupos >100K pessoas, gerar 3 sub-agentes com posições divergentes (favorável, neutro, contrário)
**Estimativa:** 2 horas

### 4.3 Benchmark Retrospectivo
**Problema:** Nenhuma calibração contra dados reais
**Solução:** Simular eleição DF 2022 (Ibaneis vs Leandro Grass) e comparar com resultado real
**Dados necessários:** Dossiê da eleição 2022 (já existe no benchmark_eleitoral do MiroFish)
**Estimativa:** 4 horas (simulação + análise)

### 4.4 Métricas de Convergência
**Problema:** Não há medida de quando a simulação "estabilizou"
**Solução:** Calcular entropia de Shannon das ações por rodada. Quando entropia estabiliza (delta < 5%), simulação pode parar
**Arquivo:** Novo módulo backend/app/utils/convergence.py
**Estimativa:** 2 horas

---

## FASE 5: Persistência (P3) — Sobreviver a restarts

### 5.1 Docker Volume para Patches
**Problema:** Patches via sed/python se perdem no restart do container
**Solução:** Montar /app/backend como volume Docker a partir do repo local
**Arquivo:** deploy/docker-compose.vps.yaml
**Estimativa:** 30 min

### 5.2 Git Push das Correções
**Problema:** Código no servidor diverge do repo
**Solução:** Após cada fase, commitar e push ao GitHub. docker-compose rebuild do repo
**Estimativa:** Contínuo

---

## Cronograma

| Fase | Escopo | Estimativa | Prioridade |
|------|--------|-----------|------------|
| 1 | Estabilidade | 2h | P0 — AGORA |
| 2 | Português | 45min | P1 — Hoje |
| 3 | Velocidade | 8h | P2 — Esta semana |
| 4 | Poder preditivo | 9h | P2 — Esta semana |
| 5 | Persistência | 1h | P3 — Contínuo |

**Total estimado:** ~21 horas de trabalho

---

## Critério de Sucesso

- [ ] Simulação completa 40 rodadas sem interrupção (OmniRoute pode cair e voltar)
- [ ] Zero texto em inglês no relatório final
- [ ] Tempo total upload→relatório < 30 minutos
- [ ] Grafo com >10 nós materializados em toda simulação
- [ ] Helena Strategos com análise em PT-BR e probabilidades calibradas
- [ ] Benchmark retrospectivo com erro < 20% vs resultado real
