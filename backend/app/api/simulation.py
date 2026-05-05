"""
Rotas de API de simulacao
Step2: Leitura e filtragem de entidades Zep, preparacao e execucao OASIS (totalmente automatizado)
"""

import os
import traceback
from flask import request, jsonify, send_file

from . import simulation_bp
from ..config import Config
from ..services.zep_entity_reader import ZepEntityReader
from ..services.oasis_profile_generator import OasisProfileGenerator
from ..services.simulation_manager import SimulationManager, SimulationStatus
from ..services.simulation_runner import SimulationRunner, RunnerStatus
from ..utils.logger import get_logger
from ..models.project import ProjectManager

logger = get_logger('mirofish.api.simulation')


# Prefixo de otimizacao do prompt de Interview
# Adicionar este prefixo evita que o Agent chame ferramentas, respondendo diretamente com texto
INTERVIEW_PROMPT_PREFIX = "Com base no seu perfil, todas as memorias e acoes passadas, responda diretamente em texto sem chamar nenhuma ferramenta:"


def optimize_interview_prompt(prompt: str) -> str:
    """
    Otimiza pergunta do Interview, adiciona prefixo para evitar chamada de ferramentas

    Args:
        prompt: Pergunta original

    Returns:
        Pergunta otimizada
    """
    if not prompt:
        return prompt
    # Evita adicionar prefixo duplicado
    if prompt.startswith(INTERVIEW_PROMPT_PREFIX):
        return prompt
    return f"{INTERVIEW_PROMPT_PREFIX}{prompt}"


# ============== Interface de leitura de entidades ==============

@simulation_bp.route('/entities/<graph_id>', methods=['GET'])
def get_graph_entities(graph_id: str):
    """
    Obtem todas as entidades do grafo (filtradas)

    Retorna apenas nos de tipos predefinidos (Labels alem de Entity)

    Parametros de Query:
        entity_types: lista separada por virgula (opcional, para filtragem)
        enrich: se obtem informacoes de arestas (padrao true)
    """
    try:
        entity_types_str = request.args.get('entity_types', '')
        entity_types = [t.strip() for t in entity_types_str.split(',') if t.strip()] if entity_types_str else None
        enrich = request.args.get('enrich', 'true').lower() == 'true'

        logger.info(f"Obtendo entidades do grafo: graph_id={graph_id}, entity_types={entity_types}, enrich={enrich}")

        reader = ZepEntityReader()
        result = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=enrich
        )

        return jsonify({
            "success": True,
            "data": result.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha ao obter entidades do grafo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/entities/<graph_id>/<entity_uuid>', methods=['GET'])
def get_entity_detail(graph_id: str, entity_uuid: str):
    """Obtem informacoes detalhadas de uma entidade"""
    try:
        reader = ZepEntityReader()
        entity = reader.get_entity_with_context(graph_id, entity_uuid)

        if not entity:
            return jsonify({
                "success": False,
                "error": f"Entidade não encontrada: {entity_uuid}"
            }), 404

        return jsonify({
            "success": True,
            "data": entity.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha ao obter detalhes da entidade: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/entities/<graph_id>/by-type/<entity_type>', methods=['GET'])
def get_entities_by_type(graph_id: str, entity_type: str):
    """Obtem todas as entidades de um tipo"""
    try:
        enrich = request.args.get('enrich', 'true').lower() == 'true'

        reader = ZepEntityReader()
        entities = reader.get_entities_by_type(
            graph_id=graph_id,
            entity_type=entity_type,
            enrich_with_edges=enrich
        )

        return jsonify({
            "success": True,
            "data": {
                "entity_type": entity_type,
                "count": len(entities),
                "entities": [e.to_dict() for e in entities]
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter entidades: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de gerenciamento de simulacao ==============

@simulation_bp.route('/create', methods=['POST'])
def create_simulation():
    """
    Criar nova simulacao

    Nota: parametros como max_rounds sao gerados pelo LLM, sem necessidade de configuracao manual

    Requisicao (JSON):
        {
            "project_id": "proj_xxxx",      // obrigatorio
            "graph_id": "mirofish_xxxx",    // opcional, se nao fornecido sera obtido do project
            "enable_twitter": true,          // opcional, padrao true
            "enable_reddit": true            // opcional, padrao true
        }

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "project_id": "proj_xxxx",
                "graph_id": "mirofish_xxxx",
                "status": "created",
                "enable_twitter": true,
                "enable_reddit": true,
                "created_at": "2025-12-01T10:00:00"
            }
        }
    """
    try:
        data = request.get_json() or {}

        project_id = data.get('project_id')
        if not project_id:
            return jsonify({
                "success": False,
                "error": "Informe o project_id"
            }), 400

        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto não encontrado: {project_id}"
            }), 404

        graph_id = data.get('graph_id') or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "O projeto ainda não possui um grafo construído. Execute primeiro /api/graph/build"
            }), 400

        manager = SimulationManager()
        state = manager.create_simulation(
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=data.get('enable_twitter', True),
            enable_reddit=data.get('enable_reddit', True),
        )

        return jsonify({
            "success": True,
            "data": state.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha ao criar simulacao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _check_simulation_prepared(simulation_id: str) -> tuple:
    """
    Verifica se a simulacao ja foi preparada

    Condicoes de verificacao:
    1. state.json existe e status e "ready"
    2. Arquivos necessarios existem

    Nota: scripts (run_*.py) permanecem em backend/scripts/

    Args:
        simulation_id: ID da simulacao

    Returns:
        (is_prepared: bool, info: dict)
    """
    import os
    from ..config import Config

    simulation_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)

    # Verifica se o diretorio existe
    if not os.path.exists(simulation_dir):
        return False, {"reason": "Diretório da simulação não encontrado"}

    # Lista de arquivos obrigatorios (scripts em backend/scripts/)
    required_files = [
        "state.json",
        "simulation_config.json",
        "reddit_profiles.json",
        "twitter_profiles.csv"
    ]

    # Verifica se arquivo existe
    existing_files = []
    missing_files = []
    for f in required_files:
        file_path = os.path.join(simulation_dir, f)
        if os.path.exists(file_path):
            existing_files.append(f)
        else:
            missing_files.append(f)

    if missing_files:
        return False, {
            "reason": "Arquivos obrigatórios ausentes",
            "missing_files": missing_files,
            "existing_files": existing_files
        }

    # Verifica o estado no state.json
    state_file = os.path.join(simulation_dir, "state.json")
    try:
        import json
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        status = state_data.get("status", "")
        config_generated = state_data.get("config_generated", False)

        # Log detalhado
        logger.debug(f"Verificando estado de preparacao da simulacao: {simulation_id}, status={status}, config_generated={config_generated}")

        # Se config_generated=True e arquivos existem, preparacao concluida
        # Os seguintes estados indicam preparacao concluida:
        # - ready: preparacao concluida, pode executar
        # - preparing: se config_generated=True indica conclusao
        # - running: em execucao, preparacao ja concluida
        # - completed: concluido, preparacao ja concluida
        # - stopped: parado, preparacao ja concluida
        # - failed: falhou (mas preparacao concluida)
        prepared_statuses = ["ready", "preparing", "running", "completed", "stopped", "failed"]
        if status in prepared_statuses and config_generated:
            # Obtem estatisticas dos arquivos
            profiles_file = os.path.join(simulation_dir, "reddit_profiles.json")
            config_file = os.path.join(simulation_dir, "simulation_config.json")

            profiles_count = 0
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                    profiles_count = len(profiles_data) if isinstance(profiles_data, list) else 0

            # Se preparing mas arquivos completos, atualiza para ready
            if status == "preparing":
                try:
                    state_data["status"] = "ready"
                    from datetime import datetime
                    state_data["updated_at"] = datetime.now().isoformat()
                    with open(state_file, 'w', encoding='utf-8') as f:
                        json.dump(state_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"Atualizacao automatica do estado da simulacao: {simulation_id} preparing -> ready")
                    status = "ready"
                except Exception as e:
                    logger.warning(f"Falha na atualizacao automatica do estado: {e}")

            logger.info(f"Simulacao {simulation_id} Resultado: preparacao concluida (status={status}, config_generated={config_generated})")
            return True, {
                "status": status,
                "entities_count": state_data.get("entities_count", 0),
                "profiles_count": profiles_count,
                "entity_types": state_data.get("entity_types", []),
                "config_generated": config_generated,
                "created_at": state_data.get("created_at"),
                "updated_at": state_data.get("updated_at"),
                "existing_files": existing_files
            }
        else:
            logger.warning(f"Simulacao {simulation_id} Resultado: preparacao nao concluida (status={status}, config_generated={config_generated})")
            return False, {
                "reason": f"Estado nao na lista de preparados ou config_generated e false: status={status}, config_generated={config_generated}",
                "status": status,
                "config_generated": config_generated
            }

    except Exception as e:
        return False, {"reason": f"Falha ao ler o arquivo de estado: {str(e)}"}


@simulation_bp.route('/prepare', methods=['POST'])
def prepare_simulation():
    """
    Preparar ambiente (tarefa assincrona, LLM gera parametros)

    Operacao demorada, interface retorna task_id imediatamente,
    use GET /api/simulation/prepare/status para consultar progresso

    Caracteristicas:
    - Detecta preparacoes concluidas, evitando geracao duplicada
    - Se ja preparado, retorna resultados existentes
    - Suporta regeneracao forcada (force_regenerate=true)

    Etapas:
    1. Verifica se ja existe preparacao concluida
    2. Le e filtra entidades do grafo Zep
    3. Gera Agent Profile para cada entidade (com retentativa)
    4. LLM gera configuracao (com retentativa)
    5. Salva configuracao e scripts

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",                   // obrigatorio, ID da simulacao
            "entity_types": ["Student", "PublicFigure"],  // opcional, tipos de entidade
            "use_llm_for_profiles": true,                 // opcional, usar LLM para perfis
            "parallel_profile_count": 5,                  // opcional, paralelismo, padrao 5
            "force_regenerate": false,                    // opcional, forcar regeneracao, padrao false
            "enrich_queries": ["query1", "query2"],       // opcional, queries Google via Apify
            "enrich_actors": ["@handle1", "@handle2"]     // opcional, perfis Instagram via Apify
        }

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",           // retornado para nova tarefa
                "status": "preparing|ready",
                "message": "Tarefa de preparação iniciada | preparação já concluída",
                "already_prepared": true|false    // se ja esta preparada
            }
        }
    """
    import threading
    import os
    from ..models.task import TaskManager, TaskStatus
    from ..config import Config

    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        # Verifica se deve forcar regeneracao
        force_regenerate = data.get('force_regenerate', False)
        logger.info(f"Iniciando processamento da requisicao /prepare: simulation_id={simulation_id}, force_regenerate={force_regenerate}")

        # Verifica se ja esta preparado (evita geracao duplicada)
        if not force_regenerate:
            logger.debug(f"Verificando simulacao {simulation_id} se ja esta preparada...")
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            logger.debug(f"Resultado da verificacao: is_prepared={is_prepared}, prepare_info={prepare_info}")
            if is_prepared:
                logger.info(f"Simulacao {simulation_id} ja preparada, pulando geracao duplicada")
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "message": "A preparação já foi concluída anteriormente. Não é necessário gerar novamente.",
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })
            else:
                logger.info(f"Simulacao {simulation_id} nao preparada, iniciando tarefa de preparacao")

        # Obtem informacoes necessarias do projeto
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto não encontrado: {state.project_id}"
            }), 404

        # Obtem requisitos da simulacao
        simulation_requirement = project.simulation_requirement or ""
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "O projeto não possui a descrição do objetivo da simulação (simulation_requirement)"
            }), 400

        # Obtem texto do documento
        document_text = ProjectManager.get_extracted_text(state.project_id) or ""

        # Enriquecimento Apify (opcional)
        enrich_queries = data.get('enrich_queries', [])
        enrich_actors = data.get('enrich_actors', [])
        enrich_ig_posts = data.get('enrich_ig_posts', [])
        enrich_ig_tagged = data.get('enrich_ig_tagged', [])
        enrich_youtube = data.get('enrich_youtube', [])
        enrich_auto = data.get('enrich_auto', False)
        has_enrich = any([enrich_queries, enrich_actors, enrich_ig_posts,
                          enrich_ig_tagged, enrich_youtube, enrich_auto])
        if has_enrich:
            try:
                from ..services.apify_enricher import ApifyEnricher
                enrich_profile = data.get('enrich_profile', 'lean')
                enricher = ApifyEnricher(profile=enrich_profile)
                if enrich_auto and not any([enrich_queries, enrich_actors]):
                    targets = enricher.extract_targets_from_text(
                        document_text + "\n" + simulation_requirement
                    )
                    enrich_queries = enrich_queries or targets.get("queries", [])
                    enrich_actors = enrich_actors or targets.get("ig_handles", [])
                    enrich_youtube = enrich_youtube or targets.get("yt_urls", [])
                    enrich_ig_posts = enrich_ig_posts or enrich_actors
                    logger.info(f"Apify auto: {len(enrich_queries)} queries, "
                                f"{len(enrich_actors)} IG, {len(enrich_youtube)} YT")
                import queue

                result_queue = queue.Queue(maxsize=1)

                def run_enrichment():
                    try:
                        result_queue.put({
                            "block": enricher.build_enrichment_block(
                                queries=enrich_queries,
                                actors_instagram=enrich_actors,
                                ig_posts_handles=enrich_ig_posts,
                                ig_tagged_handles=enrich_ig_tagged,
                                youtube_urls=enrich_youtube,
                                project_id=state.project_id,
                            )
                        })
                    except Exception as enrich_error:
                        result_queue.put({"error": enrich_error})

                timeout_seconds = float(os.environ.get("APIFY_ENRICH_TIMEOUT_SECONDS", "45"))
                enrich_thread = threading.Thread(target=run_enrichment, daemon=True)
                enrich_thread.start()

                try:
                    enrich_result = result_queue.get(timeout=timeout_seconds)
                except queue.Empty:
                    logger.warning(
                        "Apify enrichment excedeu %.0fs e foi ignorado; "
                        "simulacao prossegue sem bloquear.",
                        timeout_seconds,
                    )
                    enrich_result = {
                        "block": (
                            "# Enriquecimento Apify\n\n"
                            "Apify foi solicitado, mas nao retornou dentro do "
                            f"limite operacional de {timeout_seconds:.0f}s. "
                            "A simulacao prosseguiu com o briefing consolidado "
                            "e deve tratar a ausencia de enriquecimento externo "
                            "como limitacao metodologica.\n"
                        )
                    }

                if enrich_result.get("error"):
                    raise enrich_result["error"]

                block = enrich_result.get("block", "")
                if block:
                    document_text = document_text.rstrip() + "\n\n" + block + "\n"
                    logger.info(f"Apify: {len(block)} chars anexados ao contexto")
            except Exception as e:
                logger.warning(f"Apify enrichment falhou (simulacao prossegue sem): {e}")

        entity_types_list = data.get('entity_types')
        use_llm_for_profiles = data.get('use_llm_for_profiles', True)
        parallel_profile_count = data.get('parallel_profile_count', 5)

        # ========== Obtendo quantidade de entidades sincronamente ==========
        # Assim o frontend obtem total esperado imediatamente
        try:
            logger.info(f"Obtendo quantidade de entidades sincronamente: graph_id={state.graph_id}")
            reader = ZepEntityReader()
            # Leitura rapida (sem arestas, apenas contagem)
            filtered_preview = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=entity_types_list,
                enrich_with_edges=False  # Sem arestas, mais rapido
            )
            # Salva quantidade no estado (para frontend obter imediatamente)
            state.entities_count = filtered_preview.filtered_count
            state.entity_types = list(filtered_preview.entity_types)
            logger.info(f"Quantidade esperada de entidades: {filtered_preview.filtered_count}, tipos: {filtered_preview.entity_types}")
        except Exception as e:
            logger.warning(f"Falha ao obter quantidade de entidades (sera retentado em segundo plano): {e}")
            # Falha nao afeta fluxo, tarefa em segundo plano ira reobtter

        # Cria tarefa assincrona
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="simulation_prepare",
            metadata={
                "simulation_id": simulation_id,
                "project_id": state.project_id
            }
        )

        # Atualiza estado (contendo quantidade pre-obtida)
        state.status = SimulationStatus.PREPARING
        manager._save_simulation_state(state)

        # Define tarefa em segundo plano
        def run_prepare():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="Iniciando preparacao do ambiente de simulacao..."
                )

                # Prepara simulacao (com callback de progresso)
                # Armazena detalhes de progresso por etapa
                stage_details = {}

                def progress_callback(stage, progress, message, **kwargs):
                    # Calcula progresso total
                    stage_weights = {
                        "reading": (0, 20),           # 0-20%
                        "generating_profiles": (20, 70),  # 20-70%
                        "generating_config": (70, 90),    # 70-90%
                        "copying_scripts": (90, 100)       # 90-100%
                    }

                    start, end = stage_weights.get(stage, (0, 100))
                    current_progress = int(start + (end - start) * progress / 100)

                    # Constroi informacoes de progresso
                    stage_names = {
                        "reading": "Lendo entidades do grafo",
                        "generating_profiles": "Gerando perfis de Agent",
                        "generating_config": "Gerando configuracao",
                        "copying_scripts": "Preparando scripts"
                    }

                    stage_index = list(stage_weights.keys()).index(stage) + 1 if stage in stage_weights else 1
                    total_stages = len(stage_weights)

                    # Atualiza detalhes da etapa
                    stage_details[stage] = {
                        "stage_name": stage_names.get(stage, stage),
                        "stage_progress": progress,
                        "current": kwargs.get("current", 0),
                        "total": kwargs.get("total", 0),
                        "item_name": kwargs.get("item_name", "")
                    }

                    # Constroi informacoes de progresso
                    detail = stage_details[stage]
                    progress_detail_data = {
                        "current_stage": stage,
                        "current_stage_name": stage_names.get(stage, stage),
                        "stage_index": stage_index,
                        "total_stages": total_stages,
                        "stage_progress": progress,
                        "current_item": detail["current"],
                        "total_items": detail["total"],
                        "item_description": message
                    }

                    # Constroi mensagem concisa
                    if detail["total"] > 0:
                        detailed_message = (
                            f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: "
                            f"{detail['current']}/{detail['total']} - {message}"
                        )
                    else:
                        detailed_message = f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: {message}"

                    task_manager.update_task(
                        task_id,
                        progress=current_progress,
                        message=detailed_message,
                        progress_detail=progress_detail_data
                    )

                result_state = manager.prepare_simulation(
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    document_text=document_text,
                    defined_entity_types=entity_types_list,
                    use_llm_for_profiles=use_llm_for_profiles,
                    progress_callback=progress_callback,
                    parallel_profile_count=parallel_profile_count
                )

                # Tarefa concluida
                task_manager.complete_task(
                    task_id,
                    result=result_state.to_simple_dict()
                )

            except Exception as e:
                logger.error(f"Falha ao preparar simulacao: {str(e)}")
                logger.error(traceback.format_exc())
                task_manager.fail_task(task_id, str(e))

                # Atualiza estado para falha
                state = manager.get_simulation(simulation_id)
                if state:
                    state.status = SimulationStatus.FAILED
                    state.error = str(e)
                    manager._save_simulation_state(state)

        # Inicia thread em segundo plano
        thread = threading.Thread(target=run_prepare, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "task_id": task_id,
                "status": "preparing",
                "message": "A tarefa de preparação foi iniciada. Consulte o progresso em /api/simulation/prepare/status",
                "already_prepared": False,
                "expected_entities_count": state.entities_count,  # Total esperado de Agents
                "entity_types": state.entity_types  # Lista de tipos de entidade
            }
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

    except Exception as e:
        logger.error(f"Falha ao iniciar tarefa de preparacao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/prepare/status', methods=['POST'])
def get_prepare_status():
    """
    Consultar progresso da tarefa de preparacao

    Suporta dois modos de consulta:
    1. Via task_id para tarefa em andamento
    2. Via simulation_id para verificar preparacao

    Requisicao (JSON):
        {
            "task_id": "task_xxxx",          // opcional, task_id retornado por prepare
            "simulation_id": "sim_xxxx"      // opcional, ID da simulacao
        }

    Retorno:
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|ready",
                "progress": 45,
                "message": "...",
                "already_prepared": true|false,  // se ja existe preparacao concluida
                "prepare_info": {...}            // informacoes quando ja preparado
            }
        }
    """
    from ..models.task import TaskManager

    try:
        data = request.get_json() or {}

        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')

        # Se simulation_id fornecido, verifica primeiro
        if simulation_id:
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            if is_prepared:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "progress": 100,
                        "message": "A preparação já foi concluída",
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })

        # Se nao tem task_id, retorna erro
        if not task_id:
            if simulation_id:
                # Tem simulation_id mas nao preparado
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "not_started",
                        "progress": 0,
                        "message": "A preparação ainda não foi iniciada. Execute /api/simulation/prepare para começar.",
                        "already_prepared": False
                    }
                })
            return jsonify({
                "success": False,
                "error": "Informe task_id ou simulation_id"
            }), 400

        task_manager = TaskManager()
        task = task_manager.get_task(task_id)

        if not task:
            # Tarefa nao existe, verifica se preparado
            if simulation_id:
                is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
                if is_prepared:
                    return jsonify({
                        "success": True,
                        "data": {
                            "simulation_id": simulation_id,
                            "task_id": task_id,
                            "status": "ready",
                            "progress": 100,
                            "message": "Tarefa concluída (a preparação já existia)",
                            "already_prepared": True,
                            "prepare_info": prepare_info
                        }
                    })

            return jsonify({
                "success": False,
                "error": f"Tarefa não encontrada: {task_id}"
            }), 404

        task_dict = task.to_dict()
        task_dict["already_prepared"] = False

        return jsonify({
            "success": True,
            "data": task_dict
        })

    except Exception as e:
        logger.error(f"Falha ao consultar estado da tarefa: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id: str):
    """Obter estado da simulacao"""
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        result = state.to_dict()

        # Se simulacao pronta, anexa instrucoes
        if state.status == SimulationStatus.READY:
            result["run_instructions"] = manager.get_run_instructions(simulation_id)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Falha ao obter estado da simulacao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/quality', methods=['GET'])
def get_simulation_quality(simulation_id: str):
    """
    Obter diagnostico de qualidade da simulacao para relatorio.

    Consolida diversidade comportamental, diversidade semantica e gate estrutural
    antes de permitir entrega conclusiva.
    """
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        source_text = None
        try:
            source_text = ProjectManager.get_extracted_text(state.project_id)
        except Exception:
            pass

        require_completed_arg = request.args.get('require_completed')
        require_completed = None
        if require_completed_arg is not None:
            require_completed = require_completed_arg.lower() in {"1", "true", "sim", "yes"}

        from ..services.report_system_gate import evaluate_report_system_gate

        gate_result = evaluate_report_system_gate(
            simulation_id=simulation_id,
            graph_id=request.args.get('graph_id') or state.graph_id,
            source_text=source_text,
            require_completed_simulation=require_completed,
            delivery_mode=request.args.get('delivery_mode'),
        )

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "simulation_status": state.status.value,
                "project_id": state.project_id,
                "graph_id": state.graph_id,
                "diversity": gate_result.metrics.get("diversity", {}),
                "report_gate": gate_result.to_dict(),
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter diagnostico de qualidade da simulacao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/list', methods=['GET'])
def list_simulations():
    """
    Listar todas as simulacoes

    Parametros de Query:
        project_id: filtrar por ID do projeto (opcional)
    """
    try:
        project_id = request.args.get('project_id')

        manager = SimulationManager()
        simulations = manager.list_simulations(project_id=project_id)

        return jsonify({
            "success": True,
            "data": [s.to_dict() for s in simulations],
            "count": len(simulations)
        })

    except Exception as e:
        logger.error(f"Falha ao listar simulacoes: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _get_report_id_for_simulation(simulation_id: str) -> str:
    """
    Obtem report_id mais recente da simulacao

    Percorre reports, encontra o correspondente,
    se multiplos retorna o mais recente

    Args:
        simulation_id: ID da simulacao

    Returns:
        report_id ou None
    """
    import json
    from datetime import datetime

    # Caminho: backend/uploads/reports
    # __file__ e app/api/simulation.py, sobe dois niveis ate backend/
    reports_dir = os.path.join(os.path.dirname(__file__), '../../uploads/reports')
    if not os.path.exists(reports_dir):
        return None

    matching_reports = []

    try:
        for report_folder in os.listdir(reports_dir):
            report_path = os.path.join(reports_dir, report_folder)
            if not os.path.isdir(report_path):
                continue

            meta_file = os.path.join(report_path, "meta.json")
            if not os.path.exists(meta_file):
                continue

            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

                if meta.get("simulation_id") == simulation_id:
                    matching_reports.append({
                        "report_id": meta.get("report_id"),
                        "created_at": meta.get("created_at", ""),
                        "status": meta.get("status", "")
                    })
            except Exception:
                continue

        if not matching_reports:
            return None

        # Ordena por data decrescente, retorna mais recente
        matching_reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return matching_reports[0].get("report_id")

    except Exception as e:
        logger.warning(f"Buscar simulation {simulation_id}  - falha ao buscar report: {e}")
        return None


@simulation_bp.route('/history', methods=['GET'])
def get_simulation_history():
    """
    Obtem lista de simulacoes historicas (com detalhes do projeto)

    Para exibicao na pagina inicial, retorna lista enriquecida

    Parametros de Query:
        limit: limite (padrao 20)

    Retorno:
        {
            "success": true,
            "data": [
                {
                    "simulation_id": "sim_xxxx",
                    "project_id": "proj_xxxx",
                    "project_name": "Analise de repercussao publica",
                    "simulation_requirement": "Se a universidade publicar...",
                    "status": "completed",
                    "entities_count": 68,
                    "profiles_count": 68,
                    "entity_types": ["Student", "Professor", ...],
                    "created_at": "2024-12-10",
                    "updated_at": "2024-12-10",
                    "total_rounds": 120,
                    "current_round": 120,
                    "report_id": "report_xxxx",
                    "version": "v1.0.2"
                },
                ...
            ],
            "count": 7
        }
    """
    try:
        limit = request.args.get('limit', 20, type=int)

        manager = SimulationManager()
        simulations = manager.list_simulations()[:limit]

        # Enriquece dados da simulacao
        enriched_simulations = []
        for sim in simulations:
            sim_dict = sim.to_dict()

            # Obtem configuracao (le simulation_requirement)
            config = manager.get_simulation_config(sim.simulation_id)
            if config:
                sim_dict["simulation_requirement"] = config.get("simulation_requirement", "")
                time_config = config.get("time_config", {})
                sim_dict["total_simulation_hours"] = time_config.get("total_simulation_hours", 0)
                # Rodadas recomendadas (fallback)
                recommended_rounds = int(
                    time_config.get("total_simulation_hours", 0) * 60 /
                    max(time_config.get("minutes_per_round", 60), 1)
                )
            else:
                sim_dict["simulation_requirement"] = ""
                sim_dict["total_simulation_hours"] = 0
                recommended_rounds = 0

            # Obtem estado de execucao (rodadas do usuario)
            run_state = SimulationRunner.get_run_state(sim.simulation_id)
            if run_state:
                sim_dict["current_round"] = run_state.current_round
                sim_dict["runner_status"] = run_state.runner_status.value
                # Usa total_rounds do usuario, senao usa recomendado
                sim_dict["total_rounds"] = run_state.total_rounds if run_state.total_rounds > 0 else recommended_rounds
            else:
                sim_dict["current_round"] = 0
                sim_dict["runner_status"] = "idle"
                sim_dict["total_rounds"] = recommended_rounds

            # Obtem arquivos do projeto (maximo 3)
            project = ProjectManager.get_project(sim.project_id)
            if project and hasattr(project, 'files') and project.files:
                sim_dict["files"] = [
                    {"filename": f.get("filename", "Arquivo desconhecido")}
                    for f in project.files[:3]
                ]
            else:
                sim_dict["files"] = []

            # Obtem report_id (busca report mais recente)
            sim_dict["report_id"] = _get_report_id_for_simulation(sim.simulation_id)

            # Adiciona versao
            sim_dict["version"] = "v1.0.2"

            # Formata data
            try:
                created_date = sim_dict.get("created_at", "")[:10]
                sim_dict["created_date"] = created_date
            except:
                sim_dict["created_date"] = ""

            enriched_simulations.append(sim_dict)

        return jsonify({
            "success": True,
            "data": enriched_simulations,
            "count": len(enriched_simulations)
        })

    except Exception as e:
        logger.error(f"Falha ao obter simulacoes historicas: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/profiles', methods=['GET'])
def get_simulation_profiles(simulation_id: str):
    """
    Obter Agent Profile da simulacao

    Parametros de Query:
        platform: tipo (reddit/twitter, padrao reddit)
    """
    try:
        platform = request.args.get('platform', 'reddit')

        manager = SimulationManager()
        profiles = manager.get_profiles(simulation_id, platform=platform)

        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "count": len(profiles),
                "profiles": profiles
            }
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

    except Exception as e:
        logger.error(f"Falha ao obter Profile: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/profiles/realtime', methods=['GET'])
def get_simulation_profiles_realtime(simulation_id: str):
    """
    Obter Agent Profile em tempo real (durante geracao)

    Diferenca de /profiles:
    - Le arquivos diretamente
    - Para visualizacao em tempo real
    - Retorna metadados adicionais (horario de modificacao, etc.)

    Parametros de Query:
        platform: tipo (reddit/twitter, padrao reddit)

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "platform": "reddit",
                "count": 15,
                "total_expected": 93,  // total esperado (se disponivel)
                "is_generating": true,  // se esta gerando
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "profiles": [...]
            }
        }
    """
    import json
    import csv
    from datetime import datetime

    try:
        platform = request.args.get('platform', 'reddit')

        # Obtem diretorio da simulacao
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)

        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        # Determina caminho do arquivo
        if platform == "reddit":
            profiles_file = os.path.join(sim_dir, "reddit_profiles.json")
        else:
            profiles_file = os.path.join(sim_dir, "twitter_profiles.csv")

        # Verifica se arquivo existe
        file_exists = os.path.exists(profiles_file)
        profiles = []
        file_modified_at = None

        if file_exists:
            # Obtem horario de modificacao
            file_stat = os.stat(profiles_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

            try:
                if platform == "reddit":
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        profiles = json.load(f)
                else:
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        profiles = list(reader)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Falha ao ler arquivo de profiles (pode estar sendo escrito): {e}")
                profiles = []

        # Verifica se esta gerando (via state.json)
        is_generating = False
        total_expected = None

        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    total_expected = state_data.get("entities_count")
            except Exception:
                pass

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "platform": platform,
                "count": len(profiles),
                "total_expected": total_expected,
                "is_generating": is_generating,
                "file_exists": file_exists,
                "file_modified_at": file_modified_at,
                "profiles": profiles
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter Profile em tempo real: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/config/realtime', methods=['GET'])
def get_simulation_config_realtime(simulation_id: str):
    """
    Obter configuracao em tempo real

    Diferenca de /config:
    - Le arquivos diretamente
    - Para visualizacao em tempo real
    - Retorna metadados adicionais (horario de modificacao, etc.)
    - Retorna informacoes parciais

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "is_generating": true,  // se esta gerando
                "generation_stage": "generating_config",  // etapa de geracao atual
                "config": {...}  // conteudo da configuracao (se existir)
            }
        }
    """
    import json
    from datetime import datetime

    try:
        # Obtem diretorio da simulacao
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)

        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        # Caminho do arquivo de configuracao
        config_file = os.path.join(sim_dir, "simulation_config.json")

        # Verifica se arquivo existe
        file_exists = os.path.exists(config_file)
        config = None
        file_modified_at = None

        if file_exists:
            # Obtem horario de modificacao
            file_stat = os.stat(config_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Falha ao ler arquivo de config (pode estar sendo escrito): {e}")
                config = None

        # Verifica se esta gerando (via state.json)
        is_generating = False
        generation_stage = None
        config_generated = False

        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    config_generated = state_data.get("config_generated", False)

                    # Determina etapa atual
                    if is_generating:
                        if state_data.get("profiles_generated", False):
                            generation_stage = "generating_config"
                        else:
                            generation_stage = "generating_profiles"
                    elif status == "ready":
                        generation_stage = "completed"
            except Exception:
                pass

        # Constroi dados de retorno
        response_data = {
            "simulation_id": simulation_id,
            "file_exists": file_exists,
            "file_modified_at": file_modified_at,
            "is_generating": is_generating,
            "generation_stage": generation_stage,
            "config_generated": config_generated,
            "config": config
        }

        # Se configuracao existe, extrai estatisticas
        if config:
            response_data["summary"] = {
                "total_agents": len(config.get("agent_configs", [])),
                "simulation_hours": config.get("time_config", {}).get("total_simulation_hours"),
                "initial_posts_count": len(config.get("event_config", {}).get("initial_posts", [])),
                "hot_topics_count": len(config.get("event_config", {}).get("hot_topics", [])),
                "has_twitter_config": "twitter_config" in config,
                "has_reddit_config": "reddit_config" in config,
                "generated_at": config.get("generated_at"),
                "llm_model": config.get("llm_model")
            }

        return jsonify({
            "success": True,
            "data": response_data
        })

    except Exception as e:
        logger.error(f"Falha ao obter Config em tempo real: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/config', methods=['GET'])
def get_simulation_config(simulation_id: str):
    """
    Obter configuracao (gerada pelo LLM)

    Retorno contendo:
        - time_config: tempo (duracao, rodadas, pico/vale)
        - agent_configs: atividade de cada Agent
        - event_config: eventos (posts iniciais, topicos)
        - platform_configs: plataforma
        - generation_reasoning: raciocinio do LLM
    """
    try:
        manager = SimulationManager()
        config = manager.get_simulation_config(simulation_id)

        if not config:
            return jsonify({
                "success": False,
                "error": "A configuração da simulação não existe. Execute primeiro a rota /prepare."
            }), 404

        return jsonify({
            "success": True,
            "data": config
        })

    except Exception as e:
        logger.error(f"Falha ao obter configuracao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/config/download', methods=['GET'])
def download_simulation_config(simulation_id: str):
    """Baixar configuracao da simulacao"""
    try:
        manager = SimulationManager()
        sim_dir = manager._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")

        if not os.path.exists(config_path):
            return jsonify({
                "success": False,
                "error": "Arquivo de configuração não encontrado. Execute primeiro a rota /prepare."
            }), 404

        return send_file(
            config_path,
            as_attachment=True,
            download_name="simulation_config.json"
        )

    except Exception as e:
        logger.error(f"Falha ao baixar configuracao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/script/<script_name>/download', methods=['GET'])
def download_simulation_script(script_name: str):
    """
    Baixar script de execucao (em backend/scripts/)

    Valores possiveis de script_name:
        - run_twitter_simulation.py
        - run_reddit_simulation.py
        - run_parallel_simulation.py
        - action_logger.py
    """
    try:
        # Scripts em backend/scripts/
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))

        # Valida nome do script
        allowed_scripts = [
            "run_twitter_simulation.py",
            "run_reddit_simulation.py",
            "run_parallel_simulation.py",
            "action_logger.py"
        ]

        if script_name not in allowed_scripts:
            return jsonify({
                "success": False,
                "error": f"Script desconhecido: {script_name}. Opções permitidas: {allowed_scripts}"
            }), 400

        script_path = os.path.join(scripts_dir, script_name)

        if not os.path.exists(script_path):
            return jsonify({
                "success": False,
                "error": f"Arquivo de script não encontrado: {script_name}"
            }), 404

        return send_file(
            script_path,
            as_attachment=True,
            download_name=script_name
        )

    except Exception as e:
        logger.error(f"Falha ao baixar script: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de geracao de Profile (uso independente) ==============

@simulation_bp.route('/generate-profiles', methods=['POST'])
def generate_profiles():
    """
    Gera Agent Profile do grafo (sem criar simulacao)

    Requisicao (JSON):
        {
            "graph_id": "mirofish_xxxx",     // obrigatorio
            "entity_types": ["Student"],      // opcional
            "use_llm": true,                  // opcional
            "platform": "reddit"              // opcional
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Informe o graph_id"
            }), 400

        entity_types = data.get('entity_types')
        use_llm = data.get('use_llm', True)
        platform = data.get('platform', 'reddit')

        reader = ZepEntityReader()
        filtered = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=True
        )

        if filtered.filtered_count == 0:
            return jsonify({
                "success": False,
                "error": "Nenhuma entidade correspondente aos critérios foi encontrada"
            }), 400

        generator = OasisProfileGenerator()
        profiles = generator.generate_profiles_from_entities(
            entities=filtered.entities,
            use_llm=use_llm
        )

        if platform == "reddit":
            profiles_data = [p.to_reddit_format() for p in profiles]
        elif platform == "twitter":
            profiles_data = [p.to_twitter_format() for p in profiles]
        else:
            profiles_data = [p.to_dict() for p in profiles]

        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "entity_types": list(filtered.entity_types),
                "count": len(profiles_data),
                "profiles": profiles_data
            }
        })

    except Exception as e:
        logger.error(f"Falha ao gerar Profile: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de controle de execucao de simulacao ==============

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """
    Iniciar execucao da simulacao

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",          // obrigatorio, ID da simulacao
            "platform": "parallel",                // opcional: twitter / reddit / parallel (padrao)
            "max_rounds": 100,                     // opcional: maximo de rodadas
            "enable_graph_memory_update": false,   // opcional: atualizar memoria do grafo Zep
            "force": false                         // opcional: forcar reinicio
        }

    Sobre o parametro force:
        - Se habilitado, para e limpa logs primeiro
        - Limpa: run_state.json, actions.jsonl, simulation.log, etc.
        - Nao limpa configuracao e profile
        - Para reexecucao da simulacao

    Sobre enable_graph_memory_update:
        - Atividades dos Agents atualizadas no grafo Zep em tempo real
        - Grafo memoriza o processo de simulacao
        - Requer graph_id valido
        - Usa atualizacao em lote

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "process_pid": 12345,
                "twitter_running": true,
                "reddit_running": true,
                "started_at": "2025-12-01T10:00:00",
                "graph_memory_update_enabled": true,  // se a atualizacao de memoria esta habilitada
                "force_restarted": true               // se foi reinicio forcado
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        platform = data.get('platform', 'parallel')
        max_rounds = data.get('max_rounds')  # opcional: maximo de rodadas
        enable_graph_memory_update = data.get('enable_graph_memory_update', False)  # opcional: habilitar atualizacao de memoria do grafo
        force = data.get('force', False)  # opcional: forcar reinicio

        # Valida parametro max_rounds
        if max_rounds is not None:
            try:
                max_rounds = int(max_rounds)
                if max_rounds <= 0:
                    return jsonify({
                        "success": False,
                        "error": "max_rounds deve ser um inteiro positivo"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "max_rounds deve ser um inteiro válido"
                }), 400

        if platform not in ['twitter', 'reddit', 'parallel']:
            return jsonify({
                "success": False,
                "error": f"Tipo de plataforma inválido: {platform}. Opções válidas: twitter/reddit/parallel"
            }), 400

        # Verifica se a simulacao esta pronta
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        force_restarted = False

        # Tratamento inteligente: se preparacao concluida, permite reinicio
        if state.status != SimulationStatus.READY:
            # Verifica se preparacao concluida
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)

            if is_prepared:
                # Preparacao concluida, verifica processos em execucao
                if state.status == SimulationStatus.RUNNING:
                    # Verifica se o processo esta realmente em execucao
                    run_state = SimulationRunner.get_run_state(simulation_id)
                    if run_state and run_state.runner_status.value == "running":
                        # Processo em execucao
                        if force:
                            # Modo forcado: parando simulacao em execucao
                            logger.info(f"Modo forcado: parando simulacao em execucao {simulation_id}")
                            try:
                                SimulationRunner.stop_simulation(simulation_id)
                            except Exception as e:
                                logger.warning(f"Aviso ao parar simulacao: {str(e)}")
                                logger.error(traceback.format_exc())
                        else:
                            return jsonify({
                                "success": False,
                                "error": "A simulação está em execução. Pare primeiro pela rota /stop ou use force=true para reiniciar à força."
                            }), 400

                # Se modo forcado, limpa logs
                if force:
                    logger.info(f"Modo forcado: limpando logs {simulation_id}")
                    cleanup_result = SimulationRunner.cleanup_simulation_logs(simulation_id)
                    if not cleanup_result.get("success"):
                        logger.warning(f"Aviso ao limpar logs: {cleanup_result.get('errors')}")
                    force_restarted = True

                # Processo nao existe ou terminou, reseta para ready
                logger.info(f"Simulacao {simulation_id} preparacao concluida, resetando para ready (estado anterior: {state.status.value}）")
                state.status = SimulationStatus.READY
                manager._save_simulation_state(state)
            else:
                # Preparacao nao concluida
                return jsonify({
                    "success": False,
                    "error": f"A simulação não está pronta. Estado atual: {state.status.value}. Execute primeiro a rota /prepare."
                }), 400

        # Obtem graph_id (para memoria do grafo)
        graph_id = None
        if enable_graph_memory_update:
            # Obtem graph_id do estado ou projeto
            graph_id = state.graph_id
            if not graph_id:
                # Tenta obter do projeto
                project = ProjectManager.get_project(state.project_id)
                if project:
                    graph_id = project.graph_id

            if not graph_id:
                return jsonify({
                    "success": False,
                    "error": "Para habilitar a atualização de memória do grafo é necessário um graph_id válido. Verifique se o projeto já construiu o grafo."
                }), 400

            logger.info(f"Habilitando atualizacao de memoria do grafo: simulation_id={simulation_id}, graph_id={graph_id}")

        # Inicia simulacao
        run_state = SimulationRunner.start_simulation(
            simulation_id=simulation_id,
            platform=platform,
            max_rounds=max_rounds,
            enable_graph_memory_update=enable_graph_memory_update,
            graph_id=graph_id
        )

        # Atualiza estado da simulacao
        state.status = SimulationStatus.RUNNING
        manager._save_simulation_state(state)

        response_data = run_state.to_dict()
        if max_rounds:
            response_data['max_rounds_applied'] = max_rounds
        response_data['graph_memory_update_enabled'] = enable_graph_memory_update
        response_data['force_restarted'] = force_restarted
        if enable_graph_memory_update:
            response_data['graph_id'] = graph_id

        return jsonify({
            "success": True,
            "data": response_data
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        logger.error(f"Falha ao iniciar simulacao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/stop', methods=['POST'])
def stop_simulation():
    """
    Parar simulacao

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx"  // obrigatorio, ID da simulacao
        }

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "stopped",
                "completed_at": "2025-12-01T12:00:00"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        run_state = SimulationRunner.stop_simulation(simulation_id)

        # Atualiza estado da simulacao
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.PAUSED
            manager._save_simulation_state(state)

        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        logger.error(f"Falha ao parar simulacao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de monitoramento em tempo real ==============

@simulation_bp.route('/<simulation_id>/run-status', methods=['GET'])
def get_run_status(simulation_id: str):
    """
    Obter estado de execucao em tempo real (polling do frontend)

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                "total_rounds": 144,
                "progress_percent": 3.5,
                "simulated_hours": 2,
                "total_simulation_hours": 72,
                "twitter_running": true,
                "reddit_running": true,
                "twitter_actions_count": 150,
                "reddit_actions_count": 200,
                "total_actions_count": 350,
                "started_at": "2025-12-01T10:00:00",
                "updated_at": "2025-12-01T10:30:00"
            }
        }
    """
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)

        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "current_round": 0,
                    "total_rounds": 0,
                    "progress_percent": 0,
                    "twitter_actions_count": 0,
                    "reddit_actions_count": 0,
                    "total_actions_count": 0,
                }
            })

        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha ao obter estado de execucao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/run-status/detail', methods=['GET'])
def get_run_status_detail(simulation_id: str):
    """
    Obter estado detalhado (com todas as acoes)

    Para exibicao em tempo real no frontend

    Parametros de Query:
        platform: filtrar (twitter/reddit, opcional)

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                ...
                "all_actions": [
                    {
                        "round_num": 5,
                        "timestamp": "2025-12-01T10:30:00",
                        "platform": "twitter",
                        "agent_id": 3,
                        "agent_name": "Agent Name",
                        "action_type": "CREATE_POST",
                        "action_args": {"content": "..."},
                        "result": null,
                        "success": true
                    },
                    ...
                ],
                "twitter_actions": [...],  # Todas as acoes do Twitter
                "reddit_actions": [...]    # Todas as acoes do Reddit
            }
        }
    """
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        platform_filter = request.args.get('platform')

        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "all_actions": [],
                    "twitter_actions": [],
                    "reddit_actions": []
                }
            })

        # Obtem lista completa de acoes
        all_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter
        )

        # Obtem acoes por plataforma
        twitter_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="twitter"
        ) if not platform_filter or platform_filter == "twitter" else []

        reddit_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="reddit"
        ) if not platform_filter or platform_filter == "reddit" else []

        # Obtem acoes da rodada atual
        current_round = run_state.current_round
        recent_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter,
            round_num=current_round
        ) if current_round > 0 else []

        # Obtem informacoes basicas
        result = run_state.to_dict()
        result["all_actions"] = [a.to_dict() for a in all_actions]
        result["twitter_actions"] = [a.to_dict() for a in twitter_actions]
        result["reddit_actions"] = [a.to_dict() for a in reddit_actions]
        result["rounds_count"] = len(run_state.rounds)
        # recent_actions exibe apenas a rodada mais recente
        result["recent_actions"] = [a.to_dict() for a in recent_actions]

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Falha ao obter estado detalhado: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/actions', methods=['GET'])
def get_simulation_actions(simulation_id: str):
    """
    Obter historico de acoes dos Agents

    Parametros de Query:
        limit: quantidade (padrao 100)
        offset: deslocamento (padrao 0)
        platform: filtrar (twitter/reddit)
        agent_id: filtrar Agent ID
        round_num: filtrar rodada

    Retorno:
        {
            "success": true,
            "data": {
                "count": 100,
                "actions": [...]
            }
        }
    """
    try:
        # 2026-04-18, Phase 7: validacao de limits (evita OOM)
        from ..utils.pagination import get_limit, get_offset
        limit = get_limit(default=100, max_limit=10000)
        offset = get_offset(default=0)
        platform = request.args.get('platform')
        agent_id = request.args.get('agent_id', type=int)
        round_num = request.args.get('round_num', type=int)

        actions = SimulationRunner.get_actions(
            simulation_id=simulation_id,
            limit=limit,
            offset=offset,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )

        return jsonify({
            "success": True,
            "data": {
                "count": len(actions),
                "actions": [a.to_dict() for a in actions]
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter historico de acoes: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/timeline', methods=['GET'])
def get_simulation_timeline(simulation_id: str):
    """
    Obter linha do tempo (resumo por rodada)

    Para barra de progresso no frontend

    Parametros de Query:
        start_round: rodada inicial (padrao 0)
        end_round: rodada final (padrao todas)

    Retorna resumo de cada rodada
    """
    try:
        start_round = request.args.get('start_round', 0, type=int)
        end_round = request.args.get('end_round', type=int)

        timeline = SimulationRunner.get_timeline(
            simulation_id=simulation_id,
            start_round=start_round,
            end_round=end_round
        )

        return jsonify({
            "success": True,
            "data": {
                "rounds_count": len(timeline),
                "timeline": timeline
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter linha do tempo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/agent-stats', methods=['GET'])
def get_agent_stats(simulation_id: str):
    """
    Obter estatisticas de cada Agent

    Para ranking de atividade no frontend
    """
    try:
        stats = SimulationRunner.get_agent_stats(simulation_id)

        return jsonify({
            "success": True,
            "data": {
                "agents_count": len(stats),
                "stats": stats
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter estatisticas dos Agents: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de consulta ao banco de dados ==============

@simulation_bp.route('/<simulation_id>/posts', methods=['GET'])
def get_simulation_posts(simulation_id: str):
    """
    Obter posts da simulacao

    Parametros de Query:
        platform: tipo (twitter/reddit)
        limit: quantidade (padrao 50)
        offset: deslocamento

    Retorna posts (do SQLite)
    """
    try:
        platform = request.args.get('platform', 'reddit')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )

        db_file = f"{platform}_simulation.db"
        db_path = os.path.join(sim_dir, db_file)

        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "platform": platform,
                    "count": 0,
                    "posts": [],
                    "message": "O banco de dados não existe. A simulação pode ainda não ter sido executada."
                }
            })

        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM post
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            posts = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT COUNT(*) FROM post")
            total = cursor.fetchone()[0]

        except sqlite3.OperationalError:
            posts = []
            total = 0

        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "total": total,
                "count": len(posts),
                "posts": posts
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter posts: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>/comments', methods=['GET'])
def get_simulation_comments(simulation_id: str):
    """
    Obter comentarios (apenas Reddit)

    Parametros de Query:
        post_id: filtrar post (opcional)
        limit: quantidade
        offset: deslocamento
    """
    try:
        post_id = request.args.get('post_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )

        db_path = os.path.join(sim_dir, "reddit_simulation.db")

        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "count": 0,
                    "comments": []
                }
            })

        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if post_id:
                cursor.execute("""
                    SELECT * FROM comment
                    WHERE post_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (post_id, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM comment
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            comments = [dict(row) for row in cursor.fetchall()]

        except sqlite3.OperationalError:
            comments = []

        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "count": len(comments),
                "comments": comments
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter comentarios: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de entrevista (Interview) ==============

@simulation_bp.route('/interview', methods=['POST'])
def interview_agent():
    """
    Entrevistar um Agent

    Nota: requer ambiente em modo de espera de comandos

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",       // obrigatorio, ID da simulacao
            "agent_id": 0,                     // obrigatorio，Agent ID
            "prompt": "Qual e a sua opiniao sobre este assunto?",  // obrigatorio, pergunta da entrevista
            "platform": "twitter",             // opcional, especificar plataforma
                                               // sem especificar: entrevista ambas plataformas
            "timeout": 60                      // opcional, timeout (segundos), padrao 60
        }

    Retorno (sem platform, modo dual):
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "Qual e a sua opiniao sobre este assunto?",
                "result": {
                    "agent_id": 0,
                    "prompt": "...",
                    "platforms": {
                        "twitter": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit": {"agent_id": 0, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }

    Retorno (com platform):
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "Qual e a sua opiniao sobre este assunto?",
                "result": {
                    "agent_id": 0,
                    "response": "Eu acredito que...",
                    "platform": "twitter",
                    "timestamp": "2025-12-08T10:00:00"
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        agent_id = data.get('agent_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # opcional: twitter/reddit/None
        timeout = data.get('timeout', 60)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        if agent_id is None:
            return jsonify({
                "success": False,
                "error": "Informe o agent_id"
            }), 400

        if not prompt:
            return jsonify({
                "success": False,
                "error": "Informe o prompt da entrevista"
            }), 400

        # Valida parametro platform
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "O parâmetro platform só pode ser 'twitter' ou 'reddit'"
            }), 400

        # Verifica estado do ambiente
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "O ambiente da simulação não está em execução ou foi encerrado. Verifique se a simulação foi concluída e entrou no modo de espera de comandos."
            }), 400

        # Otimiza prompt, adiciona prefixo
        optimized_prompt = optimize_interview_prompt(prompt)

        result = SimulationRunner.interview_agent(
            simulation_id=simulation_id,
            agent_id=agent_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"Tempo limite excedido ao aguardar a resposta da entrevista: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"Falha no Interview: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/interview/batch', methods=['POST'])
def interview_agents_batch():
    """
    Entrevistar multiplos Agents em lote

    Nota: requer ambiente em execucao

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",       // obrigatorio, ID da simulacao
            "interviews": [                    // obrigatorio, lista de entrevistas
                {
                    "agent_id": 0,
                    "prompt": "Qual e a sua opiniao sobre A?",
                    "platform": "twitter"      // opcional, plataforma deste Agent
                },
                {
                    "agent_id": 1,
                    "prompt": "Qual e a sua opiniao sobre B?"  // sem platform usa padrao
                }
            ],
            "platform": "reddit",              // opcional, plataforma padrao (sobrescrita por cada item)
                                               // sem especificar: entrevista cada Agent em ambas
            "timeout": 120                     // opcional, timeout (segundos), padrao 120
        }

    Retorno:
        {
            "success": true,
            "data": {
                "interviews_count": 2,
                "result": {
                    "interviews_count": 4,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        "twitter_1": {"agent_id": 1, "response": "...", "platform": "twitter"},
                        "reddit_1": {"agent_id": 1, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        interviews = data.get('interviews')
        platform = data.get('platform')  # opcional: twitter/reddit/None
        timeout = data.get('timeout', 120)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        if not interviews or not isinstance(interviews, list):
            return jsonify({
                "success": False,
                "error": "Informe interviews (lista de entrevistas)"
            }), 400

        # Valida parametro platform
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "O parâmetro platform só pode ser 'twitter' ou 'reddit'"
            }), 400

        # Valida cada item de entrevista
        for i, interview in enumerate(interviews):
            if 'agent_id' not in interview:
                return jsonify({
                    "success": False,
                    "error": f"O item {i+1} da lista de entrevistas não possui agent_id"
                }), 400
            if 'prompt' not in interview:
                return jsonify({
                    "success": False,
                    "error": f"O item {i+1} da lista de entrevistas não possui prompt"
                }), 400
            # Valida platform de cada item
            item_platform = interview.get('platform')
            if item_platform and item_platform not in ("twitter", "reddit"):
                return jsonify({
                    "success": False,
                    "error": f"No item {i+1} da lista de entrevistas, platform só pode ser 'twitter' ou 'reddit'"
                }), 400

        # Verifica estado do ambiente
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "O ambiente da simulação não está em execução ou foi encerrado. Verifique se a simulação foi concluída e entrou no modo de espera de comandos."
            }), 400

        # Otimiza prompt de cada item
        optimized_interviews = []
        for interview in interviews:
            optimized_interview = interview.copy()
            optimized_interview['prompt'] = optimize_interview_prompt(interview.get('prompt', ''))
            optimized_interviews.append(optimized_interview)

        result = SimulationRunner.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=optimized_interviews,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"Tempo limite excedido ao aguardar a resposta da entrevista em lote: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"Falha no Interview em lote: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/interview/all', methods=['POST'])
def interview_all_agents():
    """
    Entrevista global - mesma pergunta para todos

    Nota: requer ambiente em execucao

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",            // obrigatorio, ID da simulacao
            "prompt": "Qual e a sua opiniao geral?",  // obrigatorio, pergunta (mesma para todos os Agents)
            "platform": "reddit",                   // opcional, especificar plataforma
                                                    // sem especificar: entrevista cada Agent em ambas
            "timeout": 180                          // opcional, timeout (segundos), padrao 180
        }

    Retorno:
        {
            "success": true,
            "data": {
                "interviews_count": 50,
                "result": {
                    "interviews_count": 100,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        ...
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # opcional: twitter/reddit/None
        timeout = data.get('timeout', 180)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        if not prompt:
            return jsonify({
                "success": False,
                "error": "Informe o prompt da entrevista"
            }), 400

        # Valida parametro platform
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "O parâmetro platform só pode ser 'twitter' ou 'reddit'"
            }), 400

        # Verifica estado do ambiente
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "O ambiente da simulação não está em execução ou foi encerrado. Verifique se a simulação foi concluída e entrou no modo de espera de comandos."
            }), 400

        # Otimiza prompt, adiciona prefixo
        optimized_prompt = optimize_interview_prompt(prompt)

        result = SimulationRunner.interview_all_agents(
            simulation_id=simulation_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"Tempo limite excedido ao aguardar a resposta da entrevista global: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"Falha no Interview global: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/interview/history', methods=['POST'])
def get_interview_history():
    """
    Obter historico de Interview

    Le registros do banco de dados

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",  // obrigatorio, ID da simulacao
            "platform": "reddit",          // opcional, tipo (reddit/twitter)
                                           // se nao especificado retorna historico de ambas
            "agent_id": 0,                 // opcional, apenas historico deste Agent
            "limit": 100                   // opcional, quantidade, padrao 100
        }

    Retorno:
        {
            "success": true,
            "data": {
                "count": 10,
                "history": [
                    {
                        "agent_id": 0,
                        "response": "Eu acredito que...",
                        "prompt": "Qual e a sua opiniao sobre este assunto?",
                        "timestamp": "2025-12-08T10:00:00",
                        "platform": "reddit"
                    },
                    ...
                ]
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        platform = data.get('platform')  # se nao especificado retorna historico de ambas
        agent_id = data.get('agent_id')
        limit = data.get('limit', 100)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        history = SimulationRunner.get_interview_history(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": {
                "count": len(history),
                "history": history
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter historico de Interview: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/env-status', methods=['POST'])
def get_env_status():
    """
    Obter estado do ambiente de simulacao

    Verifica se o ambiente esta ativo (pode receber comandos)

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx"  // obrigatorio, ID da simulacao
        }

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "env_alive": true,
                "twitter_available": true,
                "reddit_available": true,
                "message": "O ambiente está em execução e pode receber comandos de entrevista"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        env_alive = SimulationRunner.check_env_alive(simulation_id)

        # Obtem informacoes de estado mais detalhadas
        env_status = SimulationRunner.get_env_status_detail(simulation_id)

        if env_alive:
            message = "O ambiente está em execução e pode receber comandos de entrevista"
        else:
            message = "O ambiente não está em execução ou foi encerrado"

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "env_alive": env_alive,
                "twitter_available": env_status.get("twitter_available", False),
                "reddit_available": env_status.get("reddit_available", False),
                "message": message
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter estado do ambiente: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/close-env', methods=['POST'])
def close_simulation_env():
    """
    Fechar ambiente de simulacao

    Envia comando de fechamento, saindo do modo de espera.

    Nota: diferente de /stop que forca terminacao,
    esta interface permite fechamento elegante.

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",  // obrigatorio, ID da simulacao
            "timeout": 30                  // opcional, timeout (segundos), padrao 30
        }

    Retorno:
        {
            "success": true,
            "data": {
                "message": "O comando de encerramento do ambiente foi enviado",
                "result": {...},
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        timeout = data.get('timeout', 30)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        result = SimulationRunner.close_simulation_env(
            simulation_id=simulation_id,
            timeout=timeout
        )

        # Atualiza estado da simulacao
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.COMPLETED
            manager._save_simulation_state(state)

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        logger.error(f"Falha ao fechar ambiente: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
