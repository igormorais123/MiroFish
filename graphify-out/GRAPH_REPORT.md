# Graph Report - mirofish-ai-friend  (2026-07-29)

## Corpus Check
- 223 files · ~249,218 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4459 nodes · 9391 edges · 195 communities (170 shown, 25 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 540 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f0277105`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Step4Report.vue
- report_agent.py
- Step3Simulation.vue
- ReportManager
- build_executive_package
- test_report_quality.py
- Step5Interaction.vue
- test_vox_science_artifacts.py
- report.py
- report_exporter.py
- datetime
- OasisProfileGenerator
- PowerPersonaCatalog
- codex_proxy.py
- graph.py
- internal.py
- ProjectManager
- social_bootstrap.py
- report_quality.py
- SimulationManager
- report_system_gate.py
- IPCHandler
- MainView.vue
- IPCHandler
- EntityNode
- Asset
- SimulationIPCClient
- ZepGraphiti
- HelenaCommandCenter.vue
- Step2EnvSetup.vue
- simulation.py
- SimulationRunState
- harness_evidence_bundle.py
- ForecastLedger
- evaluate_report_method_checklist
- Any
- .log
- SimulationConfigGenerator
- SimulationRunView.vue
- TaskManager
- Flask
- cli.py
- TextProcessor
- frontend/package.json
- ._generate_section_react
- RalphMethodEvaluator
- TokenTracker
- GoldenCaseLoader
- test_retry.py
- HookifyEvaluator
- report.js
- SimulationView.vue
- ApifyEnricher
- test_vox_metrics.py
- repair_report_finalization
- .check_env_alive
- normalize_report_attribution
- report_content_repair.py
- StrategicDensityGate
- PlatformActionLogger
- HistoryDatabase.vue
- SimulationRunner
- ReportView.vue
- GraphitiClient
- PowerCatalog
- create_app
- ReportDeliveryEvaluator
- run_reddit_simulation
- simulation.js
- test_pagination.py
- LLMClient
- TokenUsage
- InteractionView.vue
- llm_proxy_v2.py
- GitOps
- run_parallel_simulation.py
- ParallelIPCHandler
- scripts
- warning
- SkillPromptEvaluator
- Home.vue
- AgentAction
- test_translation.py
- AgentActivity
- GraphPanel.vue
- helenaExecutor.js
- GeneticCopyAsset
- build_decision_packet
- mission_bundle.py
- report_diagrams.py
- ._request
- ExperimentLog
- test_helena_control_api.py
- Config
- OntologyGenerator
- simulation_runner.py
- test_report_exports_api.py
- MissionSelection
- FrontendPerfAsset
- helena.js
- Any
- Any
- Step1GraphBuild.vue
- GraphBuilderService
- SimulationLogManager
- router/index.js
- ._build_graph_worker
- build_report_evolution_readiness
- ZepGraphMemoryUpdater
- CostGuard
- llm_client.py
- .chat
- validate_uploaded_file
- SimulationStatus
- evaluate_section_grounding
- FrontendPerfEvaluator
- ProxyHandler
- mirofish_smoke_check.py
- Graphiti Service
- escapeHtml
- token_tracker.py
- .path
- createExportDraft
- vercel.json
- .wait_for_graph_materialization
- .close
- closeModal
- get_graph_status
- services/__init__.py
- report_section_workers
- ._call_with_retry
- Any
- PlatformSimulation
- phase03_e2e_validation.py
- approveAndExecute
- smoke_test.sh
- start_mirofish.sh
- .delete_group
- autoresearch/__init__.py
- targets/__init__.py
- conftest.py
- vite.config.js
- mirofish-reconcile-check.sh
- stop_mirofish.sh
- Exception
- Path
- PathLike
- ValueError
- Smoke Test Data
- mirofish-backend
- render_safe_markdown
- Any
- Path
- report_bundle_verifier.py
- SimulationIPCServer
- resolve_delivery_governance
- loads_first_object
- simulation_data_reader.py
- PageSpan
- test_helena_reasoning_effort.py
- find_excerpt
- ForecastLedger
- AtoProcessual
- build_judicial_ontology
- test_judicial_ontology.py
- normalize_type
- build_case_products
- TextProcessor
- test_report_exporter.py
- _first_non_empty
- ._ensure_log_file
- test_phase03_smoke.py
- .generate
- _count_anchored_nodes
- _ok
- CoberturaDaTese
- ResultadoDoGate
- .to_dict
- _Completed
- _carrega_rotas
- test_sistema_vem_antes_do_usuario
- test_credencial_de_api_nao_chega_ao_subprocesso
- test_concorrencia_limitada_pelo_semaforo
- test_helena_vai_para_sol_com_raciocinio_alto
- test_modelo_desconhecido_cai_no_luna_e_nao_fora_da_assinatura

## God Nodes (most connected - your core abstractions)
1. `ReportManager` - 127 edges
2. `ReportAgent` - 94 edges
3. `SimulationManager` - 85 edges
4. `error()` - 85 edges
5. `SimulationRunner` - 76 edges
6. `Report` - 75 edges
7. `PowerPersonaCatalog` - 58 edges
8. `Config` - 54 edges
9. `TokenTracker` - 54 edges
10. `ReportStatus` - 53 edges

## Surprising Connections (you probably didn't know these)
- `health()` --indirect_call--> `_metrics()`  [INFERRED]
  codex_proxy.py → backend/app/services/vox_science/artifacts.py
- `metrics()` --indirect_call--> `_metrics()`  [INFERRED]
  codex_proxy.py → backend/app/services/vox_science/artifacts.py
- `LunaOpenAIClient` --uses--> `LLMClient`  [INFERRED]
  deploy/graphiti_patches/zep_graphiti.py → backend/app/utils/llm_client.py
- `ZepGraphiti` --uses--> `LLMClient`  [INFERRED]
  deploy/graphiti_patches/zep_graphiti.py → backend/app/utils/llm_client.py
- `_api_key()` --indirect_call--> `Config`  [INFERRED]
  backend/tests/test_helena_reasoning_effort.py → backend/app/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Mirofish Infrastructure Stack** — docker_compose_neo4j, docker_compose_graphiti, docker_compose_mirofish [EXTRACTED 1.00]
- **LLM and Graph Integration** — docker_compose_graphiti, graphiti_concept, camel_ai [INFERRED 0.85]

## Communities (195 total, 25 thin omitted)

### Community 0 - "Step4Report.vue"
Cohesion: 0.01
Nodes (130): activeExport, activeExportId, activeExportVerification, activeSectionIndex, activeStep, agentLogLine, agentLogs, auditIssues (+122 more)

### Community 1 - "report_agent.py"
Cohesion: 0.03
Nodes (64): Servico do Report Agent Geracao de relatorios de simulacao no padrao ReACT usand, Registrador de log de console do Report Agent      Escreve logs no estilo consol, Converte para formato Markdown, Converte para formato Markdown, ReportConsoleLogger, ReportOutline, ReportSection, collect_report_evidence() (+56 more)

### Community 2 - "Step3Simulation.vue"
Cohesion: 0.03
Nodes (88): getPowerCatalog(), getPowerPersonaCatalog(), getMissionSelection(), getRunStatusDetail(), getSimulationQuality(), getSimulationReadiness(), saveMissionSelection(), actionIds (+80 more)

### Community 3 - "ReportManager"
Cohesion: 0.05
Nodes (50): delete_report(), download_report(), get_report_artifact(), get_report_sections(), list_report_artifacts(), Obter um artefato JSON especifico do relatorio., Baixar relatorio (formato Markdown)      Retorna arquivo Markdown, Obter lista de secoes ja geradas (saida por secoes)      O frontend pode consult (+42 more)

### Community 4 - "build_executive_package"
Cohesion: 0.07
Nodes (51): create_executive_package_route(), download_executive_package_file_route(), Criar pacote executivo apenas para relatorio publicavel., Baixar apenas arquivos allowlisted no manifesto do pacote executivo., create_app(), Resolve CORS sem wildcard implicito em ambientes publicos., Cria e configura a aplicacao Flask., _resolve_cors_origins() (+43 more)

### Community 5 - "test_report_quality.py"
Cohesion: 0.04
Nodes (76): Exception, Report Agent - Agent de geracao de relatorios de simulacao      Utiliza o padrao, Aplica a Regra Zero tambem ao resumo que abre o relatorio., Remove o conteudo final bruto da resposta antes de registra-la no agent_log., ReportAgent, audit_report_evidence(), evaluate_section_grounding(), extract_direct_quotes() (+68 more)

### Community 6 - "Step5Interaction.vue"
Cohesion: 0.04
Nodes (70): getAgentLog(), getReport(), getReportEvolutionReadiness(), getReportSections(), repairReportContent(), getSimulationProfilesRealtime(), interviewAgents(), activeReportTool (+62 more)

### Community 7 - "test_vox_science_artifacts.py"
Cohesion: 0.11
Nodes (35): _build(), _build_with(), _gate(), test_baseline_servidores_inclui_pep_e_vozes(), test_claim_policy_define_c2_para_trace_robusto_sem_erro_externo(), test_compost_audit_exclui_outcome_do_prompt(), test_detecta_dominio_eleitoral(), test_detecta_dominio_servidores_federais() (+27 more)

### Community 8 - "report.py"
Cohesion: 0.06
Nodes (43): _build_power_persona_catalog(), build_power_persona_context(), _build_power_persona_context_from_payload(), _build_power_selection_from_payload(), check_report_status(), estimate_powers(), _extract_power_ids(), _extract_power_persona_ids() (+35 more)

### Community 9 - "report_exporter.py"
Cohesion: 0.20
Nodes (25): allowed_export_file_path(), create_report_export(), _evidence_annex_markdown(), _exports_root(), list_report_exports(), load_export_manifest(), _now_iso(), _public_export_manifest() (+17 more)

### Community 10 - "datetime"
Cohesion: 0.09
Nodes (50): cancel_helena_command(), complete_helena_command(), _disabled_response(), _error_response(), execute_helena_command(), get_helena_command(), get_helena_context(), get_helena_status() (+42 more)

### Community 11 - "OasisProfileGenerator"
Cohesion: 0.05
Nodes (32): OasisAgentProfile, OasisProfileGenerator, Any, callable, Salva Profile em arquivo (escolhe formato correto por plataforma)          Requi, Salva Twitter Profile em formato CSV (conforme OASIS oficial)          Campos CS, Padroniza campo gender para formato ingles exigido pelo OASIS          OASIS exi, Salva Reddit Profile em formato JSON          Usa formato consistente com to_red (+24 more)

### Community 12 - "PowerPersonaCatalog"
Cohesion: 0.19
Nodes (23): PowerPersonaCatalog, Catalogo seguro de poderes e personas externas para INTEIA., Indexa arquivos pequenos de fontes externas sem acoplar seus sistemas., Testes do catalogo de poderes e personas externas., test_api_helpers_filtram_catalogo_e_montam_contexto(), test_arquivo_malformado_nao_derruba_catalogo(), test_catalogo_deduplica_por_caminho_e_nome_normalizado(), test_catalogo_deduplica_por_tipo_e_nome_entre_caminhos() (+15 more)

### Community 13 - "codex_proxy.py"
Cohesion: 0.11
Nodes (34): _cache_get(), _cache_key(), _cache_set(), _call_codex(), _call_llm(), _call_omniroute(), chat_completions(), embeddings() (+26 more)

### Community 14 - "graph.py"
Cohesion: 0.04
Nodes (64): delete_graph(), get_graph_data(), get_project(), Rotas de API relacionadas ao grafo de conhecimento Utiliza mecanismo de contexto, Obter detalhes do projeto, Obter dados do grafo (nos e arestas), Excluir grafo do Graphiti, _build_lenia_export() (+56 more)

### Community 15 - "internal.py"
Cohesion: 0.20
Nodes (10): _build_project_text(), create_project_from_briefing(), create_project_from_structured_briefing(), _normalize_structured_context(), Cria projeto interno a partir de briefing textual e gera ontologia., Normaliza materiais textuais enviados pela INTEIA., Alias explicito para o fluxo estruturado da INTEIA., Extrai contexto estruturado relevante para cenarios INTEIA. (+2 more)

### Community 16 - "ProjectManager"
Cohesion: 0.05
Nodes (46): allowed_file(), delete_project(), generate_ontology(), get_graph_status(), list_projects(), Redefinir estado do projeto (para reconstruir o grafo), Interface 1: Upload de arquivos, analise e geracao da definicao de ontologia, Verifica se a extensao do arquivo e permitida (+38 more)

### Community 17 - "social_bootstrap.py"
Cohesion: 0.23
Nodes (21): _action_args_for(), _action_mix(), _agent_ids_from_config(), build_social_bootstrap_plan(), _coerce_float(), _coerce_int(), _coerce_non_negative_int(), get_social_bootstrap_target() (+13 more)

### Community 18 - "report_quality.py"
Cohesion: 0.08
Nodes (40): audit_report_content_consistency(), _claim_categories(), _claim_number_value(), _coerce_positive_int(), _first_positive_metric(), _flatten_numeric_metrics(), jaccard_similarity(), _known_platforms() (+32 more)

### Community 19 - "SimulationManager"
Cohesion: 0.08
Nodes (32): get_internal_simulation(), Consulta o estado resumido de uma simulacao., LLMEntityExtractor, Extrai entidades de texto usando LLM como alternativa ao Graphiti., Conjunto completo de parametros da simulacao., SimulationParameters, Any, callable (+24 more)

### Community 20 - "report_system_gate.py"
Cohesion: 0.26
Nodes (14): _enum_value(), evaluate_decision_readiness(), _next_action(), Any, Estado de prontidao de decisao para simulacoes., Consolida simulacao, gate e relatorio em um estado de produto., Resultado da validacao estrutural pre-relatorio., ReportGateResult (+6 more)

### Community 21 - "IPCHandler"
Cohesion: 0.06
Nodes (30): CommandType, IPCHandler, main(), MaxTokensWarningFilter, Any, Script de simulacao OASIS Twitter com configuracoes predefinidas Este script le, Constantes de tipos de comando, Processador de comandos IPC (+22 more)

### Community 22 - "MainView.vue"
Cohesion: 0.09
Nodes (39): getProject(), clearPendingUpload(), getPendingUpload(), state, addLog(), buildProgress, currentPhase, currentProjectId (+31 more)

### Community 23 - "IPCHandler"
Cohesion: 0.06
Nodes (30): CommandType, IPCHandler, main(), MaxTokensWarningFilter, Any, Script de simulacao OASIS Reddit com configuracoes predefinidas Este script le o, Constantes de tipos de comando, Processador de comandos IPC (+22 more)

### Community 24 - "EntityNode"
Cohesion: 0.08
Nodes (30): Extrator de entidades via LLM (fallback quando Graphiti esta indisponivel). Usa, Gerador de Agent Profile OASIS Converte entidades do grafo Zep para o formato Ag, AgentActivityConfig, DeliveryGovernanceConfig, EventConfig, PlatformConfig, Gerador inteligente de configuracao de simulacao. Usa LLM para produzir parametr, Configuracao de eventos da simulacao. (+22 more)

### Community 25 - "Asset"
Cohesion: 0.08
Nodes (28): ABC, AutoResearch Engine — Loop autonomo de experimentacao.  Ciclo: hipotese (LLM) →, Asset, Constraints, Evaluator, ExperimentResult, Classes base abstratas para alvos de AutoResearch., Resultado de um unico experimento. (+20 more)

### Community 26 - "SimulationIPCClient"
Cohesion: 0.10
Nodes (26): CommandStatus, CommandType, IPCCommand, IPCResponse, Any, Enum, str, Modulo de comunicacao IPC para simulacao Usado para comunicacao entre processos (+18 more)

### Community 27 - "ZepGraphiti"
Cohesion: 0.07
Nodes (30): AddEntityNodeRequest, AddMessagesRequest, add_entity_node(), add_messages(), AsyncWorker, clear(), delete_entity_edge(), delete_episode() (+22 more)

### Community 28 - "HelenaCommandCenter.vue"
Cohesion: 0.05
Nodes (40): getHelenaStatus(), approvalToken, authenticated, availabilityClass, availabilityLabel, busy, closePanel(), command (+32 more)

### Community 29 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (39): getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles, emit (+31 more)

### Community 30 - "simulation.py"
Cohesion: 0.04
Nodes (85): build_graph(), Interface 2: Construir grafo a partir do project_id      Requisicao (JSON):, build_internal_graph(), create_internal_simulation(), prepare_internal_simulation(), Dispara a construcao do grafo para um projeto interno., Cria uma simulacao vinculada a um projeto existente., Dispara a preparacao da simulacao para consumo interno. (+77 more)

### Community 31 - "SimulationRunState"
Cohesion: 0.09
Nodes (15): Any, Estado de execucao da simulacao (tempo real), Adiciona acao a lista de acoes recentes, Informacoes detalhadas incluindo acoes recentes, Obtem historico de Interview de um banco de dados, Obtem historico de Interview (do banco de dados)                  Args:, Extrai resumo auditavel de um actions.jsonl sem materializar todas as acoes., Reconcilia run_state.json com os logs auditaveis.          Isso torna a leitura (+7 more)

### Community 32 - "harness_evidence_bundle.py"
Cohesion: 0.16
Nodes (33): _absolute_api_url(), _artifact_gate_passes(), _artifact_tag(), _artifact_url(), _build_evidence(), _build_forecasts(), _build_graph(), build_harness_evidence_bundle() (+25 more)

### Community 33 - "ForecastLedger"
Cohesion: 0.14
Nodes (17): _brier_score(), _canonical_json(), ForecastEntry, _log_loss(), _mean(), Any, Livro deterministico de previsoes operacionais., Retorna previsoes em ordem deterministica por id. (+9 more)

### Community 34 - "evaluate_report_method_checklist"
Cohesion: 0.13
Nodes (30): _artifact_names(), build_report_delivery_packet(), Any, Pacote de decisao de entrega para relatorios., Consolida estado de entrega sem promover rascunho a entrega cliente., _verified_bundle(), _artifact_passes(), _build_payload() (+22 more)

### Community 35 - "Any"
Cohesion: 0.05
Nodes (25): is_substantive_section_response(), Any, Inicializa o Report Agent          Args:             graph_id: ID do grafo, Define as ferramentas disponiveis, Executa uma chamada de ferramenta          Args:             tool_name: Nome da, Analisa chamadas de ferramenta a partir da resposta do LLM          Formatos sup, Valida se o JSON analisado e uma chamada de ferramenta valida, Converte o modo vindo da UI para o nome interno da ferramenta. (+17 more)

### Community 36 - ".log"
Cohesion: 0.06
Nodes (24): Obtem o tempo decorrido desde o inicio (em segundos), Registra uma entrada de log          Args:             action: Tipo de acao, ex:, Remove o contexto ativo do medidor desta instancia., Registra o inicio da geracao do relatorio, Registra o inicio do planejamento do sumario, Registra as informacoes de contexto obtidas durante o planejamento, Registra a conclusao do planejamento do sumario, Registra o inicio da geracao de uma secao (+16 more)

### Community 37 - "SimulationConfigGenerator"
Cohesion: 0.11
Nodes (17): Any, Gerador inteligente de configuracao de simulacao.      Analisa objetivo, documen, Gera a configuracao completa da simulacao em varias etapas., Monta o contexto para o LLM e o limita ao tamanho maximo., Gera um resumo das entidades agrupadas por tipo., Executa chamada ao LLM com retry e tentativa de reparo do JSON., Fecha estruturas simples em um JSON truncado., Tenta recuperar um JSON de configuracao invalido. (+9 more)

### Community 38 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (29): getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, graphOfflineNoticeShown, handleGoBack() (+21 more)

### Community 39 - "TaskManager"
Cohesion: 0.07
Nodes (27): get_task(), list_tasks(), Consultar estado da tarefa, Listar todas as tarefas, create_harness_run(), get_internal_task(), Alias semantico para iniciar a pesquisa completa via harness MiroFish., Consulta o estado de tasks internas. (+19 more)

### Community 40 - "Flask"
Cohesion: 0.08
Nodes (43): Registro de blueprints da API., get_mission_bundle(), get_report_delivery_package(), get_report_evolution_readiness(), Gerar manifesto final da missao a partir dos artefatos do relatorio., Obter pacote consolidado de entregabilidade do relatorio., Obter estado read-only para evoluir a analise do relatorio., get_simulation_readiness() (+35 more)

### Community 41 - "cli.py"
Cohesion: 0.08
Nodes (25): main(), CLI para AutoResearch INTEIA.  Uso:     python -m backend.autoresearch.cli --tar, Configura alvo Frontend Performance., Configura alvo de score da fronteira de entrega de relatorios., Mede score baseline sem modificar nada., Configura alvo Hookify Rules., Configura alvo Skill Prompt., Configura alvo Genetic Copy. (+17 more)

### Community 42 - "TextProcessor"
Cohesion: 0.09
Nodes (20): Servico de processamento de texto, _extrai_carimbo(), FileParser, Ferramenta de analise de arquivos Suporta extracao de texto de arquivos PDF, Mar, Analisador de arquivos, Extrair texto de um arquivo          Args:             file_path: Caminho do arq, Extrair texto de Markdown, com deteccao automatica de codificacao, Extrair texto de TXT, com deteccao automatica de codificacao (+12 more)

### Community 43 - "frontend/package.json"
Cohesion: 0.07
Nodes (28): axios, d3, dependencies, axios, d3, mermaid, vue, vue-router (+20 more)

### Community 44 - "._generate_section_react"
Cohesion: 0.10
Nodes (32): Conferencia, _contem(), filter_verified_facts(), _folhas_citadas(), normalizar(), Any, Enum, str (+24 more)

### Community 45 - "RalphMethodEvaluator"
Cohesion: 0.11
Nodes (13): Configura alvo de score do metodo RalphLoop + AutoResearch., setup_ralph_target(), Any, Path, RalphMethodAsset, RalphMethodConstraints, RalphMethodEvaluator, Invariantes do metodo Ralph aplicado ao Mirofish. (+5 more)

### Community 46 - "TokenTracker"
Cohesion: 0.09
Nodes (24): get_token_usage(), Retorna consumo de tokens e custo acumulado (global e por sessao)., Inicia uma sessao isolada do medidor sem zerar consumo global., Singleton thread-safe para rastrear tokens globalmente e por sessao., TokenTracker, Testes do TokenTracker e TokenUsage (Phase 10)., Reset singleton state entre testes — TokenTracker e singleton global., reset_singleton() (+16 more)

### Community 47 - "GoldenCaseLoader"
Cohesion: 0.17
Nodes (11): GoldenCaseLoader, Any, Path, Carregador defensivo para pacote de caso de ouro., Le um pacote de caso de ouro a partir de um caminho injetado., Retorna resumo do pacote em campos estaveis para auditoria local., Monta fixture curta para testes de qualidade e regressao., Carrega manifesto, JSON e listas de arquivos existentes. (+3 more)

### Community 48 - "test_retry.py"
Cohesion: 0.13
Nodes (23): Any, Exception, Mecanismo de retentativa para chamadas de API Usado para tratar logica de retent, Encapsulamento de cliente de API com retentativa, Executar chamada de funcao com retentativa em caso de falha          Args:, Chamada em lote com retentativa individual para cada item que falhar          Ar, Decorador de retentativa com backoff exponencial      Args:         max_retries:, Versao assincrona do decorador de retentativa (+15 more)

### Community 49 - "HookifyEvaluator"
Cohesion: 0.10
Nodes (16): HookifyAsset, HookifyEvaluator, match_rules(), parse_hookify_rule(), Path, Verifica se o asset modificado ainda e valido., Asset: conjunto de arquivos hookify.*.local.md., Le todos os arquivos hookify concatenados. (+8 more)

### Community 50 - "report.js"
Cohesion: 0.12
Nodes (23): createExecutivePackage(), createReportExport(), getApiBasePath(), getConsoleLog(), getExecutivePackageAttachmentUrl(), getMissionBundle(), getReportArtifacts(), getReportDeliveryPackage() (+15 more)

### Community 51 - "SimulationView.vue"
Cohesion: 0.09
Nodes (25): closeSimulationEnv(), getEnvStatus(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData (+17 more)

### Community 52 - "ApifyEnricher"
Cohesion: 0.18
Nodes (10): ApifyClient, ApifyEnricher, _cache_key(), _cache_path(), Any, Path, Enriquecimento de materiais-base via Apify.  Fontes: Google SERP, Instagram (per, Enriquece multiplos municipios de forma otimizada.          Cada municipio e um (+2 more)

### Community 53 - "test_vox_metrics.py"
Cohesion: 0.13
Nodes (25): demographic_parity_difference(), intra_group_variance(), kl_divergence(), mean_absolute_error(), _normalize(), _quantile(), Statistical distance and fairness metrics for Vox Science fidelity reports.  Pur, Stability score in [0, 1] where 1 = identical distributions.      Uses ``1 - nor (+17 more)

### Community 54 - "repair_report_finalization"
Cohesion: 0.14
Nodes (26): Reparar finalizacao do relatorio sem chamar LLM., repair_report_finalization_route(), Enum, str, ReportStatus, _now_iso(), _preview(), Any (+18 more)

### Community 55 - ".check_env_alive"
Cohesion: 0.09
Nodes (20): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt(), Entrevistar um Agent      Nota: requer ambiente em modo de espera de comandos, Entrevistar multiplos Agents em lote      Nota: requer ambiente em execucao, Entrevista global - mesma pergunta para todos      Nota: requer ambiente em exec (+12 more)

### Community 56 - "normalize_report_attribution"
Cohesion: 0.16
Nodes (21): classify_direct_quotes(), _find_origin(), label_operational_deadlines(), normalize_report_attribution(), _normalize_text(), _normalize_text_for_deadline(), Gate de atribuicao para textos de relatorio., Classifica citacoes literais conforme presenca no corpus de evidencia. (+13 more)

### Community 57 - "report_content_repair.py"
Cohesion: 0.15
Nodes (27): Reparar inconsistencias deterministicas de conteudo do relatorio., repair_report_content_route(), _artifact(), _known_agents(), _known_platforms(), _known_rounds(), _metrics_for_report(), _metrics_sentence() (+19 more)

### Community 58 - "StrategicDensityGate"
Cohesion: 0.15
Nodes (13): Any, Gate deterministico de densidade estrategica para relatorios caros., Avalia se um relatorio entrega decisao superior ao obvio., Signal, StrategicDensityGate, test_actionable_adversarial_report_passes_density_gate(), test_actionable_report_with_alternative_vocabulary_passes_density_gate(), test_density_gate_returns_clear_portuguese_issue_labels() (+5 more)

### Community 59 - "PlatformActionLogger"
Cohesion: 0.09
Nodes (9): ActionLogger, get_logger(), PlatformActionLogger, Any, 动作日志记录器 用于记录OASIS模拟中每个Agent的动作，供后端监控使用  日志结构:     sim_xxx/     ├── twitter/, 动作日志记录器（兼容旧接口）     建议使用 SimulationLogManager 代替, 初始化日志记录器                  Args:             platform: 平台名称 (twitter/reddit), MaxTokensWarningFilter (+1 more)

### Community 60 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (12): getSimulationHistory(), containerStyle, historyContainer, historyError, hoveringCard, isExpanded, loadHistory(), loading (+4 more)

### Community 61 - "SimulationRunner"
Cohesion: 0.13
Nodes (21): get_internal_run_status(), Consulta o estado do runner da simulacao., Termina processo e subprocessos (cross-platform)                  Args:, Limpa todos os processos de simulacao em execucao                  Chamado ao fe, Obtem lista de IDs de simulacoes em execucao, Executor de simulacao          Responsabilidades:     1. Executar simulacao OASI, Obter estado de execucao, Iniciar simulacao                  Args:             simulation_id: ID da simula (+13 more)

### Community 62 - "ReportView.vue"
Cohesion: 0.10
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 63 - "GraphitiClient"
Cohesion: 0.07
Nodes (24): internal_health(), Healthcheck completo com dados de infra (exige token)., Inicializa o servico.          Args:             api_key: Mantido na assinatura, Inicializa o leitor.          Args:             api_key: Mantido na assinatura p, Inicializa o atualizador.          Args:             graph_id: Identificador do, Inicializa o servico.          Args:             api_key: Mantido na assinatura, GraphitiClient, Any (+16 more)

### Community 64 - "PowerCatalog"
Cohesion: 0.13
Nodes (16): get_power_catalog(), Expor poderes formais da missao., Selecao persistente de poderes e personas de uma missao., PowerCatalog, Any, Catalogo formal de poderes comerciais do Mirofish INTEIA., Expoe poderes estaveis e estimativa comercial de selecao., Testes do catalogo formal de poderes comerciais. (+8 more)

### Community 65 - "create_app"
Cohesion: 0.10
Nodes (32): codex_cli_path(), CodexPlannerUnavailable, _extract_agent_message(), is_available(), _parse_plan_json(), plan_with_codex_cli(), Any, RuntimeError (+24 more)

### Community 66 - "ReportDeliveryEvaluator"
Cohesion: 0.11
Nodes (9): Any, Path, Invariantes para evoluir a fronteira de entrega de relatorios., Asset read-only que resume os pontos de decisao de entrega., Score deterministico da fronteira de entrega cliente., ReportDeliveryAsset, ReportDeliveryConstraints, ReportDeliveryEvaluator (+1 more)

### Community 67 - "run_reddit_simulation"
Cohesion: 0.16
Nodes (24): add_manual_action(), count_manual_actions(), create_model(), execute_social_bootstrap(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), get_seed_posts_from_db() (+16 more)

### Community 68 - "simulation.js"
Cohesion: 0.16
Nodes (18): buildGraph(), generateOntology(), getGraphData(), getGraphStatus(), getTaskStatus(), API_TIMEOUTS, requestWithRetry(), service (+10 more)

### Community 69 - "test_pagination.py"
Cohesion: 0.16
Nodes (19): get_simulation_actions(), Obter historico de acoes dos Agents      Parametros de Query:         limit: qua, get_from_line(), get_limit(), get_offset(), Validação de parâmetros de paginação.  2026-04-18, Phase 7: evita OOM e DoS por, Retorna ?limit= validado no range [1, max_limit]., Retorna ?offset= validado no range [0, max_offset]. (+11 more)

### Community 70 - "LLMClient"
Cohesion: 0.14
Nodes (17): Inicializa o cliente LLM apenas quando necessario., LLMClient, parse_llm_json_response(), Any, Cliente de LLM com suporte a alias de modelos, timeout e retry., Normaliza JSON comum e SSE retornado por gateways OpenAI-compatible.          O, Envia requisicao em modo JSON e retorna objeto desserializado., Parseia JSON de LLM tolerando markdown, texto antes/depois e fences. (+9 more)

### Community 71 - "TokenUsage"
Cohesion: 0.09
Nodes (7): Rastreamento de consumo de tokens, custo tecnico e valor INTEIA., _round_brl(), _round_usd(), TokenPhase, TokenUsage, test_token_usage_calcula_total_corretamente(), test_token_usage_custo_usd_calculado()

### Community 72 - "InteractionView.vue"
Cohesion: 0.11
Nodes (19): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+11 more)

### Community 73 - "llm_proxy_v2.py"
Cohesion: 0.15
Nodes (19): chat(), ensure_required_defaults(), extract_schema(), get_required_fields(), _is_cooling(), _log(), _pick_model(), _provider_has_credentials() (+11 more)

### Community 74 - "GitOps"
Cohesion: 0.15
Nodes (11): GitOps, Path, Operacoes git para versionamento de experimentos AutoResearch., Inicializa repo git se nao existir., Salva estado atual do asset. Retorna hash do commit., Commita melhoria. Retorna hash do novo commit., Reverte asset para ultimo commit., Retorna historico de commits recentes. (+3 more)

### Community 75 - "run_parallel_simulation.py"
Cohesion: 0.11
Nodes (19): disable_oasis_logging(), _enrich_action_context(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation(), load_config(), Script de simulacao OASIS em paralelo para duas plataformas Executa simultaneame (+11 more)

### Community 76 - "ParallelIPCHandler"
Cohesion: 0.15
Nodes (11): main(), ParallelIPCHandler, Processador de comandos IPC para duas plataformas      Gerencia os ambientes de, Atualizar status do ambiente, Buscar comandos pendentes por polling, Obter o ambiente e agent_graph da plataforma especificada          Args:, Executar Interview em uma unica plataforma          Returns:             Diciona, Processar comando de entrevista de um unico Agente          Args:             co (+3 more)

### Community 77 - "scripts"
Cohesion: 0.10
Nodes (20): concurrently, description, devDependencies, concurrently, engines, node, license, name (+12 more)

### Community 78 - "warning"
Cohesion: 0.33
Nodes (6): fetch_all_edges(), fetch_all_nodes(), Any, Compatibility stub for legacy Zep SDK callers., Compatibility stub for legacy Zep SDK callers., test_zep_paging_compat_stubs_fail_closed()

### Community 79 - "SkillPromptEvaluator"
Cohesion: 0.13
Nodes (8): Path, Avaliador LLM-as-judge para qualidade de respostas de skills., Usa LLM avaliador para pontuar resposta em cada dimensao., Calcula score composto medio sobre todos os casos de teste., Asset: arquivo SKILL.md de uma skill., Extrai secoes editaveis por headings markdown., SkillPromptAsset, SkillPromptEvaluator

### Community 80 - "Home.vue"
Cohesion: 0.08
Nodes (20): setPendingUpload(), activePrompts, addFiles(), canSubmit, error, fileInput, files, formData (+12 more)

### Community 81 - "AgentAction"
Cohesion: 0.17
Nodes (7): get_run_status_detail(), Obter estado detalhado (com todas as acoes)      Para exibicao em tempo real no, Le acoes de um unico arquivo de acoes                  Args:             file_pa, Obtem historico completo de acoes de todas as plataformas (sem paginacao), Obtem historico de acoes (com paginacao)                  Args:             simu, Obtem linha do tempo da simulacao (resumo por rodada)                  Args:, Obtem estatisticas de cada Agent                  Returns:             Lista de

### Community 82 - "test_translation.py"
Cohesion: 0.15
Nodes (18): Traduz nomes SCREAMING_SNAKE_CASE de ingles para pt-BR., _translate_relation_name(), Testes unitarios para mapa de traducao de relacoes (Phase 6)., Garante que o lado pt-BR tambem segue SCREAMING_SNAKE_CASE (ontologia upstream)., Chaves devem ser uppercase para match com SCREAMING_SNAKE_CASE do Graphiti., Multiplas relacoes podem mapear pro mesmo pt-BR (ex: DEFENDS/ADVOCATES → DEFENDE, Mapa deve cobrir pelo menos 20 relacoes comuns., test_all_keys_are_uppercase() (+10 more)

### Community 83 - "AgentActivity"
Cohesion: 0.09
Nodes (7): AgentActivity, Any, Atualizador de memoria em grafo via Graphiti Server.      Monitora os logs de ac, Registro de atividade de um agente., Envia um lote de atividades ao Graphiti como mensagens., Converte a atividade em uma descricao textual adequada para o Graphiti., ZepGraphMemoryUpdater

### Community 84 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (13): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+5 more)

### Community 85 - "helenaExecutor.js"
Cohesion: 0.32
Nodes (16): executeBuildGraph(), executeContinueAnalysis(), executeCreateSimulation(), executeGenerateReport(), executeHelenaAction(), executeHelenaPlan(), executePrepareSimulation(), executeStartSimulation() (+8 more)

### Community 86 - "GeneticCopyAsset"
Cohesion: 0.14
Nodes (8): GeneticCopyAsset, GeneticCopyEvaluator, Path, Avaliador que roda o GA e mede fitness do campeao., Roda o GA e retorna score composto: fitness + cobertura., Verifica se o template_ag.py e valido., Asset: template_ag.py do algoritmo genetico., Extrai CONFIG, PESOS e trechos de fitness_persona.

### Community 87 - "build_decision_packet"
Cohesion: 0.29
Nodes (15): _build_convergence_assessment(), build_decision_packet(), _build_red_team_assessment(), _cap(), _clamp(), decision_packet_prompt_block(), _float_metric(), _positive_int() (+7 more)

### Community 88 - "mission_bundle.py"
Cohesion: 0.25
Nodes (14): _canonical_json(), _freeze_forecasts(), gerar_mission_bundle(), Any, Bundle final da missao com manifesto e hashes deterministicos., Calcula hash de texto ou JSON usando representacao canonica., Atalho funcional para gerar o manifesto final., sha256_item() (+6 more)

### Community 89 - "report_diagrams.py"
Cohesion: 0.22
Nodes (13): build_paperbanana_report_diagrams(), _compact_label(), count_report_diagrams(), ensure_minimum_report_diagrams(), paperbanana_diagram_metadata(), Any, PaperBanana-inspired diagram support for final MiroFish reports., Append the PaperBanana visual pack when a report has fewer diagrams. (+5 more)

### Community 90 - "._request"
Cohesion: 0.10
Nodes (28): filter_recovered_facts(), is_eco(), _normaliza(), Separa fato recuperado de eco do proprio prompt.  Por que existe: no caso Vale T, True quando o fato apenas devolve o que o prompt ja dizia.      Trecho literal d, Separa o que foi recuperado do que so devolveu o pedido., _termos(), Separa o que foi recuperado do que so devolve o proprio pedido.          No caso (+20 more)

### Community 91 - "ExperimentLog"
Cohesion: 0.15
Nodes (10): ExperimentLog, Any, Path, Log JSONL append-only para experimentos AutoResearch., Log crash-resilient de experimentos. Cada linha e um JSON independente., Appenda um resultado de experimento ao log., Le todos os experimentos do log., Retorna os N ultimos experimentos. (+2 more)

### Community 92 - "test_helena_control_api.py"
Cohesion: 0.23
Nodes (13): auth_headers(), test_acoes_destrutivas_e_travessia_de_path_sao_bloqueadas(), test_cancelamento_so_antes_da_execucao(), test_comando_repetido_ativo_nao_cria_redundancia(), test_idempotency_key_reapresenta_o_mesmo_comando(), test_payload_e_comando_tem_limites(), test_planejador_remove_acoes_redundantes_do_modelo(), test_planejamento_de_leitura_nao_exige_aprovacao() (+5 more)

### Community 93 - "Config"
Cohesion: 0.14
Nodes (19): Config, Configuracao principal do backend Flask., Valida configuracoes obrigatorias para o backend., main(), Ponto de entrada do backend MiroFish, _app(), Testes do contrato interno do harness MiroFish para consumidores service-to-serv, test_harness_evidence_bundle_404_sem_relatorio() (+11 more)

### Community 94 - "OntologyGenerator"
Cohesion: 0.29
Nodes (6): OntologyGenerator, Servico de geracao de ontologia Interface 1: Analisa conteudo textual e gera def, Gerador de ontologia     Analisa conteudo textual e gera definicoes de tipos de, test_gerador_usa_a_ontologia_judicial_sem_chamar_o_modelo(), FakeLLMClient, test_ontology_generator_expande_camadas_de_stakeholders()

### Community 95 - "simulation_runner.py"
Cohesion: 0.17
Nodes (31): _allowed_language(), _baseline_sources(), _blind_test_block(), build_vox_science_artifacts(), _canonical_sha256(), _claim_level(), _claim_policy_audit(), _clean_text() (+23 more)

### Community 96 - "test_report_exports_api.py"
Cohesion: 0.13
Nodes (19): create_report_export_route(), download_report_export_file_route(), list_report_exports_route(), Criar rascunho de export verificavel para um relatorio., Listar exports existentes sem expor caminhos internos., Verificar integridade e seguranca do bundle exportado., Baixar apenas arquivos allowlisted no manifest do export., verify_report_export_bundle_route() (+11 more)

### Community 97 - "MissionSelection"
Cohesion: 0.25
Nodes (7): MissionSelection, Any, Grava e recupera escolhas comerciais e sinteticas por simulacao., Testes da selecao persistente de missao., test_build_consolida_poderes_e_personas_sem_duplicar_ids(), test_load_sem_arquivo_retorna_estado_vazio(), test_save_e_load_preservam_missao()

### Community 98 - "FrontendPerfAsset"
Cohesion: 0.16
Nodes (6): FrontendPerfAsset, FrontendPerfConstraints, Path, Invariantes para otimizacao de performance frontend., Verifica se o build completa sem erros., Asset: vite.config.js e arquivos de config do frontend.

### Community 99 - "helena.js"
Cohesion: 0.23
Nodes (14): authConfig(), cancelHelenaCommand(), completeHelenaCommand(), executeHelenaCommand(), getHelenaContext(), listHelenaCommands(), openHelenaSession(), planHelenaCommand() (+6 more)

### Community 100 - "Any"
Cohesion: 0.10
Nodes (28): is_ausencia(), parse_relation(), True quando o valor e a negativa do proprio dado, nao o dado., Converte a relacao devolvida pelo modelo numa aresta tipada.      A versao anter, Junta o que veio dos pedacos, deduplicando por nome.          A sobreposicao ent, _extrator(), Proveniência com documento e folha — o que separa "a IA disse" de "está na fl. X, Primeira ocorrência sem âncora, segunda com: a folha precisa chegar. (+20 more)

### Community 101 - "Any"
Cohesion: 0.24
Nodes (4): Any, Construir grafo de forma assincrona.          Args:             text: Texto de e, Cria um ID local para fallback sem Graphiti., Cria um grafo local de esquema quando Graphiti nao esta acessivel.          O fa

### Community 102 - "Step1GraphBuild.vue"
Cohesion: 0.14
Nodes (10): creatingSimulation, graphAvailability, graphStats, handleEnterEnvSetup(), isDetailExpanded, logContent, logsExpanded, props (+2 more)

### Community 103 - "GraphBuilderService"
Cohesion: 0.31
Nodes (7): GraphBuilderService, Excluir grupo (equivale a excluir grafo)., Servico de construcao de grafo.     Responsavel por chamar a API REST do Graphit, Quando o grafo nao materializa, retorna os dados vazios (degradacao graciosa)., test_schema_fallback_graph_persiste_dados_locais(), test_wait_for_graph_materialization_accepts_populated_graph(), test_wait_for_graph_materialization_returns_empty_gracefully()

### Community 104 - "SimulationLogManager"
Cohesion: 0.24
Nodes (5): 模拟日志管理器     统一管理所有日志文件，按平台分离, 初始化日志管理器                  Args:             simulation_dir: 模拟目录路径, SimulationLogManager, CommandType, Constantes de tipos de comando

### Community 105 - "router/index.js"
Cohesion: 0.17
Nodes (7): cleanupFns, cursorEl, cursorLabel, neuralCanvas, app, router, routes

### Community 106 - "._build_graph_worker"
Cohesion: 0.18
Nodes (6): GraphInfo, Thread de trabalho para construcao do grafo., Criar grupo no Graphiti (grupos sao criados implicitamente na primeira mensagem), Envia o contexto da ontologia como mensagem de sistema.          O Graphiti nao, Adicionar texto ao grafo em lotes via POST /messages.          IMPORTANTE: Todos, Obter informacoes do grafo via busca ampla.

### Community 107 - "build_report_evolution_readiness"
Cohesion: 0.15
Nodes (24): build_helena_report_lab(), HelenaReportTheme, _index_html(), _now_iso(), _oracle_checks(), Any, Path, Helena/Efesto/Oracle validation lab for complex INTEIA HTML reports. (+16 more)

### Community 108 - "ZepGraphMemoryUpdater"
Cohesion: 0.10
Nodes (26): Divide o texto em pedacos sobrepostos, devolvendo (offset, trecho).      Existe, split_into_chunks(), _bruta(), As quatro correcoes que destravam o grafo, diagnosticadas no caso Vale Trading., O gate precisa distinguir leitura ancorada de alucinacao., Um pedaco que volta JSON quebrado nao pode zerar o grafo inteiro., Sem o aviso, o modelo trata dado local como fato recuperado do grafo., Nove PDFs concatenados construiam o grafo so a partir da capa do primeiro. (+18 more)

### Community 109 - "CostGuard"
Cohesion: 0.17
Nodes (5): CostGuard, Controle de custo para experimentos AutoResearch., Rastreia gastos e bloqueia quando budget atingido., Registra tokens consumidos e atualiza custo., Retorna True se ainda ha budget e tempo disponivel.

### Community 110 - "llm_client.py"
Cohesion: 0.19
Nodes (10): Modulo de utilitarios, _ChatChoice, _ChatMessage, _ChatResponse, _ChatUsage, _extract_balanced_json(), Cliente unificado de LLM.  Opera sobre provedores compativeis com a API OpenAI e, Tenta um provider especifico com max_retries retries. (+2 more)

### Community 111 - ".chat"
Cohesion: 0.20
Nodes (4): Resolve aliases internos de modelo para o nome real a ser chamado., Retorna lista de providers de fallback configurados via env.          Formato: [, Executa chamada ao provider via requests (compativel com OmniRouter).          E, Envia requisicao de chat e retorna texto limpo.

### Community 112 - "validate_uploaded_file"
Cohesion: 0.27
Nodes (9): InvalidFileContent, _looks_like_text(), Exception, Validacao de conteudo de upload por assinatura (magic bytes) e heuristica de tex, Conteudo do arquivo nao bate com a extensao declarada., Heuristica simples: decodifica em UTF-8 ou latin-1 e tem poucos nulos., Valida o conteudo do arquivo conforme a extensao declarada.      Args:         p, _read_header() (+1 more)

### Community 113 - "SimulationStatus"
Cohesion: 0.36
Nodes (8): PlatformType, Enum, str, SimulationStatus, _Project, _state(), test_history_limit_1_usa_modo_leve_por_padrao(), test_history_sinaliza_simulacao_ready_com_erro_como_bloqueada()

### Community 114 - "evaluate_section_grounding"
Cohesion: 0.12
Nodes (25): build_coverage_matrix(), Para cada tese: o que a sustenta, do que ela depende, o que a ataca.      Substi, aresta(), No, Substitui 'convicção 72%' por algo verificável e acionável., Responde 'o que fica órfão se o documento X não vier'., Grafo incompleto não pode quebrar o produto., Substitui a probabilidade fabricada por algo decidível. (+17 more)

### Community 115 - "FrontendPerfEvaluator"
Cohesion: 0.29
Nodes (4): FrontendPerfEvaluator, Build e mede performance. Maior score = melhor., Avaliador de performance: build time + bundle size., Retorna tamanho total do bundle em bytes.

### Community 116 - "ProxyHandler"
Cohesion: 0.29
Nodes (3): ProxyHandler, Proxy local que traduz chamadas OpenAI SDK (httpx) para requests. Resolve incomp, BaseHTTPRequestHandler

### Community 117 - "mirofish_smoke_check.py"
Cohesion: 0.43
Nodes (6): backend_python(), fetch_json(), main(), Path, Smoke check operacional do MiroFish.  Executa validacoes locais e, se MIROFISH_L, run_step()

### Community 118 - "Graphiti Service"
Cohesion: 0.47
Nodes (6): VPS Docker Compose, Graphiti Service, Mirofish Service, Neo4j Service, Docker Image Workflow, Graphiti Memory Graph

### Community 119 - "escapeHtml"
Cohesion: 0.47
Nodes (5): renderMarkdown(), renderMarkdown(), escapeHtml(), renderSafeMarkdown(), textToSafeHtml()

### Community 120 - "token_tracker.py"
Cohesion: 0.16
Nodes (21): _alvos(), _arestas(), _attr(), build_contradiction_map(), build_information_value(), build_omissions(), _citacao(), Contradicao (+13 more)

### Community 122 - ".path"
Cohesion: 0.40
Nodes (3): Path, Verifica se o asset modificado ainda respeita as restricoes., Caminho do asset principal.

### Community 123 - "createExportDraft"
Cohesion: 0.60
Nodes (5): createExportDraft(), formatExportError(), getExportId(), loadReportExports(), verifyExportBundle()

### Community 124 - "vercel.json"
Cohesion: 0.40
Nodes (4): buildCommand, installCommand, outputDirectory, rewrites

### Community 125 - ".wait_for_graph_materialization"
Cohesion: 0.25
Nodes (4): Aguardar o processamento assincrono do Graphiti.          Faz polling em GET /ep, Espera o Graphiti processar o input e valida se o grafo ganhou conteudo., Obter dados completos do grafo.          No Graphiti, isso e feito via POST /sea, Detecta se o texto esta em ingles e traduz para pt-BR usando LLM barato.

### Community 128 - "closeModal"
Cohesion: 0.50
Nodes (4): closeModal(), goToProject(), goToReport(), goToSimulation()

### Community 129 - "get_graph_status"
Cohesion: 0.11
Nodes (16): get_postura(), Postura, Postura da analise: de que lugar o sistema fala.  Por que existe: a consulta do, Postura pelo id, caindo no padrao quando nao reconhecida., As tres, na ordem em que se leem: sustentacao, isencao, ataque., todas(), Postura da análise — o erro de mandato do caso Vale Trading.  A consulta encerra, Perito do juízo é quem o juízo nomeia, não quem o escritório contrata. (+8 more)

### Community 131 - "report_section_workers"
Cohesion: 0.16
Nodes (20): build_timeline(), _data_ordenavel(), Cronologia dos atos, ordenada por data.      Ato sem data reconhecivel vai para, Normaliza para AAAA-MM-DD, unica forma que ordena como texto.      Data so com a, Os quatro produtos do escritório, derivados do grafo do caso.  A saída era um re, Das 752 datas extraidas do acervo da Vale, so 83 vinham em dd/mm/aaaa.     Ler s, 544 das 551 datas que sobravam no acervo vinham assim., A ausência da data é informação: o ato existe e não foi possível situá-lo. (+12 more)

### Community 133 - "Any"
Cohesion: 0.14
Nodes (12): main(), Neo4jGraphIdFixer, Any, Gera relatório das correções., Ferramenta para corrigir group_ids em Neo4j., Inicializa conexão com Neo4j., Fecha conexão com Neo4j., Retorna mapeamento de group_id -> contagem de nós. (+4 more)

### Community 137 - "approveAndExecute"
Cohesion: 0.67
Nodes (3): addExecutionLog(), approveAndExecute(), summarizeResult()

### Community 140 - ".delete_group"
Cohesion: 0.16
Nodes (17): evaluate_abm_applicability(), Quando a simulacao de agentes vale como evidencia, e quando nao vale.  Por que e, Diz se a simulacao de agentes deve rodar para este dominio.      `validacao_decl, VeredictoDoAbm, Simulação de agentes só vale onde há difusão.  No caso Vale Trading, 36 tweets s, Bloquear sem dizer o que fazer no lugar não ajuda ninguém., O ABM não é descartado: segue no produto onde nasceu., Nenhuma etapa pode reescrever a aplicabilidade em runtime. (+9 more)

### Community 149 - "Exception"
Cohesion: 0.15
Nodes (18): build_prompt(), chat_completions(), codex_path(), extract_message(), extract_usage(), health(), Any, Ponte HTTP compativel com a API OpenAI que atende pela assinatura do Codex CLI. (+10 more)

### Community 150 - "Path"
Cohesion: 0.16
Nodes (16): assert_report_system_ready(), compact_evidence_for_manifest(), _contract_layers(), _count_csv_rows(), _count_json_array(), evaluate_report_system_gate(), _file_info(), Any (+8 more)

### Community 152 - "ValueError"
Cohesion: 0.31
Nodes (16): Verify path safety, expected files, hashes, and renderer metadata., verify_report_export_bundle(), _create_export(), _decision_packet(), _load_bundle_manifest(), _publishable_report(), report_store(), test_verifier_accepts_valid_export_bundle() (+8 more)

### Community 159 - "render_safe_markdown"
Cohesion: 0.20
Nodes (13): detect_unsafe_markdown_patterns(), Renderizacao segura de Markdown simples para superficies HTML., Lista padroes perigosos encontrados antes do escape., Converte Markdown limitado em HTML escapado e com metadata auditavel., _render_inline(), render_safe_markdown(), SafeMarkdownRenderResult, test_detect_unsafe_markdown_patterns_flags_iframe_and_data_url() (+5 more)

### Community 160 - "Any"
Cohesion: 0.18
Nodes (8): Any, Retorna apenas acoes de agentes (com agent_name)., Busca simples por keyword nas acoes., Retorna fatos formatados para uso no prompt do ReportAgent., Retorna estatisticas da simulacao., Resume a tabela trace dos bancos OASIS por plataforma.          O actions.jsonl, Estima o pulso induzido para separar lastro emergente de bootstrap., Carrega todas as acoes de Twitter e Reddit.

### Community 162 - "report_bundle_verifier.py"
Cohesion: 0.22
Nodes (15): _check(), _now_iso(), _persist_result(), Any, Exception, Path, Verification for generated report export bundles., Base verification error. (+7 more)

### Community 163 - "SimulationIPCServer"
Cohesion: 0.16
Nodes (9): Servidor IPC de simulacao (usado pelo lado do script de simulacao)      Consulta, Inicializar servidor IPC          Args:             simulation_dir: Diretorio de, Marcar servidor como em execucao, Marcar servidor como parado, Atualizar arquivo de estado do ambiente, Enviar resposta          Args:             response: Resposta IPC, Enviar resposta de sucesso, Enviar resposta de erro (+1 more)

### Community 164 - "resolve_delivery_governance"
Cohesion: 0.21
Nodes (12): DeliveryGovernancePolicy, normalize_delivery_mode(), Any, Politica de entrega para separar relatorio cliente de diagnostico tecnico., Contrato aplicado ao gate antes de qualquer relatorio sair do sistema., Normaliza nomes de modo sem permitir enfraquecimento acidental., Resolve a politica efetiva combinando config da simulacao, API e ambiente., resolve_delivery_governance() (+4 more)

### Community 165 - "loads_first_object"
Cohesion: 0.15
Nodes (13): loads_first_object(), Any, Le o primeiro objeto JSON, tolerando o que o modelo emenda em volta.      Tres a, Extrair entidades concretas do texto usando LLM.          Args:             text, Extrai de um pedaco. Falha isolada nao derruba o corpus inteiro., Extra data" derrubou 3 dos 1.164 pedacos do acervo da Vale., r'''O OCR deixa barra que nao inicia escape valido, como em R\$., Pedir copia literal trouxe aspa junto e partiu o objeto no meio. Perder a     en (+5 more)

### Community 166 - "simulation_data_reader.py"
Cohesion: 0.20
Nodes (9): Exporta uma sintese em portugues com contagens por status., _distinct_n(), _normalize_words(), _normalized_entropy(), Leitor de dados de simulacao direto dos arquivos actions.jsonl. Substitui buscas, Gera um resumo textual dos dados da simulacao para contexto LLM., Mede diversidade comportamental e semantica da simulacao.          Inspirado no, Conta acoes por entity_type usando simulation_config.json quando existir. (+1 more)

### Community 167 - "PageSpan"
Cohesion: 0.15
Nodes (11): Mesmo texto de `extract_from_files`, mais o indice de paginas.          Quem ing, locate_page(), PageSpan, Onde uma pagina de um documento comeca e termina no corpus concatenado., Citacao processual quando o carimbo existe; caminho do PDF quando nao., Referencia completa: citacao processual mais onde conferir no arquivo., Documento e pagina de um offset do corpus, ou None fora de qualquer pagina., O cabeçalho de documento não pertence a nenhuma folha. (+3 more)

### Community 168 - "test_helena_reasoning_effort.py"
Cohesion: 0.19
Nodes (13): _api_key(), _captured_kwargs(), Esforco de raciocinio da Helena, isolado do resto do sistema., Intercepta o payload enviado ao provider., A Helena sobe o proprio esforco sem alterar o dos demais consumidores., Quem nao pediu nada nao muda de comportamento., reasoning_effort e especifico do Luna; outros modelos recebem temperatura., Com esforco alto o raciocinio consome a mesma cota da resposta. O teto     anter (+5 more)

### Community 169 - "find_excerpt"
Cohesion: 0.15
Nodes (13): find_excerpt(), Localiza a entidade dentro do pedaco que a originou.      Devolve None quando na, Nome que nao aparece no texto foi inventado, nao extraido., test_ancoragem_ignora_diferenca_de_caixa(), test_entidade_ausente_do_texto_nao_ganha_ancora(), test_entidade_presente_no_texto_recebe_trecho_e_offset(), Uma tese e nomeada por parafrase e uma norma por forma extensa; nenhuma das, Evidencia parafraseada e alucinacao: nao pode virar pincite. (+5 more)

### Community 170 - "ForecastLedger"
Cohesion: 0.27
Nodes (11): _enrich_forecast_ledger_payload(), Completa artefatos antigos de forecast com calibracao e chart_data., ForecastLedger, Registro em memoria com deduplicacao por id estavel., test_forecast_ledger_calculates_brier_and_log_loss_for_resolved_forecast(), test_forecast_ledger_deduplicates_equal_forecasts(), test_forecast_ledger_exports_calibration_summary_and_chart_data(), test_forecast_ledger_exports_portuguese_summary_by_status() (+3 more)

### Community 171 - "AtoProcessual"
Cohesion: 0.17
Nodes (10): AtoProcessual, _e_tautologica(), True quando a descricao nao diz nada alem do que a chave ja dizia.      Retirar, O ato diz o que aconteceu, e nao apenas que aconteceu.          Nao serve para d, _ato(), Uma tabela de andamentos do Evento 96 virou 456 pseudo-atos assim., Sem descricao nao ha o que julgar; nao e o mesmo que tautologia., test_ato_que_diz_o_que_aconteceu_e_substantivo() (+2 more)

### Community 172 - "build_judicial_ontology"
Cohesion: 0.23
Nodes (11): _aresta(), build_judicial_ontology(), _entidade(), Any, Ontologia de processo judicial.  Por que existe: a ontologia padrao descreve gen, Ontologia fixa do dominio processual.      Fixa de proposito: os elementos de um, Substitui a probabilidade fabricada por valor da informação., test_arestas_dizem_o_que_sustenta_e_o_que_derruba() (+3 more)

### Community 173 - "test_judicial_ontology.py"
Cohesion: 0.24
Nodes (10): is_material_processual(), True quando o material tem densidade forense suficiente., Material processual usa ontologia de processo, não de rede social.  A ontologia, Autos' e 'petição' aparecem em texto comum; exigir dois evita falso positivo., É a pergunta que a ontologia social não sabe responder., test_material_do_caso_vale_e_processual(), test_material_nao_forense_nao_e_confundido(), test_tese_pode_ficar_orfa_de_documento() (+2 more)

### Community 174 - "normalize_type"
Cohesion: 0.18
Nodes (11): normalize_type(), Casa o tipo devolvido pelo modelo com o da ontologia, ignorando acento.      O m, O mesmo conceito aparecia partido em dois no grafo: Orgao e Órgão., Não é filtro: tipo desconhecido continua visível para diagnóstico., FUNDAMENTA_SEM e FUNDAMENTAMENTA_SE_EM viraram arestas proprias no acervo., O corte precisa ser alto o bastante para nao fundir tipos distintos., test_sem_lista_de_permitidos_nada_muda(), test_tipo_fora_da_ontologia_e_preservado() (+3 more)

### Community 175 - "build_case_products"
Cohesion: 0.22
Nodes (8): build_case_products(), Os quatro produtos, mais a contagem do que esta ancorado nos autos.      `anchor, Pacote construído sobre entidades sem ponte não é utilizável numa peça., O ato existe e a data e boa; separar nao e descartar., test_ato_generico_continua_na_cronologia(), test_grafo_vazio_produz_pacote_vazio_e_nao_inventado(), test_pacote_conta_o_que_esta_ancorado_nos_autos(), test_pacote_traz_os_quatro_produtos()

### Community 176 - "TextProcessor"
Cohesion: 0.22
Nodes (5): Extrair texto de multiplos arquivos, Dividir texto em blocos          Args:             text: Texto original, Pre-processar texto         - Remover espacos em branco excessivos         - Pad, Obter estatisticas do texto, TextProcessor

### Community 177 - "test_report_exporter.py"
Cohesion: 0.47
Nodes (8): _decision_packet(), _publishable_report(), report_store(), _save_publishable_report(), test_download_path_uses_manifest_allowlist(), test_export_blocks_unpublishable_report(), test_export_creates_draft_with_safe_html_and_manifest(), test_list_exports_does_not_expose_internal_path()

### Community 178 - "_first_non_empty"
Cohesion: 0.29
Nodes (8): _default_llm_api_key(), _default_llm_base_url(), _default_llm_model_name(), _first_non_empty(), Retorna o primeiro valor nao vazio., Escolhe o gateway padrao de LLM priorizando OmniRoute., Escolhe a chave padrao de LLM priorizando o token operacional da INTEIA., Escolhe o modelo padrao conforme o gateway configurado.

### Community 179 - "._ensure_log_file"
Cohesion: 0.25
Nodes (4): Inicializa o registrador de log de console          Args:             report_id:, Garante que o diretorio do arquivo de log existe, Configura o handler de arquivo para gravar logs simultaneamente em arquivo, Inicializa o registrador de logs          Args:             report_id: ID do rel

### Community 180 - "test_phase03_smoke.py"
Cohesion: 0.25
Nodes (6): Vox Science helpers for public-data grounded synthetic harness artifacts., Smoke test ponta-a-ponta: build_vox_science_artifacts gera os 11 artefatos + tod, Construtos de violacao acionam blockers no science_gate., Builder produz todos 11 artefatos + 8 campos novos R1-R8., test_smoke_e2e_fase03_dpd_violation_e_blind_leak_bloqueiam_gate(), test_smoke_e2e_fase03_todos_artefatos_e_campos_novos()

### Community 181 - ".generate"
Cohesion: 0.33
Nodes (4): Any, Gera a definicao de ontologia          Args:             document_texts: Lista d, Constroi a mensagem do usuario, Valida e pos-processa o resultado

### Community 182 - "_count_anchored_nodes"
Cohesion: 0.29
Nodes (7): _count_anchored_nodes(), Quantos nos do grafo tem trecho verbatim do corpus.      Devolve None quando a c, Nós existirem não basta: sem trecho de origem não há como citar fonte., Ausência de medida não pode ser lida como ausência de ancoragem., test_conta_apenas_nos_ancorados(), test_grafo_indisponivel_nao_vira_acusacao(), test_grafo_sem_nenhum_no_ancorado()

### Community 183 - "_ok"
Cohesion: 0.38
Nodes (7): _fala(), _ok(), _stream(), test_fluxo_sem_fala_do_agente_nao_vira_resposta_vazia(), test_resposta_no_formato_openai(), test_usage_ausente_vira_zero(), test_vale_a_ultima_fala_do_agente()

### Community 184 - "CoberturaDaTese"
Cohesion: 0.33
Nodes (3): CoberturaDaTese, Sem nada que a sustente, a tese nao tem como ser afirmada., Contraditada e sem lastro suficiente para responder.

### Community 187 - "_Completed"
Cohesion: 0.50
Nodes (3): _Completed, Erro de credencial nao pode virar 200 com texto de erro no conteudo., test_falha_do_codex_vira_502()

## Knowledge Gaps
- **471 isolated node(s):** `Signal`, `mirofish-backend`, `name`, `private`, `version` (+466 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `report_agent.py`, `build_executive_package`, `report.py`, `datetime`, `graph.py`, `ProjectManager`, `Path`, `EntityNode`, `SimulationIPCClient`, `simulation.py`, `resolve_delivery_governance`, `simulation_data_reader.py`, `test_helena_reasoning_effort.py`, `cli.py`, `PowerCatalog`, `create_app`, `test_helena_control_api.py`, `OntologyGenerator`, `llm_client.py`, `.chat`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `LLMClient` to `report_agent.py`, `Any`, `test_helena_reasoning_effort.py`, `cli.py`, `datetime`, `graph.py`, `llm_client.py`, `.chat`, `TokenTracker`, `EntityNode`, `ZepGraphiti`, `.wait_for_graph_materialization`, `OntologyGenerator`, `GraphitiClient`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `SimulationManager` connect `SimulationManager` to `report_agent.py`, `ReportManager`, `build_executive_package`, `test_report_quality.py`, `report.py`, `datetime`, `OasisProfileGenerator`, `graph.py`, `ProjectManager`, `report_system_gate.py`, `Path`, `EntityNode`, `SimulationIPCClient`, `simulation.py`, `SimulationRunState`, `Any`, `.log`, `SimulationConfigGenerator`, `Flask`, `repair_report_finalization`, `SimulationRunner`, `test_helena_control_api.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `ReportManager` (e.g. with `ExecutivePackageConflict` and `ExecutivePackageError`) actually correct?**
  _`ReportManager` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `ReportAgent` (e.g. with `ForecastLedger` and `MissionBundle`) actually correct?**
  _`ReportAgent` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `SimulationManager` (e.g. with `HelenaCommandStore` and `HelenaConflictError`) actually correct?**
  _`SimulationManager` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `SimulationRunner` (e.g. with `Report` and `ReportAgent`) actually correct?**
  _`SimulationRunner` has 31 INFERRED edges - model-reasoned connections that need verification._