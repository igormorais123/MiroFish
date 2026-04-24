"""API interna para integracao service-to-service com a INTEIA."""

from __future__ import annotations

import threading
import traceback
from functools import wraps

from flask import jsonify, request

from . import internal_bp
from ..config import Config
from ..models.project import ProjectManager, ProjectStatus
from ..models.task import TaskManager, TaskStatus
from ..services.graph_builder import GraphBuilderService
from ..services.ontology_generator import OntologyGenerator
from ..services.simulation_manager import SimulationManager, SimulationStatus
from ..services.simulation_runner import SimulationRunner
from ..services.text_processor import TextProcessor
from ..utils.logger import get_logger
from ..utils.token_tracker import TokenTracker

logger = get_logger('mirofish.api.internal')


def _unauthorized_response():
    return jsonify({
        "success": False,
        "error": "Nao autorizado para a API interna",
    }), 401


def _build_project_text(payload: dict) -> tuple[str, list[dict]]:
    """Normaliza materiais textuais enviados pela INTEIA."""
    materials = payload.get('materials') or []
    single_text = (payload.get('text') or '').strip()

    normalized_materials = []
    combined_parts = []

    if single_text:
        normalized_materials.append({
            "filename": "briefing.txt",
            "size": len(single_text.encode('utf-8')),
        })
        combined_parts.append("=== briefing.txt ===\n" + single_text)

    for index, material in enumerate(materials, start=1):
        text = (material.get('text') or '').strip()
        if not text:
            continue
        filename = (material.get('filename') or f"material_{index}.txt").strip()
        normalized_materials.append({
            "filename": filename,
            "size": len(text.encode('utf-8')),
        })
        combined_parts.append(f"=== {filename} ===\n{text}")

    return "\n\n".join(combined_parts).strip(), normalized_materials


def _normalize_structured_context(payload: dict) -> dict:
    """Extrai contexto estruturado relevante para cenarios INTEIA."""
    structured_context = payload.get('structured_context') or {}

    aliases = {
        "cenario": payload.get("cenario"),
        "territorio": payload.get("territorio"),
        "atores": payload.get("atores"),
        "segmentos": payload.get("segmentos"),
        "canais": payload.get("canais"),
        "hipoteses": payload.get("hipoteses"),
        "restricoes": payload.get("restricoes"),
        "objetivos_analiticos": payload.get("objetivos_analiticos"),
    }

    for key, value in aliases.items():
        if value:
            structured_context[key] = value

    return structured_context


def _render_structured_context(structured_context: dict) -> str:
    """Transforma contexto estruturado em texto legivel para ontologia e simulacao."""
    if not structured_context:
        return ""

    sections = ["## Contexto Estruturado INTEIA"]

    cenario = structured_context.get("cenario")
    if cenario:
        sections.append(f"### Cenario\n{cenario}")

    territorio = structured_context.get("territorio")
    if territorio:
        sections.append(f"### Territorio\n{territorio}")

    for list_key, title in (
        ("atores", "Atores"),
        ("segmentos", "Segmentos"),
        ("canais", "Canais"),
        ("hipoteses", "Hipoteses"),
        ("restricoes", "Restricoes"),
        ("objetivos_analiticos", "Objetivos Analiticos"),
    ):
        values = structured_context.get(list_key)
        if not values:
            continue
        if isinstance(values, list):
            content = "\n".join(f"- {item}" for item in values)
        else:
            content = str(values)
        sections.append(f"### {title}\n{content}")

    return "\n\n".join(sections).strip()


def _serialize_task(task):
    if not task:
        return None
    return task.to_dict()


def _infer_uf(project) -> str:
    structured_context = project.structured_context or {}
    territory = str(structured_context.get("territorio") or "").lower()
    mapping = {
        "roraima": "rr",
        "rr": "rr",
        "distrito federal": "df",
        "brasilia": "df",
        "df": "df",
    }
    return mapping.get(territory, "rr")


def _compute_lenia_signals(project, simulation_state=None) -> dict:
    structured_context = project.structured_context or {}
    actors = structured_context.get("atores") or []
    segments = structured_context.get("segmentos") or []
    channels = structured_context.get("canais") or []
    hypotheses = structured_context.get("hipoteses") or []

    complexity_score = min(100, 20 + len(actors) * 8 + len(segments) * 6 + len(channels) * 5)
    narrative_pressure = min(100, 15 + len(hypotheses) * 15 + len(channels) * 8)
    mobilization_score = min(100, 10 + len(actors) * 7 + len(channels) * 10)
    territorial_sensitivity = 85 if _infer_uf(project) == "rr" else 65

    if simulation_state:
        complexity_score = min(100, complexity_score + min(simulation_state.entities_count, 20))
        mobilization_score = min(100, mobilization_score + min(simulation_state.profiles_count // 2, 20))

    return {
        "complexity_score": complexity_score,
        "narrative_pressure": narrative_pressure,
        "mobilization_score": mobilization_score,
        "territorial_sensitivity": territorial_sensitivity,
    }


def _build_lenia_export(project, simulation_state=None) -> dict:
    structured_context = project.structured_context or {}
    signals = _compute_lenia_signals(project, simulation_state=simulation_state)

    return {
        "version": "1.0",
        "target_system": "lenia",
        "uf": _infer_uf(project),
        "territorio": structured_context.get("territorio") or "Roraima",
        "project_id": project.project_id,
        "simulation_id": simulation_state.simulation_id if simulation_state else None,
        "project_status": project.status.value if hasattr(project.status, "value") else project.status,
        "simulation_status": simulation_state.status.value if simulation_state else None,
        "simulation_requirement": project.simulation_requirement,
        "cenario": structured_context.get("cenario"),
        "atores": structured_context.get("atores") or [],
        "segmentos": structured_context.get("segmentos") or [],
        "canais": structured_context.get("canais") or [],
        "hipoteses": structured_context.get("hipoteses") or [],
        "restricoes": structured_context.get("restricoes") or [],
        "objetivos_analiticos": structured_context.get("objetivos_analiticos") or [],
        "signals": signals,
        "recommended_overlays": [
            "narrative_pressure",
            "mobilization_score",
            "territorial_sensitivity",
        ],
        "source_summary": {
            "total_text_length": project.total_text_length,
            "files_count": len(project.files or []),
            "entities_count": simulation_state.entities_count if simulation_state else None,
            "profiles_count": simulation_state.profiles_count if simulation_state else None,
        },
        "helena_prompt_hint": (
            "Ler o baseline do Lenia-RR em conjunto com pressao narrativa, atores-chave, "
            "segmentos sensiveis e hipoteses exportadas pelo MiroFish-Inteia."
        ),
    }


def _finalize_project_from_payload(project, payload: dict, final_text: str, materials: list[dict], structured_context: dict):
    """Gera ontologia e conclui a montagem do projeto."""
    project.simulation_requirement = (payload.get('simulation_requirement') or '').strip()
    project.structured_context = structured_context or None
    project.files = materials
    project.total_text_length = len(final_text)
    ProjectManager.save_extracted_text(project.project_id, final_text)
    ProjectManager.save_project(project)

    generator = OntologyGenerator()
    ontology = generator.generate(
        document_texts=[final_text],
        simulation_requirement=project.simulation_requirement,
        additional_context=payload.get('additional_context') or None,
    )

    project.ontology = {
        "entity_types": ontology.get("entity_types", []),
        "edge_types": ontology.get("edge_types", []),
    }
    project.analysis_summary = ontology.get("analysis_summary", "")
    project.status = ProjectStatus.ONTOLOGY_GENERATED
    ProjectManager.save_project(project)
    return project


def require_internal_token(view_func):
    """Valida o token interno enviado pela INTEIA."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        expected_token = Config.INTERNAL_API_TOKEN.strip()
        if not expected_token:
            logger.warning("INTERNAL_API_TOKEN nao configurado; acesso interno bloqueado")
            return _unauthorized_response()

        provided_token = request.headers.get('X-Internal-Token', '').strip()
        if provided_token != expected_token:
            logger.warning("Tentativa de acesso interno com token invalido")
            return _unauthorized_response()
        return view_func(*args, **kwargs)
    return wrapper


@internal_bp.route('/health', methods=['GET'])
@require_internal_token
def internal_health():
    """Healthcheck completo com dados de infra (exige token)."""
    return jsonify({
        "success": True,
        "data": {
            "service": Config.APP_NAME,
            "code": Config.APP_CODE,
            "llm_base_url": Config.LLM_BASE_URL,
            "llm_model": Config.LLM_MODEL_NAME,
            "graphiti_url": Config.GRAPHITI_BASE_URL,
        }
    })


@internal_bp.route('/health/public', methods=['GET'])
def internal_health_public():
    """Healthcheck publico — retorna apenas up/down, sem expor config.

    2026-04-18, Phase 7: criado para substituir usos de /health sem token
    (evita vazar LLM_BASE_URL/GRAPHITI_BASE_URL em monitoring externo).
    """
    return jsonify({"success": True, "status": "up"})


@internal_bp.route('/projects', methods=['POST'])
@require_internal_token
def create_internal_project():
    """Cria um projeto minimo para posterior ingestao de materiais."""
    try:
        payload = request.get_json() or {}
        project_name = payload.get('name', 'Projeto INTEIA')
        simulation_requirement = payload.get('simulation_requirement')

        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        ProjectManager.save_project(project)

        return jsonify({
            "success": True,
            "data": project.to_dict(),
        }), 201
    except Exception as exc:
        logger.error(f"Falha ao criar projeto interno: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@internal_bp.route('/projects/from-briefing', methods=['POST'])
@require_internal_token
def create_project_from_briefing():
    """Cria projeto interno a partir de briefing textual e gera ontologia."""
    try:
        payload = request.get_json() or {}
        simulation_requirement = (payload.get('simulation_requirement') or '').strip()
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Informe simulation_requirement",
            }), 400

        combined_text, materials = _build_project_text(payload)
        structured_context = _normalize_structured_context(payload)
        structured_text = _render_structured_context(structured_context)

        final_parts = [part for part in (structured_text, combined_text) if part]
        final_text = "\n\n".join(final_parts).strip()

        if not final_text:
            return jsonify({
                "success": False,
                "error": "Informe text, materials ou contexto estruturado com conteudo util",
            }), 400

        project = ProjectManager.create_project(name=payload.get('name', 'Projeto INTEIA'))
        async_mode = bool(payload.get('async') or payload.get('async_mode'))

        if async_mode:
            task_manager = TaskManager()
            task_id = task_manager.create_task(
                task_type="internal_project_briefing",
                metadata={"project_id": project.project_id, "name": project.name},
            )

            def run_project_generation():
                try:
                    task_manager.update_task(
                        task_id,
                        status=TaskStatus.PROCESSING,
                        progress=10,
                        message="Montando contexto do projeto",
                    )
                    task_manager.update_task(
                        task_id,
                        status=TaskStatus.PROCESSING,
                        progress=35,
                        message="Persistindo briefing estruturado",
                    )
                    _finalize_project_from_payload(
                        project=project,
                        payload=payload,
                        final_text=final_text,
                        materials=materials,
                        structured_context=structured_context,
                    )
                    task_manager.update_task(
                        task_id,
                        status=TaskStatus.COMPLETED,
                        progress=100,
                        message="Projeto estruturado concluido",
                        result=project.to_dict(),
                    )
                except Exception as exc:
                    logger.error(f"Falha ao gerar projeto estruturado: {exc}")
                    logger.error(traceback.format_exc())
                    task_manager.update_task(
                        task_id,
                        status=TaskStatus.FAILED,
                        message=f"Falha ao gerar projeto estruturado: {exc}",
                    )

            threading.Thread(target=run_project_generation, daemon=True).start()

            return jsonify({
                "success": True,
                "data": {
                    "project_id": project.project_id,
                    "task_id": task_id,
                    "status": "processing",
                    "input_mode": "briefing",
                    "has_structured_context": bool(structured_context),
                    "message": "Projeto estruturado em processamento",
                },
            }), 202

        project = _finalize_project_from_payload(
            project=project,
            payload=payload,
            final_text=final_text,
            materials=materials,
            structured_context=structured_context,
        )

        return jsonify({
            "success": True,
            "data": {
                **project.to_dict(),
                "input_mode": "briefing",
                "has_structured_context": bool(structured_context),
            },
        }), 201
    except Exception as exc:
        logger.error(f"Falha ao criar projeto por briefing: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@internal_bp.route('/projects/from-structured-briefing', methods=['POST'])
@require_internal_token
def create_project_from_structured_briefing():
    """Alias explicito para o fluxo estruturado da INTEIA."""
    return create_project_from_briefing()


@internal_bp.route('/projects/<project_id>', methods=['GET'])
@require_internal_token
def get_internal_project(project_id: str):
    """Retorna um projeto para consumo interno pela INTEIA."""
    project = ProjectManager.get_project(project_id)
    if not project:
        return jsonify({
            "success": False,
            "error": f"Projeto nao encontrado: {project_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict(),
    })


@internal_bp.route('/projects/<project_id>/lenia-export', methods=['GET'])
@require_internal_token
def export_project_to_lenia(project_id: str):
    """Exporta um projeto no formato de acoplamento inicial para o Lenia."""
    project = ProjectManager.get_project(project_id)
    if not project:
        return jsonify({
            "success": False,
            "error": f"Projeto nao encontrado: {project_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": _build_lenia_export(project),
    })


@internal_bp.route('/projects/<project_id>/graph/build', methods=['POST'])
@require_internal_token
def build_internal_graph(project_id: str):
    """Dispara a construcao do grafo para um projeto interno."""
    try:
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto nao encontrado: {project_id}",
            }), 404

        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": "Projeto ainda sem ontologia gerada",
            }), 400

        payload = request.get_json() or {}
        force = payload.get('force', False)
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": "O grafo ja esta em construcao",
                "task_id": project.graph_build_task_id,
            }), 400

        if force and project.status in (
            ProjectStatus.GRAPH_BUILDING,
            ProjectStatus.GRAPH_COMPLETED,
            ProjectStatus.FAILED,
        ):
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None

        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({
                "success": False,
                "error": "Texto extraido nao encontrado para o projeto",
            }), 400

        if not project.ontology:
            return jsonify({
                "success": False,
                "error": "Ontologia nao encontrada no projeto",
            }), 400

        graph_name = payload.get('graph_name', project.name or 'MiroFish-Inteia Graph')
        chunk_size = payload.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = payload.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="internal_graph_build",
            metadata={"project_id": project_id, "graph_name": graph_name},
        )

        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        ProjectManager.save_project(project)

        def build_task():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=5,
                    message="Inicializando a construcao do grafo",
                )
                builder = GraphBuilderService()

                chunks = TextProcessor.split_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
                task_manager.update_task(
                    task_id,
                    progress=10,
                    message=f"Texto dividido em {len(chunks)} blocos",
                )

                graph_id = builder.create_graph(name=graph_name)
                project.graph_id = graph_id
                ProjectManager.save_project(project)

                if not builder.client.healthcheck():
                    raise RuntimeError(
                        "Graphiti indisponivel ou endpoint de health incompatível."
                    )

                task_manager.update_task(
                    task_id,
                    progress=18,
                    message="Ontologia sendo aplicada ao grafo",
                )
                builder.set_ontology(graph_id, project.ontology)

                def add_progress_callback(message, progress_ratio):
                    task_manager.update_task(
                        task_id,
                        progress=18 + int(progress_ratio * 42),
                        message=message,
                    )

                builder.add_text_batches(
                    graph_id,
                    chunks,
                    batch_size=3,
                    progress_callback=add_progress_callback,
                )

                task_manager.update_task(
                    task_id,
                    progress=60,
                    message="Aguardando processamento do Graphiti",
                )

                def wait_progress_callback(message, progress_ratio):
                    task_manager.update_task(
                        task_id,
                        progress=60 + int(progress_ratio * 30),
                        message=message,
                    )

                graph_data = builder.wait_for_graph_materialization(
                    graph_id,
                    expected_count=len(chunks),
                    progress_callback=wait_progress_callback,
                    timeout=120,
                    stall_timeout=30,
                )

                project.status = ProjectStatus.GRAPH_COMPLETED
                project.error = None
                ProjectManager.save_project(project)

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="Construcao do grafo concluida",
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": graph_data.get("node_count", 0),
                        "edge_count": graph_data.get("edge_count", 0),
                    },
                )
            except Exception as exc:
                logger.error(f"Falha na construcao do grafo: {exc}")
                logger.error(traceback.format_exc())
                project.status = ProjectStatus.FAILED
                project.error = str(exc)
                ProjectManager.save_project(project)
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Falha na construcao do grafo: {exc}",
                )

        threading.Thread(target=build_task, daemon=True).start()

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "status": "processing",
                "message": "Construcao do grafo iniciada",
            },
        }), 202
    except Exception as exc:
        logger.error(f"Falha ao iniciar construcao interna do grafo: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@internal_bp.route('/projects/<project_id>/simulation', methods=['POST'])
@require_internal_token
def create_internal_simulation(project_id: str):
    """Cria uma simulacao vinculada a um projeto existente."""
    try:
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto nao encontrado: {project_id}",
            }), 404

        payload = request.get_json() or {}
        graph_id = payload.get('graph_id') or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Projeto ainda sem grafo associado",
            }), 400

        manager = SimulationManager()
        state = manager.create_simulation(
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=payload.get('enable_twitter', True),
            enable_reddit=payload.get('enable_reddit', True),
        )

        return jsonify({
            "success": True,
            "data": state.to_dict(),
        }), 201
    except Exception as exc:
        logger.error(f"Falha ao criar simulacao interna: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@internal_bp.route('/simulations/<simulation_id>/prepare', methods=['POST'])
@require_internal_token
def prepare_internal_simulation(simulation_id: str):
    """Dispara a preparacao da simulacao para consumo interno."""
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulacao nao encontrada: {simulation_id}",
            }), 404

        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto nao encontrado: {state.project_id}",
            }), 404

        simulation_requirement = (project.simulation_requirement or '').strip()
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Projeto sem simulation_requirement",
            }), 400

        document_text = ProjectManager.get_extracted_text(state.project_id) or ""
        payload = request.get_json() or {}
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="internal_simulation_prepare",
            metadata={"simulation_id": simulation_id, "project_id": state.project_id},
        )

        state.status = SimulationStatus.PREPARING
        manager._save_simulation_state(state)

        def run_prepare():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="Iniciando preparacao da simulacao",
                )

                def progress_callback(stage, progress, message, **details):
                    stage_weights = {
                        "reading": 20,
                        "generating_profiles": 65,
                        "generating_config": 15,
                    }
                    stage_offsets = {
                        "reading": 0,
                        "generating_profiles": 20,
                        "generating_config": 85,
                    }
                    total_progress = stage_offsets.get(stage, 0) + int(
                        progress * stage_weights.get(stage, 0) / 100
                    )
                    task_manager.update_task(
                        task_id,
                        progress=min(total_progress, 99),
                        message=message,
                        progress_detail={
                            "stage": stage,
                            "stage_progress": progress,
                            **details,
                        },
                    )

                result_state = manager.prepare_simulation(
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    document_text=document_text,
                    defined_entity_types=payload.get('entity_types'),
                    use_llm_for_profiles=payload.get('use_llm_for_profiles', True),
                    progress_callback=progress_callback,
                    parallel_profile_count=payload.get('parallel_profile_count', 5),
                )

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="Preparacao da simulacao concluida",
                    result=result_state.to_dict(),
                )
            except Exception as exc:
                logger.error(f"Falha na preparacao da simulacao: {exc}")
                logger.error(traceback.format_exc())
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Falha na preparacao: {exc}",
                )

        threading.Thread(target=run_prepare, daemon=True).start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "task_id": task_id,
                "status": "processing",
                "message": "Preparacao da simulacao iniciada",
            },
        }), 202
    except Exception as exc:
        logger.error(f"Falha ao iniciar preparacao interna da simulacao: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@internal_bp.route('/simulations/<simulation_id>/start', methods=['POST'])
@require_internal_token
def start_internal_simulation(simulation_id: str):
    """Inicia a simulacao ja preparada."""
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulacao nao encontrada: {simulation_id}",
            }), 404

        payload = request.get_json() or {}
        run_state = SimulationRunner.start_simulation(
            simulation_id=simulation_id,
            platform=payload.get('platform', 'parallel'),
            max_rounds=payload.get('max_rounds'),
            enable_graph_memory_update=payload.get('enable_graph_memory_update', False),
            graph_id=payload.get('graph_id') or state.graph_id,
        )

        state.status = SimulationStatus.RUNNING
        manager._save_simulation_state(state)

        return jsonify({
            "success": True,
            "data": run_state.to_detail_dict(),
        }), 202
    except ValueError as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 400
    except Exception as exc:
        logger.error(f"Falha ao iniciar simulacao interna: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@internal_bp.route('/simulations/<simulation_id>', methods=['GET'])
@require_internal_token
def get_internal_simulation(simulation_id: str):
    """Consulta o estado resumido de uma simulacao."""
    manager = SimulationManager()
    state = manager.get_simulation(simulation_id)
    if not state:
        return jsonify({
            "success": False,
            "error": f"Simulacao nao encontrada: {simulation_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": state.to_dict(),
    })


@internal_bp.route('/simulations/<simulation_id>/lenia-export', methods=['GET'])
@require_internal_token
def export_simulation_to_lenia(simulation_id: str):
    """Exporta uma simulacao no formato de acoplamento inicial para o Lenia."""
    manager = SimulationManager()
    state = manager.get_simulation(simulation_id)
    if not state:
        return jsonify({
            "success": False,
            "error": f"Simulacao nao encontrada: {simulation_id}",
        }), 404

    project = ProjectManager.get_project(state.project_id)
    if not project:
        return jsonify({
            "success": False,
            "error": f"Projeto nao encontrado: {state.project_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": _build_lenia_export(project, simulation_state=state),
    })


@internal_bp.route('/simulations/<simulation_id>/run-status', methods=['GET'])
@require_internal_token
def get_internal_run_status(simulation_id: str):
    """Consulta o estado do runner da simulacao."""
    run_state = SimulationRunner.get_run_state(simulation_id)
    if not run_state:
        return jsonify({
            "success": False,
            "error": f"Estado de execucao nao encontrado: {simulation_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": run_state.to_detail_dict(),
    })


@internal_bp.route('/tasks/<task_id>', methods=['GET'])
@require_internal_token
def get_internal_task(task_id: str):
    """Consulta o estado de tasks internas."""
    task = TaskManager().get_task(task_id)
    if not task:
        return jsonify({
            "success": False,
            "error": f"Task nao encontrada: {task_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": _serialize_task(task),
    })


@internal_bp.route('/run-preset', methods=['POST'])
@require_internal_token
def run_preset():
    """Executa pipeline Mirofish completo em uma chamada.

    Payload:
        {
            "name": "Simulacao X",
            "simulation_requirement": "descricao...",
            "materials": [{"filename": "x.md", "text": "..."}, ...],
            "structured_context": {...},            # opcional
            "preset": "vida-pessoal|eleitoral|mercado",   # opcional, define max_rounds
            "max_rounds": 50,                       # opcional, override
            "enable_twitter": true,
            "enable_reddit": true
        }

    Retorna task_id para polling via /api/internal/v1/tasks/<task_id>.
    Quando a task completa, result inclui {project_id, simulation_id, report_id}.
    """
    try:
        payload = request.get_json() or {}

        presets = {
            "vida-pessoal": {"max_rounds": 50, "parallel_profile_count": 5},
            "eleitoral": {"max_rounds": 200, "parallel_profile_count": 10},
            "mercado": {"max_rounds": 100, "parallel_profile_count": 8},
            "smoke": {"max_rounds": 10, "parallel_profile_count": 5},
        }
        preset_cfg = presets.get(payload.get("preset") or "smoke", presets["smoke"])
        max_rounds = int(payload.get("max_rounds") or preset_cfg["max_rounds"])
        parallel_profile_count = int(payload.get("parallel_profile_count") or preset_cfg["parallel_profile_count"])
        enable_twitter = bool(payload.get("enable_twitter", True))
        enable_reddit = bool(payload.get("enable_reddit", True))

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="mirofish_run_preset",
            metadata={"preset": payload.get("preset", "smoke"), "max_rounds": max_rounds},
        )

        def run_pipeline():
            try:
                import time as _t
                task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=2, message="Criando projeto...")

                # 1. Projeto + ontologia (sync)
                project = ProjectManager.create_project(name=payload.get("name", "Projeto Mirofish"))
                combined, materials = _build_project_text(payload)
                structured = _normalize_structured_context(payload)
                structured_text = _render_structured_context(structured)
                final_text = "\n\n".join(p for p in (structured_text, combined) if p).strip()
                if not final_text:
                    raise ValueError("Sem conteudo textual em materials/structured_context")
                project = _finalize_project_from_payload(project, payload, final_text, materials, structured)
                task_manager.update_task(task_id, progress=18, message=f"Ontologia gerada: {project.project_id}")

                # 2. Graph build
                from ..services.graph_builder import GraphBuilderService
                from ..services.text_processor import TextProcessor
                builder = GraphBuilderService()
                text = ProjectManager.get_extracted_text(project.project_id)
                chunks = TextProcessor.split_text(text, chunk_size=project.chunk_size or Config.DEFAULT_CHUNK_SIZE,
                                                  overlap=project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)
                graph_id = builder.create_graph(name=project.name or "Mirofish Graph")
                project.graph_id = graph_id
                ProjectManager.save_project(project)
                builder.set_ontology(graph_id, project.ontology)
                builder.add_text_batches(graph_id, chunks, batch_size=3)
                try:
                    builder.wait_for_graph_materialization(graph_id, expected_count=len(chunks), timeout=180, stall_timeout=45)
                except Exception as e:
                    logger.warning(f"Grafo materializou parcialmente: {e}")
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)
                task_manager.update_task(task_id, progress=45, message=f"Grafo pronto: {graph_id}")

                # 3. Simulacao
                manager = SimulationManager()
                state = manager.create_simulation(project_id=project.project_id, graph_id=graph_id,
                                                  enable_twitter=enable_twitter, enable_reddit=enable_reddit)
                task_manager.update_task(task_id, progress=55, message=f"Simulacao criada: {state.simulation_id}")

                # 4. Prepare (gera perfis)
                manager.prepare_simulation(
                    simulation_id=state.simulation_id,
                    simulation_requirement=project.simulation_requirement,
                    document_text=text,
                    use_llm_for_profiles=True,
                    parallel_profile_count=parallel_profile_count,
                )
                task_manager.update_task(task_id, progress=70, message="Perfis gerados")

                # 5. Start + wait
                SimulationRunner.start_simulation(
                    simulation_id=state.simulation_id,
                    platform="parallel",
                    max_rounds=max_rounds,
                    enable_graph_memory_update=False,
                    graph_id=graph_id,
                )
                deadline = _t.time() + 3600
                while _t.time() < deadline:
                    rs = SimulationRunner.get_run_state(state.simulation_id)
                    if rs and rs.to_detail_dict().get("runner_status") in ("completed", "failed", "stopped"):
                        break
                    _t.sleep(10)
                task_manager.update_task(task_id, progress=85, message="Simulacao concluida, gerando relatorio...")

                # 6. Relatorio
                import uuid
                from ..services.report_agent import ReportAgent, ReportManager
                report_id = f"report_{uuid.uuid4().hex[:12]}"
                agent = ReportAgent(graph_id=graph_id, simulation_id=state.simulation_id,
                                    simulation_requirement=project.simulation_requirement)
                report = agent.generate_report(report_id=report_id)
                ReportManager.save_report(report)

                task_manager.update_task(
                    task_id, status=TaskStatus.COMPLETED, progress=100,
                    message="Pipeline Mirofish concluido",
                    result={
                        "project_id": project.project_id,
                        "graph_id": graph_id,
                        "simulation_id": state.simulation_id,
                        "report_id": report_id,
                        "report_url": f"/api/report/{report_id}",
                    },
                )
            except Exception as exc:
                logger.error(f"Falha run-preset: {exc}")
                logger.error(traceback.format_exc())
                task_manager.update_task(task_id, status=TaskStatus.FAILED, message=f"Falha: {exc}")

        threading.Thread(target=run_pipeline, daemon=True).start()
        return jsonify({"success": True, "data": {"task_id": task_id, "status": "processing"}}), 202
    except Exception as exc:
        logger.error(f"Falha run-preset: {exc}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(exc)}), 500


@internal_bp.route('/token-usage', methods=['GET'])
@require_internal_token
def get_token_usage():
    """Retorna consumo de tokens e custo acumulado (global e por sessao)."""
    tracker = TokenTracker()
    session_id = request.args.get('session_id')

    data = {"global": tracker.get_global()}

    if session_id:
        data["session"] = tracker.get_session(session_id)
    else:
        data["sessions"] = tracker.get_all_sessions()

    return jsonify({
        "success": True,
        "data": data,
    })
