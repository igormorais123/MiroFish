# Plano de Implementacao — Consultoria por Simulacao INTEIA no Mirofish

Data: 2026-05-04  
Fonte-base: https://mirantenews.com.br/artigos/inteia-consultoria-simulacoes-agentes-gemeos-digitais  
Status: plano estrutural + P0 tecnico aplicado

## Status real

O Mirofish INTEIA ja tinha o nucleo mais dificil implantado: intake, ontologia, grafo, perfis OASIS, simulacao Twitter/Reddit, Apify, API interna `run-preset`, Helena Strategos, QC de overlap e historico de simulacoes. A lacuna critica era de governanca: o relatorio ainda podia ser produzido como artefato textual mesmo quando a simulacao ou a evidencia eram fracas. Isso contradizia a promessa central da reportagem: testar antes de recomendar e mostrar erro, limite e risco residual.

## Tese de implementacao

A reportagem nao deve virar copy no produto. Deve virar contrato de execucao:

1. nenhuma entrega sem demanda e material-base;
2. nenhuma simulacao sem agentes/perfis e configuracao persistida;
3. nenhum relatorio sem execucao auditavel;
4. nenhuma citacao direta sem existir no corpus;
5. nenhuma recomendacao sem separar fato, simulacao, inferencia e campo necessario.

## Mapeamento da reportagem para o sistema atual

| Camada prometida | O que ja existe | Ajuste estrutural necessario |
|---|---|---|
| Intake e diagnostico | `ProjectManager`, `simulation_requirement`, contexto estruturado, upload/texto | Tornar briefing estruturado obrigatorio para modo cliente e registrar hipotese testada |
| Agentes sinteticos | `OasisProfileGenerator`, perfis Reddit/Twitter, fallback LLM de entidades | Importador de perfis INTEIA e bancos Helena/Colmeia como presets |
| Replicas digitais | OASIS como mundo social; `simulation_config.json`; Lenia export parcial | Formalizar tipos de replica: social, mercado, juridica, operacional, infraestrutura |
| Verificacao | QC overlap, grounding por secao, logs `agent_log.jsonl` | Gate hard antes/depois do relatorio; auditoria de citacoes; proximo passo: auditoria numerica |
| Entrega | `ReportAgent`, Helena final, markdown, API de download | Relatorio com manifesto de evidencias, limites e risco residual; bloquear status completed se falhar |

## P0 aplicado agora

Implementado no codigo:

1. `backend/app/services/report_system_gate.py`
   - bloqueia relatorio se a simulacao nao tiver estado, projeto, grafo, texto-base, config, perfis, `run_state` concluido e minimo de acoes;
   - cria contrato das cinco camadas da reportagem;
   - coleta corpus local de evidencias para auditoria.

2. `backend/app/services/report_agent.py`
   - salva `system_gate.json`, `evidence_manifest.json` e `evidence_audit.json`;
   - adiciona `quality_gate` e `evidence_audit` ao `meta.json`;
   - falha fechado se houver citacao direta sem suporte;
   - ajusta prompts para consultoria por simulacao: hipotese, resultado, limite, risco residual.

3. `backend/app/api/report.py`
   - retorna `409` antes de iniciar task quando o gate estrutural falha.

4. `backend/app/api/internal.py`
   - `run-preset` passa texto-base para o relatorio e falha a task se o relatorio nao terminar como `COMPLETED`.

5. `backend/app/utils/report_quality.py`
   - adiciona extracao e auditoria conservadora de citacoes;
   - ignora exemplos em blocos de codigo;
   - renderiza bloco de auditoria no relatorio.

6. `backend/app/config.py`
   - novas chaves:
     - `REPORT_MIN_ACTIONS` default `10`;
     - `REPORT_REQUIRE_COMPLETED_SIMULATION` default `true`;
     - `REPORT_REQUIRE_SOURCE_TEXT` default `true`;
     - `REPORT_FAIL_ON_UNSUPPORTED_QUOTES` default `true`.

## Estudo complementar — opiniao publica com agentes sinteticos

Fonte Mirante: https://mirantenews.com.br/artigos/opiniao-publica-agentes-sinteticos  
Artigo primario: Lan, Hu, Guo e Huang, "Public opinion dissemination simulation based on large language model multi-agent systems", Scientific Reports, publicado em 2026-04-04, DOI `10.1038/s41598-026-44206-z`.  
Artigo adjacente estudado: Yao et al., "Social opinions prediction utilizes fusing dynamics equation with LLM-based agents", Scientific Reports, publicado em 2025-05-03.

### Achado metodologico

O artigo de Lan et al. confirma a tese da reportagem principal, mas acrescenta uma exigencia que o gate anterior ainda nao media: uma simulacao social util precisa provar diversidade comportamental e semantica. Contar acoes nao basta. Um sistema pode gerar 40 postagens e ainda ser apenas monologo distribuido.

O metodo do artigo combina:

1. camada macro probabilistica;
2. camada micro cognitiva com LLM;
3. procedimento operacional padronizado de simulacao publica;
4. piscina global de informacao compartilhada;
5. avaliacao por entropia comportamental e Distinct-1/2.

O ponto central para Mirofish INTEIA: o LLM nao deve decidir tudo. Frequencia, ativacao, tendencia, papeis e alvos precisam ser constrangidos por parametros. O LLM entra para gerar conteudo semantico quando a simulacao ja definiu quem fala, quando fala e por que fala.

### O que foi acrescentado no sistema

Implementado depois do estudo complementar:

1. `backend/app/services/simulation_data_reader.py`
   - `get_diversity_metrics()` agora mede:
     - entropia normalizada dos tipos de acao;
     - entropia normalizada da participacao por agente;
     - Distinct-1;
     - Distinct-2;
     - tamanho medio dos textos;
     - cobertura por `entity_type`;
     - distribuicao por plataforma.

2. `backend/app/services/report_system_gate.py`
   - o gate passa a inserir metricas de diversidade em `quality_gate.metrics.diversity`;
   - bloqueia relatorio se `Distinct-2` ficar abaixo do minimo configurado;
   - bloqueia relatorio se a participacao ficar concentrada demais em poucos agentes;
   - alerta quando todos os atos sao do mesmo tipo, porque isso indica monologo/postagem, nao opiniao publica.

3. `backend/app/config.py`
   - novas chaves:
     - `REPORT_MIN_DISTINCT_2` default `0.30`;
     - `REPORT_MIN_AGENT_ACTIVITY_ENTROPY` default `0.25`;
     - `REPORT_MIN_BEHAVIOR_ENTROPY` default `0.20`;
     - `REPORT_REQUIRE_ACTION_TYPE_DIVERSITY` default `true`.

4. `backend/tests/test_simulation_data_reader.py`
   - adiciona testes para detectar simulacao variada e simulacao homogenea.

### Resultado critico nos dados existentes

Ao aplicar o novo gate em simulacoes locais antigas:

| Simulacao | Acoes | Distinct-2 | Entropia de acao | Resultado |
|---|---:|---:|---:|---|
| `sim_263de9cacb1f` | 28 | 0.2453 | 0.00 | bloqueada |
| `sim_3aad150e338a` | 40 | 0.2480 | 0.00 | bloqueada |

Essa e uma descoberta importante. Antes, essas simulacoes passavam porque tinham acoes suficientes e execucao concluida. Depois do estudo de opiniao publica, elas falham porque sao semanticamente repetitivas e todas as acoes registradas sao `CREATE_POST`. Isso confirma a avaliacao Helena+Efesto de 2026-04-24: havia risco de "teatro" operacional mesmo com pipeline funcionando.

### Decisao tecnica

O sistema agora diferencia:

- **evidencia suficiente**: ha simulacao concluida e corpus local;
- **evidencia diversa**: agentes e textos variam o bastante para sustentar leitura social;
- **evidencia publicavel**: passa gate estrutural, auditoria de citacoes e diversidade minima.

Depois da correcao de 2026-05-04, a diversidade de tipo de acao passou a ser bloqueio por default (`REPORT_REQUIRE_ACTION_TYPE_DIVERSITY=true`). O gate tambem le a tabela `trace` dos bancos OASIS para verificar se houve comportamento social real, distinguindo postagens iniciais de comentarios, curtidas, repostagens, follows ou novas postagens pos-estimulo.

### Fase P0.2 implementada em 2026-05-04

1. `SimulationState` agora sincroniza com `SimulationRunner` ao salvar `run_state.json`; APIs, relatorio e tela deixam de discordar sobre `running/completed/failed`.
2. O ReportManager expoe artefatos JSON auditaveis (`system_gate.json`, `evidence_manifest.json`, `evidence_audit.json`) por API.
3. A rota `/api/simulation/<simulation_id>/quality` consolida diversidade, trace OASIS e gate de relatorio antes da entrega.
4. O runner paralelo deixou de duplicar postagens iniciais como se fossem acoes posteriores.
5. O leitor local mede `oasis_trace`: contagem por plataforma, entropia comportamental, estimativa de postagens dinamicas e total de acoes interativas.
6. Perfis OASIS novos recebem contrato comportamental explicito para agir como participantes sociais, nao apenas observadores.
7. Testes adicionados para sincronizacao de status, artefatos de auditoria, trace OASIS e contrato comportamental.
8. A interface da etapa de simulacao consulta `/api/simulation/<simulation_id>/quality` e so libera o botao de relatorio quando o mesmo gate sistemico do backend aprova a simulacao.

### Fase P0.3 implementada em 2026-05-04

1. `frontend/src/components/Step4Report.vue` passou a mostrar a cadeia de custodia do relatorio: gate estrutural, auditoria de citacoes, artefatos gerados, metricas de diversidade e motivos de bloqueio.
2. Relatorios antigos sem `quality_gate` e `evidence_audit` agora sao classificados como `legacy_unverified` no backend e tratados na interface como legado nao publicavel.
3. `backend/app/services/social_bootstrap.py` adiciona um plano deterministico de pulso social inicial, configuravel por `social_dynamics`.
4. Novas configuracoes de simulacao incluem `social_dynamics` por default, com mistura de acoes para Twitter e Reddit.
5. `backend/scripts/run_parallel_simulation.py` executa o pulso dentro do proprio OASIS depois dos posts iniciais, registrando apenas acoes persistidas no `trace` e em `actions.jsonl`.
6. O pulso inicial resolve o gargalo encontrado nas simulacoes antigas: em vez de depender apenas do LLM escolher interacoes, o sistema garante uma primeira camada auditavel de comentarios, likes/dislikes, reposts e quotes contra posts de outros agentes.

### Implicacao para produto

O proximo gargalo nao e relatorio. E calibracao da simulacao.

Para cumprir a promessa da reportagem, o Mirofish precisa gerar e registrar mais do que posts:

1. comentarios;
2. reposts;
3. likes/dislikes;
4. respostas institucionais;
5. amplificacao por atores de alta influencia;
6. decaimento por fadiga ou deslocamento de atencao.

Sem isso, Helena deve bloquear ou rebaixar a entrega para "diagnostico tecnico de simulacao", nao "relatorio de consultoria".

Com a fase P0.3, esse requisito deixa de ser apenas uma recomendacao e entra como comportamento padrao do runner. O gate continua necessario: se o OASIS nao persistir as interacoes ou se a diversidade semantica ficar fraca, o relatorio segue bloqueado.

## Invariante operacional

Um relatorio cliente INTEIA so pode ter status `completed` se:

1. `simulation_id` existe;
2. `project_id` existe;
3. `simulation_requirement` existe;
4. texto-base do projeto existe;
5. `graph_id` existe e bate com a simulacao;
6. `simulation_config.json` existe;
7. ha perfis sinteticos persistidos;
8. `run_state.json` existe e esta `completed`;
9. ha pelo menos `REPORT_MIN_ACTIONS` acoes reais de agentes;
10. ha diversidade semantica minima nos textos gerados;
11. a participacao nao esta concentrada em poucos agentes;
12. existe diversidade comportamental minima de tipos de acao;
13. o `trace` OASIS nao se limita a sign-up, refresh e postagens iniciais;
14. todas as aspas diretas do relatorio aparecem literalmente no corpus de evidencia.

Este e o ponto que reduz a chance de "relatorio bonito com base fraca".

## Adaptacao as peculiaridades Mirofish INTEIA

Nem tudo da reportagem encaixa literalmente.

- "Replica digital" no Mirofish atual e principalmente social/comportamental, nao fisica. Para infraestrutura tecnica, sera necessario outro adaptador de dominio.
- Helena deve permanecer camada de direcao e leitura, nao substituir o motor OASIS.
- Graphiti e util, mas nao pode ser ponto unico de verdade; o sistema ja usa fallback local via `actions.jsonl`, e isso deve continuar.
- O produto deve aceitar smoke test, mas smoke test nao pode virar relatorio cliente. Para demo tecnica, reduza `REPORT_MIN_ACTIONS`; para entrega, mantenha o default ou suba.

## Ganhos criticos esperados

| Ganho | Avaliacao | Motivo |
|---|---:|---|
| Reducao de alucinacao em relatorio | Alta | citacao direta sem corpus bloqueia status final |
| Rastreabilidade | Alta | manifesto liga relatorio a projeto, simulacao, config, acoes e evidencias |
| Deteccao de teatro simulado | Alta | Distinct-2, entropia de agentes, entropia de acao e trace OASIS expõem simulacao homogenea |
| Valor consultivo | Medio/alto | relatorio passa a mostrar limite e risco residual, nao so narrativa |
| Velocidade | Neutro/negativo leve | gate pode bloquear rodadas pequenas; custo aceitavel para entrega cliente |
| Repetibilidade | Alta | criterios viram configuracao e teste, nao decisao manual |
| Defesa metodologica | Alta | facilita explicar o que foi simulado, o que foi inferido e o que exige campo |

## Red Team

Contra-hipotese forte: o gate pode bloquear uma simulacao util com poucas acoes, especialmente em dominios onde a ausencia de acao tambem e dado. Mitigacao: permitir preset analitico de "baixa atividade" no futuro, mas ele deve gerar relatorio diagnostico, nao recomendacao cliente.

Segundo risco: auditoria literal de aspas rejeita citacao traduzida. Decisao: isso e correto. Traducao vira parafrase marcada `[Simulacao]` ou `[Inferencia]`, sem aspas diretas.

Terceiro risco: se `run_state` estiver errado, o gate bloqueia indevidamente. Mitigacao implementada em 2026-05-04: sincronizacao automatica entre `SimulationRunner` e `SimulationState`.

## Cenarios 30 dias

| Cenario | Probabilidade | Resultado |
|---|---:|---|
| Base | 55% | Gate estabiliza relatorios novos; ajustes ficam em UI, auditoria numerica e presets |
| Otimista | 30% | Mirofish vira motor confiavel de consultoria simulada para pilotos eleitorais/mercado |
| Pessimista | 15% | OASIS gera poucas acoes; maior parte das rodadas bloqueia e exige ajuste de comportamento dos agentes |

## Roadmap restante

### P0 — Fechar garantias

1. Criar auditoria numerica: percentuais e probabilidades devem vir de contagem, metrica ou ser marcados como inferencia calibrada.
2. Expor `system_gate.json` e `evidence_audit.json` no frontend. **Concluido na P0.3.**
3. Separar modo `cliente` de modo `smoke/demo`.
4. Validar em nova execucao OASIS se o contrato comportamental gera comentarios, reposts, likes/dislikes e respostas de controle com fidelidade. **Parcialmente implementado na P0.3; falta rodada real longa com LLM.**
5. Implementar preset de baixa atividade que gere diagnostico tecnico sem fingir opiniao publica.

### P1 — Consolidar conhecimento INTEIA

1. Adaptador de perfis Helena/Colmeia para OASIS.
2. Presets por dominio: eleitoral, juridico, mercado, educacao, infraestrutura.
3. Biblioteca de hipoteses testaveis por dominio.
4. Memoria acumulada: cada relatorio aprovado vira insumo versionado da proxima rodada.

### P2 — Produto e avaliacao de ROI

1. Painel de prontidao antes do botao de relatorio.
2. Benchmark contra metodo tradicional: tempo, custo, retrabalho, taxa de contradicao, utilidade decisoria.
3. Exportacao executiva: resumo cliente + anexo tecnico de evidencias.
4. Pilotos: politica/eleicao, empresa/mercado e operacao tecnica.

## Criterio de pronto do sistema completo

O sistema so estara completo quando uma demanda cliente conseguir atravessar:

`briefing -> grafo -> perfis -> simulacao -> verificacao -> relatorio -> memoria acumulada`

sem etapa manual escondida, sem relatorio fora do gate e com trilha de evidencia suficiente para defender a conclusao.

Confianca desta implementacao inicial: 0.82. O ponto mais forte e o bloqueio estrutural do relatorio. O ponto ainda fraco e a dependencia de acoes suficientes do OASIS; se o simulador continuar gerando pouco comportamento, o gate vai fazer o papel certo: bloquear a fantasia.
