# Relatório Helena + Efesto — Teste MiroFish-INTEIA (24/04/2026)

**Contexto:** primeira execução ponta-a-ponta do MiroFish no PC de Igor, com dossiês pessoais como input. Stack 100% local por credencial OmniRoute ter falhado. Este documento é avaliação crítica e roadmap de upgrade — não bajulação.

---

## 1. O que foi testado

| Componente | Versão | Onde rodou |
|---|---|---|
| Backend Flask | 0.1.0 (local) | Python 3.11.14 venv + porta 5001 |
| Graphiti Server | `zepai/graphiti:latest` | Docker + porta 8003 |
| Neo4j | `neo4j:5-community` | Docker + volume persistente |
| Ollama | 0.12.x | RTX 3060 Ti (8 GB VRAM) |
| LLM chat | `qwen2.5:7b-instruct` | Ollama local |
| Embedder | `nomic-embed-text` (aliased) | Ollama local |
| Input | 2 dossiês Igor (10,5 KB total) | `.hermes/memories/` |
| Simulação | 15 agentes × 10 rounds × 2 plataformas (Twitter + Reddit) | subprocess OASIS |
| Saída | Markdown de 7 KB + `análise estratégica` Helena | `REL_Igor_simulacao_sim_95c309e2.md` |

Tempo total: **7 min** (ontologia → grafo → perfis → simulação → relatório).

---

## 2. Helena Strategos — Avaliação do resultado

### 2.1 O que funcionou (pouco, mas importante)

- **Pipeline completou** sem intervenção manual. Das 8 etapas (projeto, ontologia, grafo, simulação criada, prepare, start, completed, relatório), todas fecharam com `status=completed`.
- **Estrutura do relatório** seguiu o template INTEIA: síntese, eventos, reações, análise estratégica com riscos/oportunidades/recomendações, confiança.
- **Voz do Igor** foi parcialmente capturada — o modelo reconheceu TDAH+TEA+AH, SEEDF, INTEIA, doutorado IDP, estilo "direto sem bajulação".
- A seção **"Confiança da Previsão"** se auto-desacreditou honestamente ("ausência de dados precisos... limita nossa confiança"). Isso é ouro: o modelo reconheceu as próprias limitações. A Regra Zero (não inferência como fato) está sobrevivendo à camada de relatório.

### 2.2 O que NÃO funcionou — honestidade brutal

**Fabricação grave.** O relatório inventa:
- "INTEIA é instituto sem fins lucrativos" — não está nos dossiês (INTEIA é startup, não ONG).
- "Audiência judicial Dia 1" — não existe nos dossiês.
- "Em uma cena registrada, ele disse: 'A justiça deve ser aplicada sem compromissos'" — aspas inventadas. Igor nunca disse isso.
- Citações Reddit/Twitter ("Sua contribuição... tem sido extremamente valiosa") — fabricadas, já que só 2 ações ocorreram na simulação inteira.
- Probabilidades aparentemente rigorosas ("30% de chance", "40% de aprovação do doutorado") — **números tirados do nada**. Nem o modelo tem base pra isso, nem o simulador forneceu estatísticas.

**Isto fere a Regra Zero frontalmente.** Um relatório INTEIA com citações fabricadas e percentuais inventados é lixo operacional — pior que relatório vazio, porque induz a decisão errada.

### 2.3 Volume da simulação é teatro

- **15 agentes, 10 rounds, 9 segundos de execução, 2 ações totais** (2 no Twitter, 0 no Reddit).
- O "ecossistema de opinião pública" que o relatório descreve é ficção: **não houve opinião pública suficiente para ser simulada**.
- O OASIS truncou de 72 → 10 rodadas por `max_rounds` que defini no script — decisão minha, errada para cenário de vida pessoal (precisaria 50+).

### 2.4 Utilidade estratégica real

**Escala 0-10 de utilidade para decisão INTEIA:** 2/10.

Serve para:
- Validar que o pipeline Mirofish funciona sem OmniRoute (valor técnico de deploy);
- Demonstração (pitch/demo de feature);

**Não serve para:**
- Decisões sobre a vida do Igor (conteúdo é fabricado ou genérico);
- Apresentação a cliente (Paixão Cortes, Jorge Everton) — o output mostraria fragilidade;
- Doutorado (metodologia sem rigor, amostra irrelevante).

### 2.5 Decisão Helena

Este relatório é **descartável**. Guardar só como caso-teste técnico. **Não use como input em nenhum processo decisório real.** Repete o erro estrutural da Colmeia v5 (alucinação empacotada como análise).

---

## 3. Efesto — Análise técnica do pipeline

### 3.1 Gargalos encontrados (ordenados por gravidade)

#### G1. **Graphiti async worker travou — 0 nós persistidos**

- Graphiti aceitou 31 chunks (`POST /messages → 202`), mas a extração em background **não gerou nós no Neo4j**.
- Pipeline continuou por timeout (`100% concluído` sem material real).
- Causa suspeita: fila interna do Graphiti + concorrência com Ollama (qwen2.5:7b com parallelism 1 no runner Ollama).
- **Impacto:** simulação, perfis e relatório rodaram sobre **grafo vazio** — Graphiti respondeu `/search` 200 com zero resultados, mascarando ausência de dados.

#### G2. **Resolução de alias quebrada no SimulationConfig**

- `LLM_MODEL_ALIASES` funciona no `LLMClient.chat()` principal, mas `simulation_config.py` chama `haiku-tasks` literal → 404 do Ollama.
- Workaround: regras fallback (sem LLM) geraram configs de agente.
- **Impacto:** agentes sem personalidade derivada do grafo — todos acabaram genéricos.

#### G3. **Backend não força reload do `.env`**

- Edit em `.env` exige `taskkill` dos processos Python órfãos (3 rodando simultaneamente sem querer).
- `netstat` mostrou PID 37824 persistente mesmo após kill; só SIGTERM explícito mata.
- **Impacto:** debugging do tipo "por que minha mudança não pegou?" (perdi 10 minutos aqui).

#### G4. **Ollama OpenAI compat ignora `format=json`**

- Enviar `format: "json"` em `/v1/chat/completions` **não** ativa grammar constrained sampling. Só `/api/chat` nativa respeita.
- Precisei patchear `llm_client.py` para rotear para API nativa quando `response_format={type:json_object}`.
- **Impacto:** 3 tentativas perdidas (gemma4:e2b, gemma4:26b, qwen2.5 sem patch) antes de descobrir.

#### G5. **Graphiti hardcoded para `text-embedding-3-small`**

- `EMBEDDER_MODEL_NAME=nomic-embed-text` em env **não é lido** pelo Graphiti (embedder config ignorou var).
- Workaround: criei alias Ollama `text-embedding-3-small → nomic-embed-text` via Modelfile.
- **Impacto:** 500 Internal em `/search` até o alias ser criado.

#### G6. **Pipeline poll usa campo errado**

- `run_sim_igor.py` checa `rs.get("status")` mas OASIS retorna `runner_status`.
- Loop espera eternamente `completed`. Simulação já havia terminado aos 38s, script ficou girando 3 minutos até eu matar.
- **Impacto:** falso timeout, ruído no monitor.

### 3.2 Métricas de performance

| Etapa | Duração | Bottleneck |
|---|---|---|
| Ontologia (Ollama qwen 7b) | ~45 s | LLM single-stream |
| Graphiti ingest (31 chunks) | ~5 s | Só envio, async pendente |
| Graphiti processamento | **NÃO COMPLETOU** | Worker async travado |
| Perfis (15 agentes) | ~60 s | Serial, sem paralelismo |
| OASIS runtime | 9 s | Trivial — nada acontece |
| Report agent (5 seções × 2 passes) | ~5 min | Tool-calling serial no qwen |

**Memória GPU:** 4,5 GB de 8 GB usados. Margem pra modelo maior.

### 3.3 Dívidas técnicas do código Mirofish

1. `llm_client.py:200` resolve alias via `Config.resolve_model_name` mas só em `chat()` — `chat_json()` delega, mas caller especial (simulation_config) bypassa.
2. `ontology_generator.py` tem prompt em PT-BR 150 linhas — custo fixo de ~2K tokens toda chamada. Cache poderia cortar.
3. Sem retry exponencial no OASIS runner; se Ollama saturar, rodada é perdida.
4. `run_sim_igor.py` que escrevi é frágil — não respeita backpressure, campos OASIS, max_rounds correto.
5. Graph build tem timeout fixo 120s; insuficiente pra Ollama local com qwen 7B.

---

## 4. Helena + Efesto — Plano de upgrade (prioridade descendente)

### P0 — Bloqueia uso real

1. **Trocar chave OmniRoute.** Sem isso, Mirofish local só serve pra smoke test. Investir 10 min do Igor para gerar key nova no painel `omniroute.srv1354997.hstgr.cloud` > **desbloqueia 80% dos problemas**. Com Sonnet/Opus, extração, perfis, relatório saem com qualidade INTEIA real.
2. **Fix Graphiti async worker.** Sem grafo com nós, simulação é teatro. Debug necessário: habilitar log DEBUG no Graphiti, medir se worker async inicia, ver se Ollama respondeu completions. Possível fix: trocar imagem Graphiti para versão que aceita Ollama-nativa (ou fork com embedder configurável).
3. **Consertar resolução de alias no SimulationConfig.** 5 linhas — substituir construtor do LLMClient em `simulation_config.py` para sempre passar por `resolve_model_name`.

### P1 — Qualidade do resultado

4. **Guard-rails anti-fabricação no ReportAgent.** Adicionar verificação pós-geração: para cada citação "ele disse: ...", conferir se aparece no texto original dos dossiês. Se não, remover ou marcar `[Inferência]`.
5. **`max_rounds` padrão 50 para cenário "vida pessoal"**, 200 para cenário eleitoral. Adicionar tabela de presets no `run_sim_igor.py`.
6. **Seed estatístico explícito.** Se relatório mencionar probabilidades, exigir que venham de contagens da simulação real, não de imaginação do LLM. Prompt deve ter: "Se não tem dado, diga 'não estimável'. Nunca chute número."

### P2 — Produtividade operacional

7. **`setup.sh` idempotente.** Script único que: (a) cria venv se faltar, (b) `docker compose up -d` Neo4j+Graphiti, (c) start Ollama serve 0.0.0.0, (d) pull modelos necessários, (e) start backend + health check. Substitui o `setup_and_run.bat` atual que assume `uv` instalado.
8. **Frontend no mesmo origin.** Servir `frontend/dist/` pelo próprio Flask para evitar CORS e proxy complexo. 20 linhas no `__init__.py`.
9. **Preset "Perfil INTEIA" no Mirofish:** endpoint `/api/internal/v1/run-preset` que recebe `{dossies: [...], requirement: "..."}` e executa os 8 passos atuais autônomos, retornando o `report_id` e URL pronta.
10. **Telemetria de fabricação.** Contar por relatório: nº citações diretas vs nº citações presentes nos dossiês. Métrica de "taxa de alucinação" embutida.

### P3 — Arquitetura (longo prazo)

11. **Embedder descasado do LLM.** Embedder pode ser `nomic-embed-text` (rápido, CPU OK), LLM chat pode ser modelo pesado via OmniRoute — melhor razão custo/qualidade.
12. **Graphiti pode ser substituído por Qdrant + re-ranker custom.** Menos complexidade, mais controle.
13. **OASIS parece subutilizado.** 10 rounds geraram 2 ações — model de comportamento muito conservador. Ajustar `action_probability` no config de plataforma.

---

## 5. Resumo executivo (Helena)

**Status Mirofish hoje:** instalado, rodando, mas operacionalmente inútil sem Sonnet/Opus via OmniRoute. Provou integração técnica, não provou valor analítico.

**Próximo passo único, indiscutível:** restaurar credencial OmniRoute. Tudo o mais vira secundário com LLM real no backend. Se Igor puder gerar key nas próximas 24h, testamos Mirofish de verdade com Jorge Everton ou Paixão Cortes como input e aí sim há decisão possível.

**Este teste como ele foi:** descartável para decisão, útil para estabelecer a baseline técnica e mapear os 13 pontos acima.

---

**Assinado:** Helena Strategos Inteia (estratégia) × Efesto (arquitetura/tecnologia)
**Data:** 2026-04-24 02:35 BRT
