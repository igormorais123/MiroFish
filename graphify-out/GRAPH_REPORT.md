# Graph Report - .  (2026-07-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3955 nodes · 8443 edges · 159 communities (137 shown, 22 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 534 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `07306e71`
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

## God Nodes (most connected - your core abstractions)
1. `ReportManager` - 120 edges
2. `ReportAgent` - 94 edges
3. `error()` - 84 edges
4. `SimulationManager` - 77 edges
5. `SimulationRunner` - 76 edges
6. `Report` - 75 edges
7. `PowerPersonaCatalog` - 58 edges
8. `TokenTracker` - 54 edges
9. `ReportStatus` - 53 edges
10. `Config` - 49 edges

## Surprising Connections (you probably didn't know these)
- `LunaOpenAIClient` --uses--> `LLMClient`  [INFERRED]
  deploy/graphiti_patches/zep_graphiti.py → backend/app/utils/llm_client.py
- `ZepGraphiti` --uses--> `LLMClient`  [INFERRED]
  deploy/graphiti_patches/zep_graphiti.py → backend/app/utils/llm_client.py
- `health()` --indirect_call--> `_metrics()`  [INFERRED]
  codex_proxy.py → backend/app/services/vox_science/artifacts.py
- `metrics()` --indirect_call--> `_metrics()`  [INFERRED]
  codex_proxy.py → backend/app/services/vox_science/artifacts.py
- `report_store()` --indirect_call--> `ReportManager`  [INFERRED]
  backend/tests/test_executive_package.py → backend/app/services/report_agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Mirofish Infrastructure Stack** — docker_compose_neo4j, docker_compose_graphiti, docker_compose_mirofish [EXTRACTED 1.00]
- **LLM and Graph Integration** — docker_compose_graphiti, graphiti_concept, camel_ai [INFERRED 0.85]

## Communities (159 total, 22 thin omitted)

### Community 0 - "Step4Report.vue"
Cohesion: 0.01
Nodes (130): activeExport, activeExportId, activeExportVerification, activeSectionIndex, activeStep, agentLogLine, agentLogs, auditIssues (+122 more)

### Community 1 - "report_agent.py"
Cohesion: 0.04
Nodes (61): MissionBundle, Monta o manifesto final sem depender de arquivos fisicos., Enum, str, Servico do Report Agent Geracao de relatorios de simulacao no padrao ReACT usand, Registrador de log de console do Report Agent      Escreve logs no estilo consol, Inicializa o registrador de log de console          Args:             report_id:, Configura o handler de arquivo para gravar logs simultaneamente em arquivo (+53 more)

### Community 2 - "Step3Simulation.vue"
Cohesion: 0.03
Nodes (88): getPowerCatalog(), getPowerPersonaCatalog(), getMissionSelection(), getRunStatusDetail(), getSimulationQuality(), getSimulationReadiness(), saveMissionSelection(), actionIds (+80 more)

### Community 3 - "ReportManager"
Cohesion: 0.04
Nodes (53): download_report(), get_report_artifact(), get_report_sections(), list_report_artifacts(), Baixar relatorio (formato Markdown)      Retorna arquivo Markdown, Obter lista de secoes ja geradas (saida por secoes)      O frontend pode consult, Listar artefatos de gate, manifesto e auditoria do relatorio., Obter um artefato JSON especifico do relatorio. (+45 more)

### Community 4 - "build_executive_package"
Cohesion: 0.05
Nodes (75): allowed_executive_package_file_path(), build_executive_package(), _evidence_annex_markdown(), ExecutivePackageConflict, ExecutivePackageError, ExecutivePackageInvalidPath, ExecutivePackageNotFound, load_executive_package_manifest() (+67 more)

### Community 5 - "test_report_quality.py"
Cohesion: 0.05
Nodes (63): Exception, Report Agent - Agent de geracao de relatorios de simulacao      Utiliza o padrao, Aplica a Regra Zero tambem ao resumo que abre o relatorio., Converte para formato Markdown, ReportAgent, ReportOutline, ReportSection, audit_report_evidence() (+55 more)

### Community 6 - "Step5Interaction.vue"
Cohesion: 0.04
Nodes (70): getAgentLog(), getReport(), getReportEvolutionReadiness(), getReportSections(), repairReportContent(), getSimulationProfilesRealtime(), interviewAgents(), activeReportTool (+62 more)

### Community 7 - "test_vox_science_artifacts.py"
Cohesion: 0.06
Nodes (72): _allowed_language(), _baseline_sources(), _blind_test_block(), build_vox_science_artifacts(), _canonical_sha256(), _claim_level(), _claim_policy_audit(), _clean_text() (+64 more)

### Community 8 - "report.py"
Cohesion: 0.04
Nodes (70): _build_power_persona_catalog(), build_power_persona_context(), _build_power_persona_context_from_payload(), _build_power_selection_from_payload(), chat_with_report_agent(), check_report_status(), create_executive_package_route(), delete_report() (+62 more)

### Community 9 - "report_exporter.py"
Cohesion: 0.08
Nodes (65): _check(), _now_iso(), _persist_result(), Any, Exception, Path, Verification for generated report export bundles., Base verification error. (+57 more)

### Community 10 - "datetime"
Cohesion: 0.10
Nodes (46): cancel_helena_command(), complete_helena_command(), _disabled_response(), _error_response(), execute_helena_command(), get_helena_command(), get_helena_context(), get_helena_status() (+38 more)

### Community 11 - "OasisProfileGenerator"
Cohesion: 0.06
Nodes (31): OasisAgentProfile, OasisProfileGenerator, Any, callable, Salva Profile em arquivo (escolhe formato correto por plataforma)          Requi, Salva Twitter Profile em formato CSV (conforme OASIS oficial)          Campos CS, Padroniza campo gender para formato ingles exigido pelo OASIS          OASIS exi, Salva Reddit Profile em formato JSON          Usa formato consistente com to_red (+23 more)

### Community 12 - "PowerPersonaCatalog"
Cohesion: 0.09
Nodes (26): PowerPersonaCatalog, Any, Path, Catalogo seguro de poderes e personas externas para INTEIA., Indexa arquivos pequenos de fontes externas sem acoplar seus sistemas., Testes do catalogo de poderes e personas externas., test_api_helpers_filtram_catalogo_e_montam_contexto(), test_arquivo_malformado_nao_derruba_catalogo() (+18 more)

### Community 13 - "codex_proxy.py"
Cohesion: 0.06
Nodes (47): main(), Neo4jGraphIdFixer, Any, Gera relatório das correções., Ferramenta para corrigir group_ids em Neo4j., Inicializa conexão com Neo4j., Fecha conexão com Neo4j., Retorna mapeamento de group_id -> contagem de nós. (+39 more)

### Community 14 - "graph.py"
Cohesion: 0.06
Nodes (44): Rotas de API relacionadas ao grafo de conhecimento Utiliza mecanismo de contexto, _default_llm_api_key(), _default_llm_base_url(), _default_llm_model_name(), _env_flag(), _first_non_empty(), _parse_alias_map(), Gerenciamento central de configuracao.  Carrega variaveis de ambiente a partir d (+36 more)

### Community 15 - "internal.py"
Cohesion: 0.05
Nodes (56): get_project(), Redefinir estado do projeto (para reconstruir o grafo), Obter detalhes do projeto, reset_project(), build_internal_graph(), _build_lenia_export(), _build_project_text(), _compute_lenia_signals() (+48 more)

### Community 16 - "ProjectManager"
Cohesion: 0.06
Nodes (37): allowed_file(), delete_project(), generate_ontology(), list_projects(), Interface 1: Upload de arquivos, analise e geracao da definicao de ontologia, Verifica se a extensao do arquivo e permitida, Listar todos os projetos, create_internal_project() (+29 more)

### Community 17 - "social_bootstrap.py"
Cohesion: 0.08
Nodes (37): Exporta uma sintese em portugues com contagens por status., _distinct_n(), _normalize_words(), _normalized_entropy(), Any, Retorna apenas acoes de agentes (com agent_name)., Gera um resumo textual dos dados da simulacao para contexto LLM., Busca simples por keyword nas acoes. (+29 more)

### Community 18 - "report_quality.py"
Cohesion: 0.06
Nodes (50): audit_report_content_consistency(), _claim_categories(), _claim_number_value(), _coerce_positive_int(), extract_numeric_claims(), _first_positive_metric(), _flatten_numeric_metrics(), jaccard_similarity() (+42 more)

### Community 19 - "SimulationManager"
Cohesion: 0.08
Nodes (32): LLMEntityExtractor, Any, Extrai entidades de texto usando LLM como alternativa ao Graphiti., Extrair entidades concretas do texto usando LLM.          Args:             text, Conjunto completo de parametros da simulacao., SimulationParameters, Any, callable (+24 more)

### Community 20 - "report_system_gate.py"
Cohesion: 0.08
Nodes (39): _enum_value(), evaluate_decision_readiness(), _next_action(), Any, Estado de prontidao de decisao para simulacoes., Consolida simulacao, gate e relatorio em um estado de produto., DeliveryGovernancePolicy, normalize_delivery_mode() (+31 more)

### Community 21 - "IPCHandler"
Cohesion: 0.06
Nodes (30): CommandType, IPCHandler, main(), MaxTokensWarningFilter, Any, Script de simulacao OASIS Twitter com configuracoes predefinidas Este script le, Constantes de tipos de comando, Processador de comandos IPC (+22 more)

### Community 22 - "MainView.vue"
Cohesion: 0.09
Nodes (44): generateOntology(), getGraphData(), getGraphStatus(), getProject(), getTaskStatus(), service, clearPendingUpload(), getPendingUpload() (+36 more)

### Community 23 - "IPCHandler"
Cohesion: 0.06
Nodes (29): CommandType, IPCHandler, main(), MaxTokensWarningFilter, Any, Script de simulacao OASIS Reddit com configuracoes predefinidas Este script le o, Constantes de tipos de comando, Processador de comandos IPC (+21 more)

### Community 24 - "EntityNode"
Cohesion: 0.07
Nodes (31): generate_profiles(), Gera Agent Profile do grafo (sem criar simulacao)      Requisicao (JSON):, Extrator de entidades via LLM (fallback quando Graphiti esta indisponivel). Usa, Gerador de Agent Profile OASIS Converte entidades do grafo Zep para o formato Ag, AgentActivityConfig, DeliveryGovernanceConfig, EventConfig, PlatformConfig (+23 more)

### Community 25 - "Asset"
Cohesion: 0.08
Nodes (28): ABC, AutoResearch Engine — Loop autonomo de experimentacao.  Ciclo: hipotese (LLM) →, Asset, Constraints, Evaluator, ExperimentResult, Classes base abstratas para alvos de AutoResearch., Resultado de um unico experimento. (+20 more)

### Community 26 - "SimulationIPCClient"
Cohesion: 0.08
Nodes (26): CommandStatus, CommandType, IPCCommand, IPCResponse, Any, Enum, str, Modulo de comunicacao IPC para simulacao Usado para comunicacao entre processos (+18 more)

### Community 27 - "ZepGraphiti"
Cohesion: 0.07
Nodes (30): AddEntityNodeRequest, AddMessagesRequest, add_entity_node(), add_messages(), AsyncWorker, clear(), delete_entity_edge(), delete_episode() (+22 more)

### Community 28 - "HelenaCommandCenter.vue"
Cohesion: 0.05
Nodes (36): getHelenaStatus(), approvalToken, authenticated, availabilityClass, availabilityLabel, busy, closePanel(), command (+28 more)

### Community 29 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (39): getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles, emit (+31 more)

### Community 30 - "simulation.py"
Cohesion: 0.07
Nodes (37): _assess_simulation_health(), _build_latest_report_index(), close_simulation_env(), get_mission_selection(), _get_oasis_simulation_dir(), _get_report_id_for_simulation(), get_run_status(), get_simulation() (+29 more)

### Community 31 - "SimulationRunState"
Cohesion: 0.09
Nodes (19): Iniciar execucao da simulacao      Requisicao (JSON):         {             "sim, start_simulation(), Estado de execucao da simulacao (tempo real), Termina processo e subprocessos (cross-platform)                  Args:, Limpa logs de execucao da simulacao (para forcar reinicio)                  Remo, Adiciona acao a lista de acoes recentes, Limpa todos os processos de simulacao em execucao                  Chamado ao fe, Obtem diretorio de execucao validando o ID recebido da API. (+11 more)

### Community 32 - "harness_evidence_bundle.py"
Cohesion: 0.14
Nodes (35): get_harness_evidence_bundle(), Entrega evidencias MiroFish em contrato estavel para Vox e outros sistemas., _absolute_api_url(), _artifact_gate_passes(), _artifact_tag(), _artifact_url(), _build_evidence(), _build_forecasts() (+27 more)

### Community 33 - "ForecastLedger"
Cohesion: 0.10
Nodes (28): _enrich_forecast_ledger_payload(), Completa artefatos antigos de forecast com calibracao e chart_data., _brier_score(), _canonical_json(), ForecastEntry, ForecastLedger, _log_loss(), _mean() (+20 more)

### Community 34 - "evaluate_report_method_checklist"
Cohesion: 0.13
Nodes (30): _artifact_names(), build_report_delivery_packet(), Any, Pacote de decisao de entrega para relatorios., Consolida estado de entrega sem promover rascunho a entrega cliente., _verified_bundle(), _artifact_passes(), _build_payload() (+22 more)

### Community 35 - "Any"
Cohesion: 0.10
Nodes (10): Any, Inicializa o Report Agent          Args:             graph_id: ID do grafo, Define as ferramentas disponiveis, Executa uma chamada de ferramenta          Args:             tool_name: Nome da, Gera analise estrategica final usando Helena Strategos com o melhor modelo dispo, Classificacao operacional para entrega ao cliente., Verdadeiro somente quando o relatorio passou por todo o contrato INTEIA., test_format_interview_result_text_includes_names_and_answers_from_payload_shapes() (+2 more)

### Community 36 - ".log"
Cohesion: 0.06
Nodes (16): Obtem o tempo decorrido desde o inicio (em segundos), Registra uma entrada de log          Args:             action: Tipo de acao, ex:, Remove o conteudo final bruto da resposta antes de registra-la no agent_log., Registra o inicio da geracao do relatorio, Registra o inicio do planejamento do sumario, Registra as informacoes de contexto obtidas durante o planejamento, Registra a conclusao do planejamento do sumario, Registra o inicio da geracao de uma secao (+8 more)

### Community 37 - "SimulationConfigGenerator"
Cohesion: 0.10
Nodes (18): Any, Converte para dicionario., Converte para string JSON., Gerador inteligente de configuracao de simulacao.      Analisa objetivo, documen, Gera a configuracao completa da simulacao em varias etapas., Monta o contexto para o LLM e o limita ao tamanho maximo., Gera um resumo das entidades agrupadas por tipo., Executa chamada ao LLM com retry e tentativa de reparo do JSON. (+10 more)

### Community 38 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (30): getEnvStatus(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, graphOfflineNoticeShown (+22 more)

### Community 39 - "TaskManager"
Cohesion: 0.08
Nodes (20): get_task(), list_tasks(), Consultar estado da tarefa, Listar todas as tarefas, get_prepare_status(), Consultar progresso da tarefa de preparacao      Suporta dois modos de consulta:, Any, Carrega tarefas salvas do disco ao inicializar (+12 more)

### Community 40 - "Flask"
Cohesion: 0.11
Nodes (27): Registro de blueprints da API., get_mission_bundle(), get_report_delivery_package(), get_report_evolution_readiness(), Gerar manifesto final da missao a partir dos artefatos do relatorio., Obter pacote consolidado de entregabilidade do relatorio., Obter estado read-only para evoluir a analise do relatorio., get_simulation_readiness() (+19 more)

### Community 41 - "cli.py"
Cohesion: 0.09
Nodes (23): main(), CLI para AutoResearch INTEIA.  Uso:     python -m backend.autoresearch.cli --tar, Configura alvo Frontend Performance., Mede score baseline sem modificar nada., Configura alvo Hookify Rules., Configura alvo Skill Prompt., Configura alvo Genetic Copy., run_baseline() (+15 more)

### Community 42 - "TextProcessor"
Cohesion: 0.09
Nodes (18): Servico de processamento de texto, Extrair texto de multiplos arquivos, Dividir texto em blocos          Args:             text: Texto original, Pre-processar texto         - Remover espacos em branco excessivos         - Pad, Obter estatisticas do texto, TextProcessor, FileParser, Ferramenta de analise de arquivos Suporta extracao de texto de arquivos PDF, Mar (+10 more)

### Community 43 - "frontend/package.json"
Cohesion: 0.07
Nodes (28): axios, d3, dependencies, axios, d3, mermaid, vue, vue-router (+20 more)

### Community 44 - "._generate_section_react"
Cohesion: 0.08
Nodes (16): is_substantive_section_response(), Analisa chamadas de ferramenta a partir da resposta do LLM          Formatos sup, Valida se o JSON analisado e uma chamada de ferramenta valida, Converte o modo vindo da UI para o nome interno da ferramenta., Monta parametros seguros para execucao direta das ferramentas no chat., Remove blocos internos de ferramenta antes de devolver ao usuario., Gera o texto de descricao das ferramentas, Planeja o sumario do relatorio          Usa o LLM para analisar a demanda de sim (+8 more)

### Community 45 - "RalphMethodEvaluator"
Cohesion: 0.11
Nodes (14): Configura alvo de score do metodo RalphLoop + AutoResearch., setup_ralph_target(), Any, Path, RalphMethodAsset, RalphMethodConstraints, RalphMethodEvaluator, Invariantes do metodo Ralph aplicado ao Mirofish. (+6 more)

### Community 46 - "TokenTracker"
Cohesion: 0.11
Nodes (22): get_token_usage(), Retorna consumo de tokens e custo acumulado (global e por sessao)., Singleton thread-safe para rastrear tokens globalmente e por sessao., TokenTracker, Testes do TokenTracker e TokenUsage (Phase 10)., Reset singleton state entre testes — TokenTracker e singleton global., reset_singleton(), test_token_usage_aplica_preco_reduzido_ao_cache() (+14 more)

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
Cohesion: 0.10
Nodes (24): closeSimulationEnv(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData, graphLoading (+16 more)

### Community 52 - "ApifyEnricher"
Cohesion: 0.17
Nodes (11): ApifyClient, ApifyEnricher, _cache_key(), _cache_path(), Any, Path, Enriquecimento de materiais-base via Apify.  Fontes: Google SERP, Instagram (per, Enriquece multiplos municipios de forma otimizada.          Cada municipio e um (+3 more)

### Community 53 - "test_vox_metrics.py"
Cohesion: 0.13
Nodes (25): demographic_parity_difference(), intra_group_variance(), kl_divergence(), mean_absolute_error(), _normalize(), _quantile(), Statistical distance and fairness metrics for Vox Science fidelity reports.  Pur, Stability score in [0, 1] where 1 = identical distributions.      Uses ``1 - nor (+17 more)

### Community 54 - "repair_report_finalization"
Cohesion: 0.15
Nodes (23): Reparar finalizacao do relatorio sem chamar LLM., repair_report_finalization_route(), _now_iso(), _preview(), Any, Exception, Reparo deterministico da finalizacao de relatorios., Erro base de finalizacao. (+15 more)

### Community 55 - ".check_env_alive"
Cohesion: 0.10
Nodes (17): interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt(), Entrevistar um Agent      Nota: requer ambiente em modo de espera de comandos, Entrevistar multiplos Agents em lote      Nota: requer ambiente em execucao, Entrevista global - mesma pergunta para todos      Nota: requer ambiente em exec, Otimiza pergunta do Interview, adiciona prefixo para evitar chamada de ferrament (+9 more)

### Community 56 - "normalize_report_attribution"
Cohesion: 0.14
Nodes (24): classify_direct_quotes(), _find_origin(), label_operational_deadlines(), normalize_report_attribution(), _normalize_text(), _normalize_text_for_deadline(), Gate de atribuicao para textos de relatorio., Classifica citacoes literais conforme presenca no corpus de evidencia. (+16 more)

### Community 57 - "report_content_repair.py"
Cohesion: 0.17
Nodes (25): _artifact(), _known_agents(), _known_platforms(), _known_rounds(), _metrics_for_report(), _metrics_sentence(), _normalize_quote(), _now_iso() (+17 more)

### Community 58 - "StrategicDensityGate"
Cohesion: 0.15
Nodes (13): Any, Gate deterministico de densidade estrategica para relatorios caros., Avalia se um relatorio entrega decisao superior ao obvio., Signal, StrategicDensityGate, test_actionable_adversarial_report_passes_density_gate(), test_actionable_report_with_alternative_vocabulary_passes_density_gate(), test_density_gate_returns_clear_portuguese_issue_labels() (+5 more)

### Community 59 - "PlatformActionLogger"
Cohesion: 0.10
Nodes (9): ActionLogger, get_logger(), PlatformActionLogger, Any, 动作日志记录器 用于记录OASIS模拟中每个Agent的动作，供后端监控使用  日志结构:     sim_xxx/     ├── twitter/, 动作日志记录器（兼容旧接口）     建议使用 SimulationLogManager 代替, 初始化日志记录器                  Args:             platform: 平台名称 (twitter/reddit), CommandType (+1 more)

### Community 60 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (12): getSimulationHistory(), containerStyle, historyContainer, historyError, hoveringCard, isExpanded, loadHistory(), loading (+4 more)

### Community 61 - "SimulationRunner"
Cohesion: 0.16
Nodes (17): Obtem lista de IDs de simulacoes em execucao, Executor de simulacao          Responsabilidades:     1. Executar simulacao OASI, Obter estado de execucao, Reconstroi um estado minimo quando run_state.json foi perdido., Carrega estado de execucao do arquivo, SimulationRunner, Path, Regressoes de reconciliacao do estado auditavel da simulacao. (+9 more)

### Community 62 - "ReportView.vue"
Cohesion: 0.10
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 63 - "GraphitiClient"
Cohesion: 0.09
Nodes (13): internal_health(), Healthcheck completo com dados de infra (exige token)., Inicializa o servico.          Args:             api_key: Mantido na assinatura, Inicializa o leitor.          Args:             api_key: Mantido na assinatura p, Inicializa o servico.          Args:             api_key: Mantido na assinatura, GraphitiClient, Verifica se o Graphiti Server esta acessivel., Retorna status detalhado do Graphiti sem levantar excecao. (+5 more)

### Community 64 - "PowerCatalog"
Cohesion: 0.13
Nodes (16): get_power_catalog(), Expor poderes formais da missao., Selecao persistente de poderes e personas de uma missao., PowerCatalog, Any, Catalogo formal de poderes comerciais do Mirofish INTEIA., Expoe poderes estaveis e estimativa comercial de selecao., Testes do catalogo formal de poderes comerciais. (+8 more)

### Community 65 - "create_app"
Cohesion: 0.10
Nodes (14): Valida configuracoes obrigatorias para o backend., create_app(), Resolve CORS sem wildcard implicito em ambientes publicos., Cria e configura a aplicacao Flask., _resolve_cors_origins(), Registrar funcao de limpeza                  Chamado ao iniciar Flask, garante l, main(), Ponto de entrada do backend MiroFish (+6 more)

### Community 66 - "ReportDeliveryEvaluator"
Cohesion: 0.12
Nodes (10): Configura alvo de score da fronteira de entrega de relatorios., setup_report_delivery_target(), Any, Path, Invariantes para evoluir a fronteira de entrega de relatorios., Asset read-only que resume os pontos de decisao de entrega., Score deterministico da fronteira de entrega cliente., ReportDeliveryAsset (+2 more)

### Community 67 - "run_reddit_simulation"
Cohesion: 0.17
Nodes (23): add_manual_action(), count_manual_actions(), create_model(), execute_social_bootstrap(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), get_seed_posts_from_db() (+15 more)

### Community 68 - "simulation.js"
Cohesion: 0.18
Nodes (13): buildGraph(), API_TIMEOUTS, requestWithRetry(), chatWithReport(), generateReport(), createSimulation(), getRunStatus(), getSimulation() (+5 more)

### Community 69 - "test_pagination.py"
Cohesion: 0.16
Nodes (19): get_simulation_actions(), Obter historico de acoes dos Agents      Parametros de Query:         limit: qua, get_from_line(), get_limit(), get_offset(), Validação de parâmetros de paginação.  2026-04-18, Phase 7: evita OOM e DoS por, Retorna ?limit= validado no range [1, max_limit]., Retorna ?offset= validado no range [0, max_offset]. (+11 more)

### Community 70 - "LLMClient"
Cohesion: 0.14
Nodes (17): Inicializa o cliente LLM apenas quando necessario., LLMClient, parse_llm_json_response(), Any, Cliente de LLM com suporte a alias de modelos, timeout e retry., Normaliza JSON comum e SSE retornado por gateways OpenAI-compatible.          O, Envia requisicao em modo JSON e retorna objeto desserializado., Parseia JSON de LLM tolerando markdown, texto antes/depois e fences. (+9 more)

### Community 71 - "TokenUsage"
Cohesion: 0.10
Nodes (5): TokenPhase, TokenUsage, test_token_usage_custo_usd_calculado(), test_token_usage_to_dict_estrutura(), test_token_usage_valor_inteia_aplica_multiplicador_5x()

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
Cohesion: 0.15
Nodes (17): build_graph(), Interface 2: Construir grafo a partir do project_id      Requisicao (JSON):, _check_simulation_prepared(), get_graph_entities(), prepare_simulation(), Verifica se a simulacao ja foi preparada      Condicoes de verificacao:     1. s, Preparar ambiente (tarefa assincrona, LLM gera parametros)      Operacao demorad, Obtem todas as entidades do grafo (filtradas)      Retorna apenas nos de tipos p (+9 more)

### Community 79 - "SkillPromptEvaluator"
Cohesion: 0.13
Nodes (8): Path, Avaliador LLM-as-judge para qualidade de respostas de skills., Usa LLM avaliador para pontuar resposta em cada dimensao., Calcula score composto medio sobre todos os casos de teste., Asset: arquivo SKILL.md de uma skill., Extrai secoes editaveis por headings markdown., SkillPromptAsset, SkillPromptEvaluator

### Community 80 - "Home.vue"
Cohesion: 0.12
Nodes (14): setPendingUpload(), addFiles(), canSubmit, error, fileInput, files, formData, handleDrop() (+6 more)

### Community 81 - "AgentAction"
Cohesion: 0.12
Nodes (13): get_agent_stats(), get_run_status_detail(), get_simulation_timeline(), Obter estado detalhado (com todas as acoes)      Para exibicao em tempo real no, Obter linha do tempo (resumo por rodada)      Para barra de progresso no fronten, Obter estatisticas de cada Agent      Para ranking de atividade no frontend, AgentAction, Le acoes de um unico arquivo de acoes                  Args:             file_pa (+5 more)

### Community 82 - "test_translation.py"
Cohesion: 0.15
Nodes (18): Traduz nomes SCREAMING_SNAKE_CASE de ingles para pt-BR., _translate_relation_name(), Testes unitarios para mapa de traducao de relacoes (Phase 6)., Garante que o lado pt-BR tambem segue SCREAMING_SNAKE_CASE (ontologia upstream)., Chaves devem ser uppercase para match com SCREAMING_SNAKE_CASE do Graphiti., Multiplas relacoes podem mapear pro mesmo pt-BR (ex: DEFENDS/ADVOCATES → DEFENDE, Mapa deve cobrir pelo menos 20 relacoes comuns., test_all_keys_are_uppercase() (+10 more)

### Community 83 - "AgentActivity"
Cohesion: 0.11
Nodes (3): AgentActivity, Registro de atividade de um agente., Converte a atividade em uma descricao textual adequada para o Graphiti.

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
Cohesion: 0.17
Nodes (9): Any, Envia mensagens ao Graphiti para extracao de entidades.          Args:, Atalho para enviar um unico bloco de texto como mensagem., Busca semantica de fatos no grafo.          Retorna dict com chave 'facts' conte, Obtem memoria a partir do historico de mensagens., Lista episodios de um grupo., Cria um no de entidade manualmente., Obtem uma aresta pelo UUID. (+1 more)

### Community 91 - "ExperimentLog"
Cohesion: 0.15
Nodes (10): ExperimentLog, Any, Path, Log JSONL append-only para experimentos AutoResearch., Log crash-resilient de experimentos. Cada linha e um JSON independente., Appenda um resultado de experimento ao log., Le todos os experimentos do log., Retorna os N ultimos experimentos. (+2 more)

### Community 92 - "test_helena_control_api.py"
Cohesion: 0.21
Nodes (14): auth_headers(), test_acoes_destrutivas_e_travessia_de_path_sao_bloqueadas(), test_cancelamento_so_antes_da_execucao(), test_comando_repetido_ativo_nao_cria_redundancia(), test_idempotency_key_reapresenta_o_mesmo_comando(), test_payload_e_comando_tem_limites(), test_planejador_remove_acoes_redundantes_do_modelo(), test_planejamento_de_leitura_nao_exige_aprovacao() (+6 more)

### Community 93 - "Config"
Cohesion: 0.24
Nodes (14): Config, Configuracao principal do backend Flask., _app(), Testes do contrato interno do harness MiroFish para consumidores service-to-serv, test_harness_evidence_bundle_404_sem_relatorio(), test_harness_evidence_bundle_exige_token(), test_harness_evidence_bundle_retorna_contrato_para_vox(), test_harness_runs_alias_dispara_pipeline_com_token() (+6 more)

### Community 94 - "OntologyGenerator"
Cohesion: 0.18
Nodes (9): OntologyGenerator, Any, Servico de geracao de ontologia Interface 1: Analisa conteudo textual e gera def, Gerador de ontologia     Analisa conteudo textual e gera definicoes de tipos de, Gera a definicao de ontologia          Args:             document_texts: Lista d, Constroi a mensagem do usuario, Valida e pos-processa o resultado, FakeLLMClient (+1 more)

### Community 95 - "simulation_runner.py"
Cohesion: 0.17
Nodes (13): Enum, str, Executor de simulacao OASIS Executa simulacao em segundo plano e registra acoes, RoundSummary, RunnerStatus, Gerencia atualizadores de memoria para multiplas simulacoes., ZepGraphMemoryManager, PathLike (+5 more)

### Community 96 - "test_report_exports_api.py"
Cohesion: 0.17
Nodes (14): create_report_export_route(), list_report_exports_route(), Criar rascunho de export verificavel para um relatorio., Listar exports existentes sem expor caminhos internos., Verificar integridade e seguranca do bundle exportado., verify_report_export_bundle_route(), Report or export bundle is missing., ReportBundleVerificationNotFound (+6 more)

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
Cohesion: 0.19
Nodes (8): get_env_status(), get_interview_history(), Obter historico de Interview      Le registros do banco de dados      Requisicao, Obter estado do ambiente de simulacao      Verifica se o ambiente esta ativo (po, Any, Obtem informacoes detalhadas do estado do ambiente          Args:             si, Informacoes detalhadas incluindo acoes recentes, Obtem historico de Interview de um banco de dados

### Community 101 - "Any"
Cohesion: 0.18
Nodes (6): Any, Construir grafo de forma assincrona.          Args:             text: Texto de e, Cria um ID local para fallback sem Graphiti., Cria um grafo local de esquema quando Graphiti nao esta acessivel.          O fa, Obter dados completos do grafo.          No Graphiti, isso e feito via POST /sea, Detecta se o texto esta em ingles e traduz para pt-BR usando LLM barato.

### Community 102 - "Step1GraphBuild.vue"
Cohesion: 0.14
Nodes (10): creatingSimulation, graphAvailability, graphStats, handleEnterEnvSetup(), isDetailExpanded, logContent, logsExpanded, props (+2 more)

### Community 103 - "GraphBuilderService"
Cohesion: 0.19
Nodes (11): delete_graph(), get_graph_data(), Obter dados do grafo (nos e arestas), Excluir grafo do Graphiti, GraphBuilderService, Excluir grupo (equivale a excluir grafo)., Servico de construcao de grafo.     Responsavel por chamar a API REST do Graphit, Quando o grafo nao materializa, retorna os dados vazios (degradacao graciosa). (+3 more)

### Community 104 - "SimulationLogManager"
Cohesion: 0.22
Nodes (5): 模拟日志管理器     统一管理所有日志文件，按平台分离, 初始化日志管理器                  Args:             simulation_dir: 模拟目录路径, SimulationLogManager, MaxTokensWarningFilter, Filtra avisos do camel-ai sobre max_tokens (nao definimos max_tokens intencional

### Community 105 - "router/index.js"
Cohesion: 0.17
Nodes (7): cleanupFns, cursorEl, cursorLabel, neuralCanvas, app, router, routes

### Community 106 - "._build_graph_worker"
Cohesion: 0.18
Nodes (6): GraphInfo, Thread de trabalho para construcao do grafo., Criar grupo no Graphiti (grupos sao criados implicitamente na primeira mensagem), Envia o contexto da ontologia como mensagem de sistema.          O Graphiti nao, Adicionar texto ao grafo em lotes via POST /messages.          IMPORTANTE: Todos, Obter informacoes do grafo via busca ampla.

### Community 107 - "build_report_evolution_readiness"
Cohesion: 0.36
Nodes (11): _artifact(), _blockers(), build_report_evolution_readiness(), _content_consistency(), _count_evolution_runs(), _gaps(), _latest_run_status(), Any (+3 more)

### Community 108 - "ZepGraphMemoryUpdater"
Cohesion: 0.27
Nodes (4): Atualizador de memoria em grafo via Graphiti Server.      Monitora os logs de ac, Inicializa o atualizador.          Args:             graph_id: Identificador do, Envia um lote de atividades ao Graphiti como mensagens., ZepGraphMemoryUpdater

### Community 109 - "CostGuard"
Cohesion: 0.17
Nodes (5): CostGuard, Controle de custo para experimentos AutoResearch., Rastreia gastos e bloqueia quando budget atingido., Registra tokens consumidos e atualiza custo., Retorna True se ainda ha budget e tempo disponivel.

### Community 110 - "llm_client.py"
Cohesion: 0.24
Nodes (9): _ChatChoice, _ChatMessage, _ChatResponse, _ChatUsage, _extract_balanced_json(), Cliente unificado de LLM.  Opera sobre provedores compativeis com a API OpenAI e, Tenta um provider especifico com max_retries retries., Extrai o primeiro objeto/array JSON balanceado de uma resposta textual. (+1 more)

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
Cohesion: 0.25
Nodes (8): evaluate_section_grounding(), Avalia uma secao do relatorio: tem numero? tem citacao? tem entidade do grafo?, Secao sem aspas mas com numero (0.4) + 2 entidades (0.2) = 0.6 -> passa., Entidades com <3 chars sao ignoradas para evitar falsos positivos., test_grounding_aprova_secao_com_numero_quote_entidade(), test_grounding_aprova_so_com_numero_e_entidade(), test_grounding_ignora_entidades_curtas(), test_grounding_rejeita_secao_narrativa_generica()

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
Cohesion: 0.50
Nodes (3): Rastreamento de consumo de tokens, custo tecnico e valor INTEIA., _round_brl(), _round_usd()

### Community 122 - ".path"
Cohesion: 0.40
Nodes (3): Path, Verifica se o asset modificado ainda respeita as restricoes., Caminho do asset principal.

### Community 123 - "createExportDraft"
Cohesion: 0.60
Nodes (5): createExportDraft(), formatExportError(), getExportId(), loadReportExports(), verifyExportBundle()

### Community 124 - "vercel.json"
Cohesion: 0.40
Nodes (4): buildCommand, installCommand, outputDirectory, rewrites

### Community 128 - "closeModal"
Cohesion: 0.50
Nodes (4): closeModal(), goToProject(), goToReport(), goToSimulation()

### Community 129 - "get_graph_status"
Cohesion: 0.67
Nodes (3): get_graph_status(), Retorna estado operacional do backend de grafo., test_graph_status_retorna_fallback_quando_graphiti_indisponivel()

### Community 131 - "report_section_workers"
Cohesion: 0.67
Nodes (3): Limita concorrencia de secoes ao que o provedor LLM suporta., report_section_workers(), test_report_section_workers_padrao_serial_e_limite()

### Community 137 - "approveAndExecute"
Cohesion: 0.67
Nodes (3): addExecutionLog(), approveAndExecute(), summarizeResult()

## Knowledge Gaps
- **462 isolated node(s):** `Signal`, `mirofish-backend`, `name`, `private`, `version` (+457 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `PowerCatalog`, `create_app`, `report_agent.py`, `report.py`, `cli.py`, `datetime`, `graph.py`, `internal.py`, `.chat`, `ProjectManager`, `llm_client.py`, `report_system_gate.py`, `EntityNode`, `OntologyGenerator`, `test_helena_control_api.py`, `simulation.py`, `simulation_runner.py`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `LLMClient` to `report_agent.py`, `Any`, `Any`, `cli.py`, `TextProcessor`, `graph.py`, `llm_client.py`, `.chat`, `TokenTracker`, `EntityNode`, `ZepGraphiti`, `OntologyGenerator`, `GraphitiClient`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `ReportManager` connect `ReportManager` to `report_agent.py`, `build_executive_package`, `test_report_quality.py`, `report.py`, `report_exporter.py`, `internal.py`, `SimulationManager`, `report_system_gate.py`, `SimulationRunState`, `harness_evidence_bundle.py`, `ForecastLedger`, `evaluate_report_method_checklist`, `Flask`, `repair_report_finalization`, `report_content_repair.py`, `StrategicDensityGate`, `SimulationRunner`, `create_app`, `AgentAction`, `report_diagrams.py`, `Config`, `simulation_runner.py`, `test_report_exports_api.py`, `build_report_evolution_readiness`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `ReportManager` (e.g. with `ExecutivePackageConflict` and `ExecutivePackageError`) actually correct?**
  _`ReportManager` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `ReportAgent` (e.g. with `ForecastLedger` and `MissionBundle`) actually correct?**
  _`ReportAgent` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `SimulationManager` (e.g. with `Report` and `ReportAgent`) actually correct?**
  _`SimulationManager` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `SimulationRunner` (e.g. with `Report` and `ReportAgent`) actually correct?**
  _`SimulationRunner` has 31 INFERRED edges - model-reasoned connections that need verification._