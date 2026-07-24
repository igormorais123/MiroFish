# Graph Report - .  (2026-07-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3951 nodes · 8496 edges · 149 communities (135 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 544 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7290bb09`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Step4Report.vue
- Step3Simulation.vue
- build_executive_package
- test_report_quality.py
- Step5Interaction.vue
- ReportManager
- SimulationRunner
- ZepToolsService
- Config
- IPCResponse
- helena.py
- OasisProfileGenerator
- evaluate_report_method_checklist
- codex_proxy.py
- SimulationManager
- report_quality.py
- graph.py
- report.py
- IPCHandler
- MainView.vue
- IPCHandler
- simulation.py
- Asset
- GraphitiClient
- ZepGraphiti
- ReportLogger
- HelenaCommandCenter.vue
- Step2EnvSetup.vue
- SimulationDataReader
- TaskManager
- internal.py
- Flask
- report_system_gate.py
- AgentActivity
- harness_evidence_bundle.py
- ForecastLedger
- EntityNode
- test_vox_science_artifacts.py
- run_reddit_simulation
- normalize_report_attribution
- SimulationRunView.vue
- artifacts.py
- LLMClient
- simulation_runner.py
- cli.py
- frontend/package.json
- TokenTracker
- ._build_graph_worker
- RalphMethodEvaluator
- report_content_repair.py
- GoldenCaseLoader
- Any
- test_retry.py
- HookifyEvaluator
- report.js
- SimulationView.vue
- test_vox_metrics.py
- TokenUsage
- InteractionView.vue
- report_exporter.py
- StrategicDensityGate
- PlatformActionLogger
- HistoryDatabase.vue
- PowerPersonaCatalog
- ParallelIPCHandler
- .check_env_alive
- ReportView.vue
- ApifyEnricher
- repair_report_finalization
- ReportDeliveryEvaluator
- simulation.js
- Any
- test_pagination.py
- test_helena_control_api.py
- llm_proxy_v2.py
- PowerCatalog
- test_translation.py
- FileParser
- GitOps
- scripts
- doStartSimulation
- test_report_exports_api.py
- SkillPromptEvaluator
- Home.vue
- mission_bundle.py
- GraphPanel.vue
- audit_report_evidence
- build_report_evolution_readiness
- GeneticCopyAsset
- helenaExecutor.js
- build_decision_packet
- create_project_from_briefing
- report_agent.py
- ExperimentLog
- jaccard_similarity
- extract_numeric_claims
- quote_supported_by_evidence
- FrontendPerfAsset
- report_bundle_verifier.py
- authConfig
- OntologyGenerator
- Step1GraphBuild.vue
- test_internal_harness_api.py
- SimulationLogManager
- TextProcessor
- CostGuard
- llm_client.py
- loadQualityGate
- ReportStatus
- .get_all_actions
- extract_direct_quotes
- test_phase03_smoke.py
- run_preset
- HarnessEvidenceBundleNotFound
- FrontendPerfEvaluator
- run_parallel_simulation.py
- InteiaBackground.vue
- PlatformSimulation
- ProxyHandler
- mirofish_smoke_check.py
- getPowerCatalog
- escapeHtml
- .path
- GraphBuilderService
- getPowerPersonaCatalog
- vercel.json
- getMissionSelection
- createExportDraft
- closeModal
- phase03_e2e_validation.py
- smoke_test.sh
- start_mirofish.sh
- autoresearch/__init__.py
- targets/__init__.py
- conftest.py
- vite.config.js
- mirofish-reconcile-check.sh
- stop_mirofish.sh
- mirofish-backend

## God Nodes (most connected - your core abstractions)
1. `ReportManager` - 127 edges
2. `ReportAgent` - 94 edges
3. `SimulationManager` - 84 edges
4. `error()` - 84 edges
5. `SimulationRunner` - 76 edges
6. `Report` - 75 edges
7. `PowerPersonaCatalog` - 58 edges
8. `TokenTracker` - 54 edges
9. `ReportStatus` - 53 edges
10. `Config` - 49 edges

## Surprising Connections (you probably didn't know these)
- `health()` --indirect_call--> `_metrics()`  [INFERRED]
  codex_proxy.py → backend/app/services/vox_science/artifacts.py
- `metrics()` --indirect_call--> `_metrics()`  [INFERRED]
  codex_proxy.py → backend/app/services/vox_science/artifacts.py
- `LunaOpenAIClient` --uses--> `LLMClient`  [INFERRED]
  deploy/graphiti_patches/zep_graphiti.py → backend/app/utils/llm_client.py
- `ZepGraphiti` --uses--> `LLMClient`  [INFERRED]
  deploy/graphiti_patches/zep_graphiti.py → backend/app/utils/llm_client.py
- `report_store()` --indirect_call--> `ReportManager`  [INFERRED]
  backend/tests/test_executive_package.py → backend/app/services/report_agent.py

## Import Cycles
- None detected.

## Communities (149 total, 14 thin omitted)

### Community 0 - "Step4Report.vue"
Cohesion: 0.01
Nodes (130): activeExport, activeExportId, activeExportVerification, activeSectionIndex, activeStep, agentLogLine, agentLogs, auditIssues (+122 more)

### Community 1 - "Step3Simulation.vue"
Cohesion: 0.03
Nodes (60): actionIds, allActions, avgSecondsPerRound, canGenerateReport, chronologicalActions, diversityMetrics, effectiveMinutesPerRound, estimatedMinutesLeft (+52 more)

### Community 2 - "build_executive_package"
Cohesion: 0.05
Nodes (75): allowed_executive_package_file_path(), build_executive_package(), _evidence_annex_markdown(), ExecutivePackageConflict, ExecutivePackageError, ExecutivePackageInvalidPath, ExecutivePackageNotFound, load_executive_package_manifest() (+67 more)

### Community 3 - "test_report_quality.py"
Cohesion: 0.03
Nodes (75): is_substantive_section_response(), Exception, Report Agent - Agent de geracao de relatorios de simulacao      Utiliza o padrao, Inicia uma sessao isolada do medidor sem zerar consumo global., Remove o contexto ativo do medidor desta instancia., Remove o conteudo final bruto da resposta antes de registra-la no agent_log., Analisa chamadas de ferramenta a partir da resposta do LLM          Formatos sup, Valida se o JSON analisado e uma chamada de ferramenta valida (+67 more)

### Community 4 - "Step5Interaction.vue"
Cohesion: 0.04
Nodes (70): getAgentLog(), getReport(), getReportEvolutionReadiness(), getReportSections(), repairReportContent(), getSimulationProfilesRealtime(), interviewAgents(), activeReportTool (+62 more)

### Community 5 - "ReportManager"
Cohesion: 0.05
Nodes (57): download_report(), get_mission_bundle(), get_report_artifact(), get_report_sections(), list_report_artifacts(), Gerar manifesto final da missao a partir dos artefatos do relatorio., Baixar relatorio (formato Markdown)      Retorna arquivo Markdown, Obter lista de secoes ja geradas (saida por secoes)      O frontend pode consult (+49 more)

### Community 6 - "SimulationRunner"
Cohesion: 0.09
Nodes (29): Iniciar execucao da simulacao      Requisicao (JSON):         {             "sim, start_simulation(), Termina processo e subprocessos (cross-platform)                  Args:, Limpa logs de execucao da simulacao (para forcar reinicio)                  Remo, Limpa todos os processos de simulacao em execucao                  Chamado ao fe, Registrar funcao de limpeza                  Chamado ao iniciar Flask, garante l, Obtem lista de IDs de simulacoes em execucao, Executor de simulacao          Responsabilidades:     1. Executar simulacao OASI (+21 more)

### Community 7 - "ZepToolsService"
Cohesion: 0.05
Nodes (35): AgentInterview, EdgeInfo, NodeInfo, Any, Servicos de busca e leitura do grafo usados pelo Report Agent.  Ferramentas cent, Executa uma busca simples e leve., Entrevista agentes simulados via API real do OASIS.          O fluxo:         1., Limpa wrappers JSON de tool call e extrai o conteudo real. (+27 more)

### Community 8 - "Config"
Cohesion: 0.05
Nodes (52): Config, _default_llm_api_key(), _default_llm_base_url(), _default_llm_model_name(), _env_flag(), _first_non_empty(), _parse_alias_map(), Gerenciamento central de configuracao.  Carrega variaveis de ambiente a partir d (+44 more)

### Community 9 - "IPCResponse"
Cohesion: 0.10
Nodes (17): IPCCommand, IPCResponse, Any, Enviar comando e aguardar resposta          Args:             command_type: Tipo, Enviar comando de entrevista para um unico Agent          Args:             agen, Enviar comando de entrevista em lote          Args:             interviews: List, Enviar comando de fechamento do ambiente          Args:             timeout: Tem, Servidor IPC de simulacao (usado pelo lado do script de simulacao)      Consulta (+9 more)

### Community 10 - "helena.py"
Cohesion: 0.10
Nodes (46): cancel_helena_command(), complete_helena_command(), _disabled_response(), _error_response(), execute_helena_command(), get_helena_command(), get_helena_context(), get_helena_status() (+38 more)

### Community 11 - "OasisProfileGenerator"
Cohesion: 0.05
Nodes (32): OasisAgentProfile, OasisProfileGenerator, Any, callable, Salva Profile em arquivo (escolhe formato correto por plataforma)          Requi, Salva Twitter Profile em formato CSV (conforme OASIS oficial)          Campos CS, Padroniza campo gender para formato ingles exigido pelo OASIS          OASIS exi, Salva Reddit Profile em formato JSON          Usa formato consistente com to_red (+24 more)

### Community 12 - "evaluate_report_method_checklist"
Cohesion: 0.13
Nodes (30): _artifact_names(), build_report_delivery_packet(), Any, Pacote de decisao de entrega para relatorios., Consolida estado de entrega sem promover rascunho a entrega cliente., _verified_bundle(), _artifact_passes(), _build_payload() (+22 more)

### Community 13 - "codex_proxy.py"
Cohesion: 0.06
Nodes (47): main(), Neo4jGraphIdFixer, Any, Gera relatório das correções., Ferramenta para corrigir group_ids em Neo4j., Inicializa conexão com Neo4j., Fecha conexão com Neo4j., Retorna mapeamento de group_id -> contagem de nós. (+39 more)

### Community 14 - "SimulationManager"
Cohesion: 0.06
Nodes (37): close_simulation_env(), get_mission_selection(), get_simulation(), get_simulation_quality(), Parar simulacao      Requisicao (JSON):         {             "simulation_id": ", Obter poderes e personas escolhidos para a missao., Salvar poderes e personas escolhidos para a missao., Fechar ambiente de simulacao      Envia comando de fechamento, saindo do modo de (+29 more)

### Community 15 - "report_quality.py"
Cohesion: 0.29
Nodes (13): _claim_categories(), _claim_number_value(), _coerce_positive_int(), _first_positive_metric(), _flatten_numeric_metrics(), _known_platforms(), _metric_categories(), _nested_mapping() (+5 more)

### Community 16 - "graph.py"
Cohesion: 0.04
Nodes (60): allowed_file(), delete_project(), generate_ontology(), get_project(), get_task(), list_projects(), list_tasks(), Rotas de API relacionadas ao grafo de conhecimento Utiliza mecanismo de contexto (+52 more)

### Community 17 - "report.py"
Cohesion: 0.04
Nodes (69): _build_power_persona_catalog(), build_power_persona_context(), _build_power_persona_context_from_payload(), _build_power_selection_from_payload(), chat_with_report_agent(), check_report_status(), create_executive_package_route(), delete_report() (+61 more)

### Community 18 - "IPCHandler"
Cohesion: 0.06
Nodes (30): CommandType, IPCHandler, main(), MaxTokensWarningFilter, Any, Script de simulacao OASIS Twitter com configuracoes predefinidas Este script le, Constantes de tipos de comando, Processador de comandos IPC (+22 more)

### Community 19 - "MainView.vue"
Cohesion: 0.09
Nodes (37): clearPendingUpload(), getPendingUpload(), state, addLog(), buildProgress, currentPhase, currentProjectId, currentStep (+29 more)

### Community 20 - "IPCHandler"
Cohesion: 0.06
Nodes (30): CommandType, IPCHandler, main(), MaxTokensWarningFilter, Any, Script de simulacao OASIS Reddit com configuracoes predefinidas Este script le o, Constantes de tipos de comando, Processador de comandos IPC (+22 more)

### Community 21 - "simulation.py"
Cohesion: 0.06
Nodes (40): _assess_simulation_health(), _build_latest_report_index(), create_simulation(), download_simulation_config(), generate_profiles(), get_entities_by_type(), get_entity_detail(), get_graph_entities() (+32 more)

### Community 22 - "Asset"
Cohesion: 0.08
Nodes (28): ABC, AutoResearch Engine — Loop autonomo de experimentacao.  Ciclo: hipotese (LLM) →, Asset, Constraints, Evaluator, ExperimentResult, Classes base abstratas para alvos de AutoResearch., Resultado de um unico experimento. (+20 more)

### Community 23 - "GraphitiClient"
Cohesion: 0.06
Nodes (26): get_graph_status(), Retorna estado operacional do backend de grafo., internal_health(), Healthcheck completo com dados de infra (exige token)., Inicializa o servico.          Args:             api_key: Mantido na assinatura, Inicializa o leitor.          Args:             api_key: Mantido na assinatura p, Inicializa o servico.          Args:             api_key: Mantido na assinatura, GraphitiClient (+18 more)

### Community 24 - "ZepGraphiti"
Cohesion: 0.07
Nodes (30): AddEntityNodeRequest, AddMessagesRequest, add_entity_node(), add_messages(), AsyncWorker, clear(), delete_entity_edge(), delete_episode() (+22 more)

### Community 25 - "ReportLogger"
Cohesion: 0.08
Nodes (17): Obtem o tempo decorrido desde o inicio (em segundos), Registra uma entrada de log          Args:             action: Tipo de acao, ex:, Registra o inicio da geracao do relatorio, Registra o inicio do planejamento do sumario, Registra as informacoes de contexto obtidas durante o planejamento, Registra a conclusao do planejamento do sumario, Registra o inicio da geracao de uma secao, Registra o processo de raciocinio ReACT (+9 more)

### Community 26 - "HelenaCommandCenter.vue"
Cohesion: 0.05
Nodes (36): getHelenaStatus(), approvalToken, authenticated, availabilityClass, availabilityLabel, busy, closePanel(), command (+28 more)

### Community 27 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (39): getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles, emit (+31 more)

### Community 28 - "SimulationDataReader"
Cohesion: 0.07
Nodes (45): _distinct_n(), _normalize_words(), _normalized_entropy(), Any, Leitor de dados de simulacao direto dos arquivos actions.jsonl. Substitui buscas, Retorna apenas acoes de agentes (com agent_name)., Gera um resumo textual dos dados da simulacao para contexto LLM., Busca simples por keyword nas acoes. (+37 more)

### Community 29 - "TaskManager"
Cohesion: 0.05
Nodes (42): build_graph(), Interface 2: Construir grafo a partir do project_id      Requisicao (JSON):, build_internal_graph(), create_internal_simulation(), prepare_internal_simulation(), Dispara a construcao do grafo para um projeto interno., Cria uma simulacao vinculada a um projeto existente., Dispara a preparacao da simulacao para consumo interno. (+34 more)

### Community 30 - "internal.py"
Cohesion: 0.08
Nodes (30): _build_lenia_export(), _compute_lenia_signals(), export_project_to_lenia(), export_simulation_to_lenia(), get_harness_evidence_bundle(), get_internal_project(), get_internal_run_status(), get_internal_simulation() (+22 more)

### Community 31 - "Flask"
Cohesion: 0.12
Nodes (24): Registro de blueprints da API., get_report_delivery_package(), get_report_evolution_readiness(), Obter pacote consolidado de entregabilidade do relatorio., Obter estado read-only para evoluir a analise do relatorio., Reparar finalizacao do relatorio sem chamar LLM., repair_report_finalization_route(), get_simulation_readiness() (+16 more)

### Community 32 - "report_system_gate.py"
Cohesion: 0.08
Nodes (40): _enum_value(), evaluate_decision_readiness(), _next_action(), Any, Estado de prontidao de decisao para simulacoes., Consolida simulacao, gate e relatorio em um estado de produto., DeliveryGovernancePolicy, normalize_delivery_mode() (+32 more)

### Community 33 - "AgentActivity"
Cohesion: 0.08
Nodes (8): AgentActivity, Any, Atualizador de memoria em grafo via Graphiti Server.      Monitora os logs de ac, Inicializa o atualizador.          Args:             graph_id: Identificador do, Registro de atividade de um agente., Envia um lote de atividades ao Graphiti como mensagens., Converte a atividade em uma descricao textual adequada para o Graphiti., ZepGraphMemoryUpdater

### Community 34 - "harness_evidence_bundle.py"
Cohesion: 0.18
Nodes (30): _absolute_api_url(), _artifact_gate_passes(), _artifact_tag(), _artifact_url(), _build_evidence(), _build_forecasts(), _build_graph(), build_harness_evidence_bundle() (+22 more)

### Community 35 - "ForecastLedger"
Cohesion: 0.10
Nodes (29): _enrich_forecast_ledger_payload(), Completa artefatos antigos de forecast com calibracao e chart_data., _brier_score(), _canonical_json(), ForecastEntry, ForecastLedger, _log_loss(), _mean() (+21 more)

### Community 36 - "EntityNode"
Cohesion: 0.04
Nodes (60): LLMEntityExtractor, Any, Extrator de entidades via LLM (fallback quando Graphiti esta indisponivel). Usa, Extrai entidades de texto usando LLM como alternativa ao Graphiti., Extrair entidades concretas do texto usando LLM.          Args:             text, AgentActivityConfig, DeliveryGovernanceConfig, EventConfig (+52 more)

### Community 37 - "test_vox_science_artifacts.py"
Cohesion: 0.11
Nodes (35): _build(), _build_with(), _gate(), test_baseline_servidores_inclui_pep_e_vozes(), test_claim_policy_define_c2_para_trace_robusto_sem_erro_externo(), test_compost_audit_exclui_outcome_do_prompt(), test_detecta_dominio_eleitoral(), test_detecta_dominio_servidores_federais() (+27 more)

### Community 38 - "run_reddit_simulation"
Cohesion: 0.16
Nodes (24): add_manual_action(), count_manual_actions(), create_model(), execute_social_bootstrap(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), get_seed_posts_from_db() (+16 more)

### Community 39 - "normalize_report_attribution"
Cohesion: 0.16
Nodes (21): classify_direct_quotes(), _find_origin(), label_operational_deadlines(), normalize_report_attribution(), _normalize_text(), _normalize_text_for_deadline(), Gate de atribuicao para textos de relatorio., Classifica citacoes literais conforme presenca no corpus de evidencia. (+13 more)

### Community 40 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (30): getEnvStatus(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, graphOfflineNoticeShown (+22 more)

### Community 41 - "artifacts.py"
Cohesion: 0.17
Nodes (31): _allowed_language(), _baseline_sources(), _blind_test_block(), build_vox_science_artifacts(), _canonical_sha256(), _claim_level(), _claim_policy_audit(), _clean_text() (+23 more)

### Community 42 - "LLMClient"
Cohesion: 0.10
Nodes (22): Resolve aliases internos de modelo para o nome real a ser chamado., Inicializa o cliente LLM apenas quando necessario., _extract_balanced_json(), LLMClient, parse_llm_json_response(), Any, Cliente de LLM com suporte a alias de modelos, timeout e retry., Normaliza JSON comum e SSE retornado por gateways OpenAI-compatible.          O (+14 more)

### Community 43 - "simulation_runner.py"
Cohesion: 0.12
Nodes (23): CommandStatus, CommandType, Enum, str, Modulo de comunicacao IPC para simulacao Usado para comunicacao entre processos, Inicializar cliente IPC          Args:             simulation_dir: Diretorio de, Verificar se o ambiente de simulacao esta ativo          Verifica atraves do arq, Cliente IPC de simulacao (usado pelo lado Flask)      Usado para enviar comandos (+15 more)

### Community 44 - "cli.py"
Cohesion: 0.09
Nodes (23): main(), CLI para AutoResearch INTEIA.  Uso:     python -m backend.autoresearch.cli --tar, Configura alvo Frontend Performance., Mede score baseline sem modificar nada., Configura alvo Hookify Rules., Configura alvo Skill Prompt., Configura alvo Genetic Copy., run_baseline() (+15 more)

### Community 45 - "frontend/package.json"
Cohesion: 0.07
Nodes (28): axios, d3, dependencies, axios, d3, mermaid, vue, vue-router (+20 more)

### Community 46 - "TokenTracker"
Cohesion: 0.10
Nodes (23): get_token_usage(), Retorna consumo de tokens e custo acumulado (global e por sessao)., Singleton thread-safe para rastrear tokens globalmente e por sessao., TokenTracker, Testes do TokenTracker e TokenUsage (Phase 10)., Reset singleton state entre testes — TokenTracker e singleton global., reset_singleton(), test_token_usage_aplica_preco_reduzido_ao_cache() (+15 more)

### Community 47 - "._build_graph_worker"
Cohesion: 0.18
Nodes (7): Any, Thread de trabalho para construcao do grafo., Criar grupo no Graphiti (grupos sao criados implicitamente na primeira mensagem), Cria um grafo local de esquema quando Graphiti nao esta acessivel.          O fa, Envia o contexto da ontologia como mensagem de sistema.          O Graphiti nao, Espera o Graphiti processar o input e valida se o grafo ganhou conteudo., Obter dados completos do grafo.          No Graphiti, isso e feito via POST /sea

### Community 48 - "RalphMethodEvaluator"
Cohesion: 0.11
Nodes (14): Configura alvo de score do metodo RalphLoop + AutoResearch., setup_ralph_target(), Any, Path, RalphMethodAsset, RalphMethodConstraints, RalphMethodEvaluator, Invariantes do metodo Ralph aplicado ao Mirofish. (+6 more)

### Community 49 - "report_content_repair.py"
Cohesion: 0.17
Nodes (25): _artifact(), _known_agents(), _known_platforms(), _known_rounds(), _metrics_for_report(), _metrics_sentence(), _normalize_quote(), _now_iso() (+17 more)

### Community 50 - "GoldenCaseLoader"
Cohesion: 0.17
Nodes (11): GoldenCaseLoader, Any, Path, Carregador defensivo para pacote de caso de ouro., Le um pacote de caso de ouro a partir de um caminho injetado., Retorna resumo do pacote em campos estaveis para auditoria local., Monta fixture curta para testes de qualidade e regressao., Carrega manifesto, JSON e listas de arquivos existentes. (+3 more)

### Community 51 - "Any"
Cohesion: 0.09
Nodes (12): Any, Inicializa o Report Agent          Args:             graph_id: ID do grafo, Define as ferramentas disponiveis, Executa uma chamada de ferramenta          Args:             tool_name: Nome da, Gera analise estrategica final usando Helena Strategos com o melhor modelo dispo, Obtem o caminho do arquivo de log do Agent, Obtem o conteudo do log do Agent          Args:             report_id: ID do rel, Obtem o log completo do Agent (obtencao unica de tudo)          Args: (+4 more)

### Community 52 - "test_retry.py"
Cohesion: 0.13
Nodes (23): Any, Exception, Mecanismo de retentativa para chamadas de API Usado para tratar logica de retent, Encapsulamento de cliente de API com retentativa, Executar chamada de funcao com retentativa em caso de falha          Args:, Chamada em lote com retentativa individual para cada item que falhar          Ar, Decorador de retentativa com backoff exponencial      Args:         max_retries:, Versao assincrona do decorador de retentativa (+15 more)

### Community 53 - "HookifyEvaluator"
Cohesion: 0.10
Nodes (16): HookifyAsset, HookifyEvaluator, match_rules(), parse_hookify_rule(), Path, Verifica se o asset modificado ainda e valido., Asset: conjunto de arquivos hookify.*.local.md., Le todos os arquivos hookify concatenados. (+8 more)

### Community 54 - "report.js"
Cohesion: 0.12
Nodes (23): createExecutivePackage(), createReportExport(), getApiBasePath(), getConsoleLog(), getExecutivePackageAttachmentUrl(), getMissionBundle(), getReportArtifacts(), getReportDeliveryPackage() (+15 more)

### Community 55 - "SimulationView.vue"
Cohesion: 0.10
Nodes (24): closeSimulationEnv(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData, graphLoading (+16 more)

### Community 56 - "test_vox_metrics.py"
Cohesion: 0.13
Nodes (25): demographic_parity_difference(), intra_group_variance(), kl_divergence(), mean_absolute_error(), _normalize(), _quantile(), Statistical distance and fairness metrics for Vox Science fidelity reports.  Pur, Stability score in [0, 1] where 1 = identical distributions.      Uses ``1 - nor (+17 more)

### Community 57 - "TokenUsage"
Cohesion: 0.09
Nodes (7): Rastreamento de consumo de tokens, custo tecnico e valor INTEIA., _round_brl(), _round_usd(), TokenPhase, TokenUsage, test_token_usage_custo_usd_calculado(), test_token_usage_valor_inteia_aplica_multiplicador_5x()

### Community 58 - "InteractionView.vue"
Cohesion: 0.09
Nodes (22): app, router, routes, addLog(), currentReportId, currentStatus, graphData, graphLoading (+14 more)

### Community 59 - "report_exporter.py"
Cohesion: 0.14
Nodes (36): allowed_export_file_path(), create_report_export(), _evidence_annex_markdown(), _exports_root(), list_report_exports(), load_export_manifest(), _now_iso(), _public_export_manifest() (+28 more)

### Community 60 - "StrategicDensityGate"
Cohesion: 0.15
Nodes (13): Any, Gate deterministico de densidade estrategica para relatorios caros., Avalia se um relatorio entrega decisao superior ao obvio., Signal, StrategicDensityGate, test_actionable_adversarial_report_passes_density_gate(), test_actionable_report_with_alternative_vocabulary_passes_density_gate(), test_density_gate_returns_clear_portuguese_issue_labels() (+5 more)

### Community 61 - "PlatformActionLogger"
Cohesion: 0.09
Nodes (9): ActionLogger, get_logger(), PlatformActionLogger, Any, 动作日志记录器 用于记录OASIS模拟中每个Agent的动作，供后端监控使用  日志结构:     sim_xxx/     ├── twitter/, 动作日志记录器（兼容旧接口）     建议使用 SimulationLogManager 代替, 初始化日志记录器                  Args:             platform: 平台名称 (twitter/reddit), MaxTokensWarningFilter (+1 more)

### Community 62 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (12): getSimulationHistory(), containerStyle, historyContainer, historyError, hoveringCard, isExpanded, loadHistory(), loading (+4 more)

### Community 63 - "PowerPersonaCatalog"
Cohesion: 0.07
Nodes (33): MissionSelection, Any, Grava e recupera escolhas comerciais e sinteticas por simulacao., PowerPersonaCatalog, Any, Path, Catalogo seguro de poderes e personas externas para INTEIA., Indexa arquivos pequenos de fontes externas sem acoplar seus sistemas. (+25 more)

### Community 64 - "ParallelIPCHandler"
Cohesion: 0.15
Nodes (11): main(), ParallelIPCHandler, Processador de comandos IPC para duas plataformas      Gerencia os ambientes de, Atualizar status do ambiente, Buscar comandos pendentes por polling, Obter o ambiente e agent_graph da plataforma especificada          Args:, Executar Interview em uma unica plataforma          Returns:             Diciona, Processar comando de entrevista de um unico Agente          Args:             co (+3 more)

### Community 65 - ".check_env_alive"
Cohesion: 0.11
Nodes (17): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt(), Entrevistar um Agent      Nota: requer ambiente em modo de espera de comandos, Entrevistar multiplos Agents em lote      Nota: requer ambiente em execucao, Entrevista global - mesma pergunta para todos      Nota: requer ambiente em exec (+9 more)

### Community 66 - "ReportView.vue"
Cohesion: 0.10
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 67 - "ApifyEnricher"
Cohesion: 0.20
Nodes (9): ApifyClient, ApifyEnricher, _cache_key(), _cache_path(), Any, Path, Enriquece multiplos municipios de forma otimizada.          Cada municipio e um, Estima custo para N municipios no perfil atual. (+1 more)

### Community 68 - "repair_report_finalization"
Cohesion: 0.19
Nodes (18): _now_iso(), _preview(), Any, Exception, Reparo deterministico da finalizacao de relatorios., Erro base de finalizacao., Relatorio nao encontrado., Relatorio ainda esta sendo gerado ou nao pode ser reparado agora. (+10 more)

### Community 69 - "ReportDeliveryEvaluator"
Cohesion: 0.12
Nodes (10): Configura alvo de score da fronteira de entrega de relatorios., setup_report_delivery_target(), Any, Path, Invariantes para evoluir a fronteira de entrega de relatorios., Asset read-only que resume os pontos de decisao de entrega., Score deterministico da fronteira de entrega cliente., ReportDeliveryAsset (+2 more)

### Community 70 - "simulation.js"
Cohesion: 0.14
Nodes (21): buildGraph(), generateOntology(), getGraphData(), getGraphStatus(), getProject(), getTaskStatus(), runInternalPreset(), API_TIMEOUTS (+13 more)

### Community 71 - "Any"
Cohesion: 0.13
Nodes (8): Any, Obtem historico de acoes (com paginacao)                  Args:             simu, Obtem linha do tempo da simulacao (resumo por rodada)                  Args:, Obtem estatisticas de cada Agent                  Returns:             Lista de, Informacoes detalhadas incluindo acoes recentes, Obtem historico de Interview de um banco de dados, Obtem historico de Interview (do banco de dados)                  Args:, Extrai resumo auditavel de um actions.jsonl sem materializar todas as acoes.

### Community 72 - "test_pagination.py"
Cohesion: 0.18
Nodes (18): get_simulation_actions(), Obter historico de acoes dos Agents      Parametros de Query:         limit: qua, get_from_line(), get_limit(), get_offset(), Validação de parâmetros de paginação.  2026-04-18, Phase 7: evita OOM e DoS por, Retorna ?limit= validado no range [1, max_limit]., Retorna ?offset= validado no range [0, max_offset]. (+10 more)

### Community 73 - "test_helena_control_api.py"
Cohesion: 0.14
Nodes (19): _check(), _client_id(), Rate limit caseiro por IP, em memoria, sem dependencias externas.  Pensado para, Identifica o cliente. Honra X-Forwarded-For quando atras de proxy., Retorna (permitido, segundos_para_proxima_tentativa)., auth_headers(), test_acoes_destrutivas_e_travessia_de_path_sao_bloqueadas(), test_cancelamento_so_antes_da_execucao() (+11 more)

### Community 74 - "llm_proxy_v2.py"
Cohesion: 0.15
Nodes (19): chat(), ensure_required_defaults(), extract_schema(), get_required_fields(), _is_cooling(), _log(), _pick_model(), _provider_has_credentials() (+11 more)

### Community 75 - "PowerCatalog"
Cohesion: 0.14
Nodes (15): get_power_catalog(), Expor poderes formais da missao., PowerCatalog, Any, Catalogo formal de poderes comerciais do Mirofish INTEIA., Expoe poderes estaveis e estimativa comercial de selecao., Testes do catalogo formal de poderes comerciais., test_bundle_supremo_soma_custo_fixo_sem_mudar_tokens() (+7 more)

### Community 76 - "test_translation.py"
Cohesion: 0.15
Nodes (18): Traduz nomes SCREAMING_SNAKE_CASE de ingles para pt-BR., _translate_relation_name(), Testes unitarios para mapa de traducao de relacoes (Phase 6)., Garante que o lado pt-BR tambem segue SCREAMING_SNAKE_CASE (ontologia upstream)., Chaves devem ser uppercase para match com SCREAMING_SNAKE_CASE do Graphiti., Multiplas relacoes podem mapear pro mesmo pt-BR (ex: DEFENDS/ADVOCATES → DEFENDE, Mapa deve cobrir pelo menos 20 relacoes comuns., test_all_keys_are_uppercase() (+10 more)

### Community 77 - "FileParser"
Cohesion: 0.14
Nodes (13): Servico de processamento de texto, FileParser, Ferramenta de analise de arquivos Suporta extracao de texto de arquivos PDF, Mar, Extrair texto de Markdown, com deteccao automatica de codificacao, Ler arquivo de texto, com deteccao automatica de codificacao em caso de falha UT, Extrair texto de TXT, com deteccao automatica de codificacao, Extrair texto de multiplos arquivos e combinar          Args:             file_p, Dividir texto em blocos menores      Args:         text: Texto original (+5 more)

### Community 78 - "GitOps"
Cohesion: 0.15
Nodes (11): GitOps, Path, Operacoes git para versionamento de experimentos AutoResearch., Inicializa repo git se nao existir., Salva estado atual do asset. Retorna hash do commit., Commita melhoria. Retorna hash do novo commit., Reverte asset para ultimo commit., Retorna historico de commits recentes. (+3 more)

### Community 79 - "scripts"
Cohesion: 0.10
Nodes (20): concurrently, description, devDependencies, concurrently, engines, node, license, name (+12 more)

### Community 80 - "doStartSimulation"
Cohesion: 0.22
Nodes (15): getRunStatusDetail(), getSimulationReadiness(), addLog(), checkPlatformsCompleted(), doStartSimulation(), emit, fetchRunStatus(), fetchRunStatusDetail() (+7 more)

### Community 81 - "test_report_exports_api.py"
Cohesion: 0.12
Nodes (19): create_report_export_route(), download_report_export_file_route(), list_report_exports_route(), Criar rascunho de export verificavel para um relatorio., Listar exports existentes sem expor caminhos internos., Verificar integridade e seguranca do bundle exportado., Baixar apenas arquivos allowlisted no manifest do export., verify_report_export_bundle_route() (+11 more)

### Community 82 - "SkillPromptEvaluator"
Cohesion: 0.13
Nodes (8): Path, Avaliador LLM-as-judge para qualidade de respostas de skills., Usa LLM avaliador para pontuar resposta em cada dimensao., Calcula score composto medio sobre todos os casos de teste., Asset: arquivo SKILL.md de uma skill., Extrai secoes editaveis por headings markdown., SkillPromptAsset, SkillPromptEvaluator

### Community 83 - "Home.vue"
Cohesion: 0.12
Nodes (14): setPendingUpload(), addFiles(), canSubmit, error, fileInput, files, formData, handleDrop() (+6 more)

### Community 84 - "mission_bundle.py"
Cohesion: 0.25
Nodes (14): _canonical_json(), _freeze_forecasts(), gerar_mission_bundle(), Any, Bundle final da missao com manifesto e hashes deterministicos., Calcula hash de texto ou JSON usando representacao canonica., Atalho funcional para gerar o manifesto final., sha256_item() (+6 more)

### Community 85 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (13): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+5 more)

### Community 86 - "audit_report_evidence"
Cohesion: 0.15
Nodes (13): audit_report_evidence(), number_supported_by_evidence(), Retorna True quando o numero literal aparece no corpus local., Audita se o relatorio usa citacoes sustentadas pelo sistema.      Returns:, test_audit_report_evidence_aceita_metricas_estruturadas_do_sistema(), test_audit_report_evidence_aceita_prazo_rotulado_como_sugestao_operacional(), test_audit_report_evidence_aceita_probabilidade_do_decision_packet(), test_audit_report_evidence_aprova_citacoes_presentes() (+5 more)

### Community 87 - "build_report_evolution_readiness"
Cohesion: 0.36
Nodes (11): _artifact(), _blockers(), build_report_evolution_readiness(), _content_consistency(), _count_evolution_runs(), _gaps(), _latest_run_status(), Any (+3 more)

### Community 88 - "GeneticCopyAsset"
Cohesion: 0.14
Nodes (8): GeneticCopyAsset, GeneticCopyEvaluator, Path, Avaliador que roda o GA e mede fitness do campeao., Roda o GA e retorna score composto: fitness + cobertura., Verifica se o template_ag.py e valido., Asset: template_ag.py do algoritmo genetico., Extrai CONFIG, PESOS e trechos de fitness_persona.

### Community 89 - "helenaExecutor.js"
Cohesion: 0.32
Nodes (16): executeBuildGraph(), executeContinueAnalysis(), executeCreateSimulation(), executeGenerateReport(), executeHelenaAction(), executeHelenaPlan(), executePrepareSimulation(), executeStartSimulation() (+8 more)

### Community 90 - "build_decision_packet"
Cohesion: 0.29
Nodes (15): _build_convergence_assessment(), build_decision_packet(), _build_red_team_assessment(), _cap(), _clamp(), decision_packet_prompt_block(), _float_metric(), _positive_int() (+7 more)

### Community 91 - "create_project_from_briefing"
Cohesion: 0.20
Nodes (10): _build_project_text(), create_project_from_briefing(), create_project_from_structured_briefing(), _normalize_structured_context(), Cria projeto interno a partir de briefing textual e gera ontologia., Normaliza materiais textuais enviados pela INTEIA., Alias explicito para o fluxo estruturado da INTEIA., Extrai contexto estruturado relevante para cenarios INTEIA. (+2 more)

### Community 92 - "report_agent.py"
Cohesion: 0.12
Nodes (22): Enum, Servico do Report Agent Geracao de relatorios de simulacao no padrao ReACT usand, Limita concorrencia de secoes ao que o provedor LLM suporta., report_section_workers(), build_paperbanana_report_diagrams(), _compact_label(), count_report_diagrams(), ensure_minimum_report_diagrams() (+14 more)

### Community 93 - "ExperimentLog"
Cohesion: 0.15
Nodes (10): ExperimentLog, Any, Path, Log JSONL append-only para experimentos AutoResearch., Log crash-resilient de experimentos. Cada linha e um JSON independente., Appenda um resultado de experimento ao log., Le todos os experimentos do log., Retorna os N ultimos experimentos. (+2 more)

### Community 94 - "jaccard_similarity"
Cohesion: 0.22
Nodes (9): jaccard_similarity(), _ngrams(), Jaccard sobre n-gramas de palavras. 0.0 = disjunto, 1.0 = identicos.      n=5 ca, NFKD garante que palavras com/sem acento batem., Texto curto demais para n-grama pedido retorna 0., test_jaccard_disjoint_returns_zero(), test_jaccard_identical_returns_one(), test_jaccard_normaliza_acentos() (+1 more)

### Community 95 - "extract_numeric_claims"
Cohesion: 0.29
Nodes (7): extract_numeric_claims(), Extrai numeros em linhas de conteudo para auditoria conservadora., Remove blocos QC/auditoria acrescentados pelo proprio sistema., _strip_generated_audit_blocks(), test_extract_numeric_claims_ignora_blocos_de_qc_gerados(), test_extract_numeric_claims_ignora_titulos_markdown(), test_extract_numeric_claims_marca_probabilidade_de_tabela_como_metricavel()

### Community 96 - "quote_supported_by_evidence"
Cohesion: 0.29
Nodes (7): _normalize(), _normalize_text_for_match(), quote_supported_by_evidence(), Retorna True somente se a citacao aparece no corpus de evidencia.      O teste e, Tokeniza, normaliza unicode (NFKD), lowercase, remove pontuacao., Normaliza texto para comparacao conservadora de citacoes., test_quote_supported_by_evidence_exige_corpus()

### Community 97 - "FrontendPerfAsset"
Cohesion: 0.16
Nodes (6): FrontendPerfAsset, FrontendPerfConstraints, Path, Invariantes para otimizacao de performance frontend., Verifica se o build completa sem erros., Asset: vite.config.js e arquivos de config do frontend.

### Community 98 - "report_bundle_verifier.py"
Cohesion: 0.17
Nodes (28): _check(), _now_iso(), _persist_result(), Any, Path, Verification for generated report export bundles., Verify path safety, expected files, hashes, and renderer metadata., _read_json() (+20 more)

### Community 99 - "authConfig"
Cohesion: 0.15
Nodes (16): authConfig(), cancelHelenaCommand(), completeHelenaCommand(), executeHelenaCommand(), getHelenaContext(), listHelenaCommands(), openHelenaSession(), planHelenaCommand() (+8 more)

### Community 100 - "OntologyGenerator"
Cohesion: 0.18
Nodes (9): OntologyGenerator, Any, Servico de geracao de ontologia Interface 1: Analisa conteudo textual e gera def, Gerador de ontologia     Analisa conteudo textual e gera definicoes de tipos de, Gera a definicao de ontologia          Args:             document_texts: Lista d, Constroi a mensagem do usuario, Valida e pos-processa o resultado, FakeLLMClient (+1 more)

### Community 101 - "Step1GraphBuild.vue"
Cohesion: 0.14
Nodes (10): creatingSimulation, graphAvailability, graphStats, handleEnterEnvSetup(), isDetailExpanded, logContent, logsExpanded, props (+2 more)

### Community 102 - "test_internal_harness_api.py"
Cohesion: 0.48
Nodes (6): _app(), Testes do contrato interno do harness MiroFish para consumidores service-to-serv, test_harness_evidence_bundle_404_sem_relatorio(), test_harness_evidence_bundle_exige_token(), test_harness_evidence_bundle_retorna_contrato_para_vox(), test_harness_runs_alias_dispara_pipeline_com_token()

### Community 103 - "SimulationLogManager"
Cohesion: 0.24
Nodes (5): 模拟日志管理器     统一管理所有日志文件，按平台分离, 初始化日志管理器                  Args:             simulation_dir: 模拟目录路径, SimulationLogManager, CommandType, Constantes de tipos de comando

### Community 104 - "TextProcessor"
Cohesion: 0.17
Nodes (7): GraphInfo, Obter informacoes do grafo via busca ampla., Extrair texto de multiplos arquivos, Dividir texto em blocos          Args:             text: Texto original, Pre-processar texto         - Remover espacos em branco excessivos         - Pad, Obter estatisticas do texto, TextProcessor

### Community 105 - "CostGuard"
Cohesion: 0.17
Nodes (5): CostGuard, Controle de custo para experimentos AutoResearch., Rastreia gastos e bloqueia quando budget atingido., Registra tokens consumidos e atualiza custo., Retorna True se ainda ha budget e tempo disponivel.

### Community 106 - "llm_client.py"
Cohesion: 0.21
Nodes (8): _ChatChoice, _ChatMessage, _ChatResponse, _ChatUsage, Cliente unificado de LLM.  Opera sobre provedores compativeis com a API OpenAI e, Retorna lista de providers de fallback configurados via env.          Formato: [, Executa chamada ao provider via requests (compativel com OmniRouter).          E, Tenta um provider especifico com max_retries retries.

### Community 107 - "loadQualityGate"
Cohesion: 0.38
Nodes (7): getSimulationQuality(), saveMissionSelection(), getGateIssuesFromError(), handleNextStep(), loadQualityGate(), persistMissionSelection(), summarizeIssue()

### Community 108 - "ReportStatus"
Cohesion: 0.06
Nodes (38): MissionBundle, Monta o manifesto final sem depender de arquivos fisicos., str, Aplica a Regra Zero tambem ao resumo que abre o relatorio., Registrador de log de console do Report Agent      Escreve logs no estilo consol, Inicializa o registrador de log de console          Args:             report_id:, Garante que o diretorio do arquivo de log existe, Configura o handler de arquivo para gravar logs simultaneamente em arquivo (+30 more)

### Community 109 - ".get_all_actions"
Cohesion: 0.33
Nodes (4): get_run_status_detail(), Obter estado detalhado (com todas as acoes)      Para exibicao em tempo real no, Le acoes de um unico arquivo de acoes                  Args:             file_pa, Obtem historico completo de acoes de todas as plataformas (sem paginacao)

### Community 110 - "extract_direct_quotes"
Cohesion: 0.33
Nodes (6): extract_direct_quotes(), Extrai citacoes diretas entre aspas duplas/curvas.      A Regra Zero INTEIA exig, Remove blocos de codigo para nao auditar exemplos como se fossem claims., _strip_code_fences(), test_extract_direct_quotes_ignora_blocos_de_codigo(), test_normalize_report_attribution_remove_aspas_aninhadas_sem_suporte()

### Community 111 - "test_phase03_smoke.py"
Cohesion: 0.25
Nodes (6): Vox Science helpers for public-data grounded synthetic harness artifacts., Smoke test ponta-a-ponta: build_vox_science_artifacts gera os 11 artefatos + tod, Construtos de violacao acionam blockers no science_gate., Builder produz todos 11 artefatos + 8 campos novos R1-R8., test_smoke_e2e_fase03_dpd_violation_e_blind_leak_bloqueiam_gate(), test_smoke_e2e_fase03_todos_artefatos_e_campos_novos()

### Community 112 - "run_preset"
Cohesion: 0.50
Nodes (4): create_harness_run(), Alias semantico para iniciar a pesquisa completa via harness MiroFish., Executa pipeline Mirofish completo em uma chamada.      Payload:         {, run_preset()

### Community 113 - "HarnessEvidenceBundleNotFound"
Cohesion: 0.67
Nodes (3): HarnessEvidenceBundleNotFound, ValueError, Levantado quando nao existe relatorio para a simulacao solicitada.

### Community 114 - "FrontendPerfEvaluator"
Cohesion: 0.29
Nodes (4): FrontendPerfEvaluator, Build e mede performance. Maior score = melhor., Avaliador de performance: build time + bundle size., Retorna tamanho total do bundle em bytes.

### Community 115 - "run_parallel_simulation.py"
Cohesion: 0.11
Nodes (19): disable_oasis_logging(), _enrich_action_context(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation(), load_config(), Script de simulacao OASIS em paralelo para duas plataformas Executa simultaneame (+11 more)

### Community 116 - "InteiaBackground.vue"
Cohesion: 0.25
Nodes (4): cleanupFns, cursorEl, cursorLabel, neuralCanvas

### Community 118 - "ProxyHandler"
Cohesion: 0.29
Nodes (3): ProxyHandler, Proxy local que traduz chamadas OpenAI SDK (httpx) para requests. Resolve incomp, BaseHTTPRequestHandler

### Community 119 - "mirofish_smoke_check.py"
Cohesion: 0.43
Nodes (6): backend_python(), fetch_json(), main(), Path, Smoke check operacional do MiroFish.  Executa validacoes locais e, se MIROFISH_L, run_step()

### Community 121 - "escapeHtml"
Cohesion: 0.47
Nodes (5): renderMarkdown(), renderMarkdown(), escapeHtml(), renderSafeMarkdown(), textToSafeHtml()

### Community 123 - ".path"
Cohesion: 0.40
Nodes (3): Path, Verifica se o asset modificado ainda respeita as restricoes., Caminho do asset principal.

### Community 124 - "GraphBuilderService"
Cohesion: 0.10
Nodes (16): delete_graph(), get_graph_data(), Obter dados do grafo (nos e arestas), Excluir grafo do Graphiti, GraphBuilderService, Construir grafo de forma assincrona.          Args:             text: Texto de e, Cria um ID local para fallback sem Graphiti., Adicionar texto ao grafo em lotes via POST /messages.          IMPORTANTE: Todos (+8 more)

### Community 126 - "vercel.json"
Cohesion: 0.40
Nodes (4): buildCommand, installCommand, outputDirectory, rewrites

### Community 128 - "createExportDraft"
Cohesion: 0.60
Nodes (5): createExportDraft(), formatExportError(), getExportId(), loadReportExports(), verifyExportBundle()

### Community 130 - "closeModal"
Cohesion: 0.50
Nodes (4): closeModal(), goToProject(), goToReport(), goToSimulation()

## Knowledge Gaps
- **457 isolated node(s):** `Signal`, `mirofish-backend`, `name`, `private`, `version` (+452 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `report_system_gate.py`, `OntologyGenerator`, `EntityNode`, `test_internal_harness_api.py`, `ZepToolsService`, `test_helena_control_api.py`, `helena.py`, `LLMClient`, `simulation_runner.py`, `SimulationDataReader`, `llm_client.py`, `cli.py`, `graph.py`, `report.py`, `simulation.py`, `report_agent.py`, `internal.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `SimulationManager` connect `SimulationManager` to `report_system_gate.py`, `test_report_quality.py`, `EntityNode`, `ReportManager`, `SimulationRunner`, `Config`, `test_helena_control_api.py`, `helena.py`, `OasisProfileGenerator`, `ReportStatus`, `simulation_runner.py`, `report.py`, `Any`, `simulation.py`, `ReportLogger`, `report_agent.py`, `TaskManager`, `internal.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `ReportManager` connect `ReportManager` to `build_executive_package`, `test_report_quality.py`, `SimulationRunner`, `ZepToolsService`, `Config`, `helena.py`, `evaluate_report_method_checklist`, `SimulationManager`, `report.py`, `SimulationDataReader`, `internal.py`, `report_system_gate.py`, `harness_evidence_bundle.py`, `ForecastLedger`, `simulation_runner.py`, `report_content_repair.py`, `Any`, `report_exporter.py`, `StrategicDensityGate`, `repair_report_finalization`, `test_helena_control_api.py`, `test_report_exports_api.py`, `build_report_evolution_readiness`, `report_agent.py`, `report_bundle_verifier.py`, `test_internal_harness_api.py`, `ReportStatus`, `HarnessEvidenceBundleNotFound`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `ReportManager` (e.g. with `ExecutivePackageConflict` and `ExecutivePackageError`) actually correct?**
  _`ReportManager` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `ReportAgent` (e.g. with `ForecastLedger` and `MissionBundle`) actually correct?**
  _`ReportAgent` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `SimulationManager` (e.g. with `HelenaCommandStore` and `HelenaConflictError`) actually correct?**
  _`SimulationManager` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `SimulationRunner` (e.g. with `Report` and `ReportAgent`) actually correct?**
  _`SimulationRunner` has 31 INFERRED edges - model-reasoned connections that need verification._