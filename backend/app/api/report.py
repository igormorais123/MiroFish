"""
Rotas de API de relatorios
Fornece interfaces para geracao, obtencao e conversa sobre relatorios de simulacao
"""

import os
import traceback
import threading
from flask import request, jsonify, send_file

from . import report_bp
from ..config import Config
from ..services.mission_bundle import MissionBundle
from ..services.mission_selection import MissionSelection
from ..services.power_catalog import PowerCatalog
from ..services.power_persona_catalog import PowerPersonaCatalog
from ..services.forecast_ledger import ForecastLedger
from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.report_delivery_packet import build_report_delivery_packet
from ..services.executive_package import (
    ExecutivePackageConflict,
    ExecutivePackageInvalidPath,
    ExecutivePackageNotFound,
    allowed_executive_package_file_path,
    build_executive_package,
)
from ..services.report_bundle_verifier import (
    ReportBundleVerificationNotFound,
    verify_report_export_bundle,
)
from ..services.report_exporter import (
    ReportExportConflict,
    ReportExportInvalidPath,
    ReportExportNotFound,
    allowed_export_file_path,
    create_report_export,
    list_report_exports,
)
from ..services.report_finalization import (
    ReportFinalizationConflict,
    ReportFinalizationNotFound,
    repair_report_finalization,
)
from ..services.simulation_manager import SimulationManager
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.report')


POWER_PERSONA_CATALOG_LIMIT = 100
POWER_PERSONA_CONTEXT_LIMIT = 4000


def _safe_limit(value, default=POWER_PERSONA_CATALOG_LIMIT, maximum=POWER_PERSONA_CATALOG_LIMIT):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(limit, maximum))


def _build_power_persona_catalog():
    return PowerPersonaCatalog(max_files=PowerPersonaCatalog.DEFAULT_MAX_FILES).build_catalog()


def _filter_power_persona_catalog(catalog, tipo=None, q=None, limit=POWER_PERSONA_CATALOG_LIMIT):
    query = (q or "").strip().lower()
    filtered = []
    for item in catalog:
        if tipo and item.get("tipo") != tipo:
            continue
        if query:
            haystack = " ".join(
                str(item.get(key, ""))
                for key in ("id", "nome", "tipo", "fonte", "origem", "resumo")
            ).lower()
            if query not in haystack:
                continue
        filtered.append(item)
        if len(filtered) >= limit:
            break
    return filtered


def _extract_power_persona_ids(value):
    if not isinstance(value, list):
        return []
    ids = []
    for item in value:
        if isinstance(item, dict):
            item_id = item.get("id")
        else:
            item_id = item
        if item_id is not None:
            ids.append(str(item_id))
    return ids


def _build_power_persona_context_from_payload(data):
    selected_ids = []
    selected_ids.extend(_extract_power_persona_ids(data.get("selected_power_persona_ids")))
    selected_ids.extend(_extract_power_persona_ids(data.get("selected_personas")))
    selected_ids.extend(_extract_power_persona_ids(data.get("selected_ids")))

    seen = set()
    selected_ids = [item_id for item_id in selected_ids if not (item_id in seen or seen.add(item_id))]
    if not selected_ids:
        return "", {"selected_ids": [], "items": [], "count": 0, "preview": ""}

    tipo = data.get("tipo")
    builder = PowerPersonaCatalog(max_files=PowerPersonaCatalog.DEFAULT_MAX_FILES)
    catalog = builder.build_catalog()
    selected_items = builder.select_items(catalog, selected_ids, tipo=tipo)
    context = builder.build_context_pack(selected_items, max_chars=POWER_PERSONA_CONTEXT_LIMIT)
    preview = context[:500] + "..." if len(context) > 500 else context
    metadata = {
        "selected_ids": selected_ids,
        "tipo": tipo,
        "count": len(selected_items),
        "items": [
            {
                "id": item.get("id"),
                "nome": item.get("nome"),
                "tipo": item.get("tipo"),
                "fonte": item.get("fonte"),
                "origem": item.get("origem"),
                "resumo_preview": (item.get("resumo") or "")[:240],
            }
            for item in selected_items
        ],
        "preview": preview,
    }
    return context, metadata


def _merge_saved_mission_selection(simulation_id, data):
    merged = dict(data or {})
    saved = MissionSelection().load(simulation_id)
    if not merged.get("selected_power_ids") and not merged.get("selected_powers"):
        saved_power_ids = saved.get("selected_power_ids") or []
        if saved_power_ids:
            merged["selected_power_ids"] = saved_power_ids
    if not merged.get("selected_power_persona_ids") and not merged.get("selected_personas"):
        saved_persona_ids = saved.get("selected_power_persona_ids") or []
        if saved_persona_ids:
            merged["selected_power_persona_ids"] = saved_persona_ids
    return merged


def _extract_power_ids(data):
    selected_ids = []
    selected_ids.extend(_extract_power_persona_ids(data.get("selected_power_ids")))
    selected_ids.extend(_extract_power_persona_ids(data.get("selected_powers")))
    seen = set()
    return [item_id for item_id in selected_ids if not (item_id in seen or seen.add(item_id))]


def _build_power_selection_from_payload(data):
    selected_ids = _extract_power_ids(data)
    base_tokens = data.get("base_tokens", 0)
    base_value_brl = data.get("base_value_brl", 0)
    estimate = PowerCatalog().estimate_selection(
        selected_ids,
        base_tokens=base_tokens,
        base_value_brl=base_value_brl,
    )
    return {
        "selected_ids": selected_ids,
        **estimate,
    }


def _enrich_forecast_ledger_payload(payload):
    """Completa artefatos antigos de forecast com calibracao e chart_data."""
    if not isinstance(payload, dict):
        return payload
    forecasts = payload.get("previsoes") or []
    normalized_forecasts = []
    for forecast in forecasts:
        if not isinstance(forecast, dict):
            continue
        normalized_forecasts.append({
            "enunciado": forecast.get("enunciado") or forecast.get("titulo") or "Previsao sem enunciado",
            "janela": forecast.get("janela") or "janela nao informada",
            "base": forecast.get("base") or forecast.get("fonte") or {},
            "sinais": forecast.get("sinais") or forecast.get("indicadores") or [],
            "grau_confianca_operacional": forecast.get("grau_confianca_operacional"),
            "status": forecast.get("status") or "congelada",
            "criado_em": forecast.get("criado_em"),
            "id": forecast.get("id"),
            "probability": forecast.get("probability"),
            "prior": forecast.get("prior"),
            "base_rate": forecast.get("base_rate"),
            "reference_class": forecast.get("reference_class"),
            "indicators": forecast.get("indicators"),
            "resolution_source": forecast.get("resolution_source"),
            "resolved_at": forecast.get("resolved_at"),
            "outcome": forecast.get("outcome"),
        })
    ledger = ForecastLedger()
    skipped_forecasts = 0
    for forecast in normalized_forecasts:
        try:
            ledger.registrar_previsao(**forecast)
        except (TypeError, ValueError):
            skipped_forecasts += 1
    enriched = dict(payload)
    enriched.setdefault("resumo", ledger.exportar_resumo())
    enriched.setdefault("calibracao", ledger.exportar_calibracao())
    enriched.setdefault("chart_data", ledger.exportar_grafico_deterministico())
    if skipped_forecasts:
        enriched["forecast_warnings"] = {
            "skipped_invalid_forecasts": skipped_forecasts,
        }
    return enriched


@report_bp.route('/power-catalog', methods=['GET'])
def get_power_catalog():
    """Expor poderes formais da missao."""
    try:
        categoria = request.args.get('categoria')
        tipo = request.args.get('tipo')
        powers = PowerCatalog().list_powers(tipo=tipo, categoria=categoria)
        return jsonify({
            "success": True,
            "data": {
                "items": powers,
                "count": len(powers),
            }
        })
    except Exception as e:
        logger.error(f"Falha ao listar poderes da missao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/power-estimate', methods=['POST'])
def estimate_powers():
    """Estimar impacto comercial dos poderes selecionados."""
    try:
        data = request.get_json() or {}
        return jsonify({
            "success": True,
            "data": _build_power_selection_from_payload(data),
        })
    except Exception as e:
        logger.error(f"Falha ao estimar poderes da missao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/power-persona-catalog', methods=['GET'])
def get_power_persona_catalog():
    """Expor catalogo seguro de poderes e personas externas."""
    try:
        tipo = request.args.get('tipo')
        q = request.args.get('q')
        limit = _safe_limit(request.args.get('limit'))
        catalog = _build_power_persona_catalog()
        items = _filter_power_persona_catalog(catalog, tipo=tipo, q=q, limit=limit)

        return jsonify({
            "success": True,
            "data": {
                "items": items,
                "count": len(items),
            }
        })

    except Exception as e:
        logger.error(f"Falha ao listar catalogo de poderes/personas: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/power-persona-context', methods=['POST'])
def build_power_persona_context():
    """Montar pacote de contexto em portugues para itens selecionados."""
    try:
        data = request.get_json() or {}
        context, metadata = _build_power_persona_context_from_payload(data)

        return jsonify({
            "success": True,
            "data": {
                "context": context,
                **metadata,
            }
        })

    except Exception as e:
        logger.error(f"Falha ao montar contexto de poderes/personas: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de geracao de relatorio ==============

@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    Gerar relatorio de analise da simulacao (tarefa assincrona)

    Esta e uma operacao demorada; a interface retorna imediatamente o task_id.
    Use GET /api/report/generate/status para consultar o progresso.

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",    // Obrigatorio, ID da simulacao
            "force_regenerate": false        // Opcional, forcar regeneracao
        }

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",
                "status": "generating",
                "message": "A tarefa de geração do relatório foi iniciada"
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

        data = _merge_saved_mission_selection(simulation_id, data)
        force_regenerate = data.get('force_regenerate', False)
        delivery_mode = data.get('delivery_mode')
        power_persona_context, power_persona_selection = _build_power_persona_context_from_payload(data)
        power_selection = _build_power_selection_from_payload(data)

        # Obter informacoes da simulacao
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        # Verificar se ja existe relatorio
        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "message": "O relatório já existe",
                        "already_generated": True
                    }
                })

        # Obter informacoes do projeto
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto não encontrado: {state.project_id}"
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "ID do grafo ausente. Verifique se o grafo já foi construído."
            }), 400

        simulation_requirement = project.simulation_requirement
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Descrição do objetivo da simulação ausente"
            }), 400

        # Gate estrutural: evita iniciar tarefa de relatorio quando a simulacao
        # ainda nao tem evidencias suficientes para sustentar conclusoes.
        source_text = None
        try:
            source_text = ProjectManager.get_extracted_text(state.project_id)
        except Exception:
            pass

        from ..services.report_system_gate import evaluate_report_system_gate

        gate_result = evaluate_report_system_gate(
            simulation_id=simulation_id,
            graph_id=graph_id,
            source_text=source_text,
            delivery_mode=delivery_mode,
        )
        if not gate_result.passes_gate:
            return jsonify({
                "success": False,
                "error": "Relatório bloqueado pelo gate estrutural INTEIA",
                "data": gate_result.to_dict(),
            }), 409

        # Gerar report_id antecipadamente para retornar ao frontend imediatamente
        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"

        # Criar tarefa assincrona
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="report_generate",
            metadata={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "report_id": report_id,
                "delivery_mode": gate_result.metrics.get("delivery_mode"),
            }
        )

        # Definir tarefa em segundo plano
        def run_generate():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="Inicializando o agente de relatório..."
                )

                # Criar Report Agent
                agent = ReportAgent(
                    graph_id=graph_id,
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    power_persona_context=power_persona_context,
                    power_persona_selection=power_persona_selection,
                    power_selection=power_selection,
                )

                # Callback de progresso
                def progress_callback(stage, progress, message):
                    task_manager.update_task(
                        task_id,
                        progress=progress,
                        message=f"[{stage}] {message}"
                    )

                # Gerar relatorio (passando o report_id pre-gerado)
                report = agent.generate_report(
                    progress_callback=progress_callback,
                    report_id=report_id,
                    source_text=source_text,
                    delivery_mode=delivery_mode,
                )

                # Salvar relatorio
                ReportManager.save_report(report)

                if report.status == ReportStatus.COMPLETED:
                    task_manager.complete_task(
                        task_id,
                        result={
                            "report_id": report.report_id,
                            "simulation_id": simulation_id,
                            "status": "completed"
                        }
                    )
                else:
                    task_manager.fail_task(task_id, report.error or "Falha na geração do relatório")

            except Exception as e:
                logger.error(f"Falha na geracao do relatorio: {str(e)}")
                logger.error(traceback.format_exc())
                task_manager.fail_task(task_id, str(e))

        # Iniciar thread em segundo plano
        thread = threading.Thread(target=run_generate, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "report_id": report_id,
                "task_id": task_id,
                "status": "generating",
                "message": "A tarefa de geração do relatório foi iniciada. Consulte o progresso em /api/report/generate/status",
                "already_generated": False
            }
        })

    except Exception as e:
        logger.error(f"Falha ao iniciar tarefa de geracao de relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/generate/status', methods=['POST'])
def get_generate_status():
    """
    Consultar progresso da tarefa de geracao de relatorio

    Requisicao (JSON):
        {
            "task_id": "task_xxxx",         // Opcional, task_id retornado pelo generate
            "simulation_id": "sim_xxxx"     // Opcional, ID da simulacao
        }

    Retorno:
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|failed",
                "progress": 45,
                "message": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')

        # Se simulation_id foi fornecido, verificar se ja existe relatorio concluido
        if simulation_id:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "progress": 100,
                        "message": "Relatório já gerado",
                        "already_completed": True
                    }
                })

        if not task_id:
            return jsonify({
                "success": False,
                "error": "Informe task_id ou simulation_id"
            }), 400

        task_manager = TaskManager()
        task = task_manager.get_task(task_id)

        if not task:
            return jsonify({
                "success": False,
                "error": f"Tarefa não encontrada: {task_id}"
            }), 404

        return jsonify({
            "success": True,
            "data": task.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha ao consultar estado da tarefa: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de obtencao de relatorio ==============

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """
    Obter detalhes do relatorio

    Retorno:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "simulation_id": "sim_xxxx",
                "status": "completed",
                "outline": {...},
                "markdown_content": "...",
                "created_at": "...",
                "completed_at": "..."
            }
        }
    """
    try:
        report = ReportManager.get_report(report_id)

        if not report:
            return jsonify({
                "success": False,
                "error": f"Relatório não encontrado: {report_id}"
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha ao obter relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/by-simulation/<simulation_id>', methods=['GET'])
def get_report_by_simulation(simulation_id: str):
    """
    Obter relatorio pelo ID da simulacao

    Retorno:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                ...
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        if not report:
            return jsonify({
                "success": False,
                "error": f"Esta simulação ainda não possui relatório: {simulation_id}",
                "has_report": False
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })

    except Exception as e:
        logger.error(f"Falha ao obter relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """
    Listar todos os relatorios

    Parametros de query:
        simulation_id: Filtrar por ID de simulacao (opcional)
        limit: Limite de quantidade retornada (padrao 50)

    Retorno:
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    """
    try:
        simulation_id = request.args.get('simulation_id')
        limit = request.args.get('limit', 50, type=int)

        reports = ReportManager.list_reports(
            simulation_id=simulation_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports)
        })

    except Exception as e:
        logger.error(f"Falha ao listar relatorios: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/artifacts', methods=['GET'])
def list_report_artifacts(report_id: str):
    """Listar artefatos de gate, manifesto e auditoria do relatorio."""
    try:
        report = ReportManager.get_report(report_id)
        if not report:
            return jsonify({
                "success": False,
                "error": f"Relatório não encontrado: {report_id}"
            }), 404

        include_content = request.args.get('include_content', 'false').lower() == 'true'
        artifacts = ReportManager.list_json_artifacts(report_id)

        if include_content:
            for artifact in artifacts:
                artifact["content"] = ReportManager.load_json_artifact(report_id, artifact["name"])

        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "simulation_id": report.simulation_id,
                "artifacts": artifacts,
            }
        })

    except Exception as e:
        logger.error(f"Falha ao listar artefatos do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/delivery-package', methods=['GET'])
def get_report_delivery_package(report_id: str):
    """Obter pacote consolidado de entregabilidade do relatorio."""
    try:
        packet = build_report_delivery_packet(report_id)
        status_code = 404 if packet.get("status") == "missing" else 200
        return jsonify({
            "success": status_code == 200,
            "data": packet,
        }), status_code
    except Exception as e:
        logger.error(f"Falha ao obter delivery package: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@report_bp.route('/<report_id>/executive-package', methods=['POST'])
def create_executive_package_route(report_id: str):
    """Criar pacote executivo apenas para relatorio publicavel."""
    try:
        manifest = build_executive_package(report_id)
        return jsonify({
            "success": True,
            "data": manifest,
        }), 200
    except ExecutivePackageNotFound as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except ExecutivePackageConflict as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        logger.error(f"Falha ao criar pacote executivo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/executive-package/<filename>', methods=['GET'])
def download_executive_package_file_route(report_id: str, filename: str):
    """Baixar apenas arquivos allowlisted no manifesto do pacote executivo."""
    try:
        path = allowed_executive_package_file_path(report_id, filename)
        return send_file(
            path,
            as_attachment=True,
            download_name=path.name,
            mimetype='application/json' if path.suffix == '.json' else 'text/html',
        )
    except ExecutivePackageNotFound as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ExecutivePackageInvalidPath as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Falha ao baixar arquivo do pacote executivo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/exports', methods=['POST'])
def create_report_export_route(report_id: str):
    """Criar rascunho de export verificavel para um relatorio."""
    try:
        export_manifest = create_report_export(report_id)
        return jsonify({
            "success": True,
            "data": export_manifest,
        }), 201
    except ReportExportNotFound as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ReportExportConflict as e:
        return jsonify({"success": False, "error": str(e)}), 409
    except Exception as e:
        logger.error(f"Falha ao criar export do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/exports', methods=['GET'])
def list_report_exports_route(report_id: str):
    """Listar exports existentes sem expor caminhos internos."""
    try:
        exports = list_report_exports(report_id)
        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "exports": exports,
            },
        }), 200
    except ReportExportNotFound as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"Falha ao listar exports do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/exports/<export_id>/bundle/verify', methods=['POST'])
def verify_report_export_bundle_route(report_id: str, export_id: str):
    """Verificar integridade e seguranca do bundle exportado."""
    try:
        verification = verify_report_export_bundle(report_id, export_id)
        return jsonify({
            "success": verification.get("passes") is True,
            "data": verification,
        }), 200
    except ReportBundleVerificationNotFound as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"Falha ao verificar bundle do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/exports/<export_id>/<filename>', methods=['GET'])
def download_report_export_file_route(report_id: str, export_id: str, filename: str):
    """Baixar apenas arquivos allowlisted no manifest do export."""
    try:
        path = allowed_export_file_path(report_id, export_id, filename)
        return send_file(
            path,
            as_attachment=True,
            download_name=filename,
        )
    except ReportExportNotFound as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ReportExportInvalidPath as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Falha ao baixar arquivo de export do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/finalization/repair', methods=['POST'])
def repair_report_finalization_route(report_id: str):
    """Reparar finalizacao do relatorio sem chamar LLM."""
    try:
        result = repair_report_finalization(report_id)
        return jsonify({
            "success": True,
            "data": result,
        }), 200
    except ReportFinalizationNotFound as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except ReportFinalizationConflict as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 409
    except Exception as e:
        logger.error(f"Falha ao reparar finalizacao do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@report_bp.route('/<report_id>/artifacts/<artifact_name>', methods=['GET'])
def get_report_artifact(report_id: str, artifact_name: str):
    """Obter um artefato JSON especifico do relatorio."""
    try:
        report = ReportManager.get_report(report_id)
        if not report:
            return jsonify({
                "success": False,
                "error": f"Relatório não encontrado: {report_id}"
            }), 404

        artifact = ReportManager.load_json_artifact(report_id, artifact_name)
        if artifact is None:
            return jsonify({
                "success": False,
                "error": f"Artefato não encontrado: {artifact_name}"
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "simulation_id": report.simulation_id,
                "artifact_name": os.path.basename(artifact_name),
                "artifact": artifact,
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter artefato do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/mission-bundle', methods=['GET'])
def get_mission_bundle(report_id: str):
    """Gerar manifesto final da missao a partir dos artefatos do relatorio."""
    try:
        report = ReportManager.get_report(report_id)
        if not report:
            return jsonify({"success": False, "error": "Relatório não encontrado"}), 404
        if report.status != ReportStatus.COMPLETED:
            status_value = report.status.value if hasattr(report.status, "value") else str(report.status)
            return jsonify({
                "success": False,
                "error": "Pacote final ainda não está pronto",
                "data": {
                    "status": status_value,
                },
            }), 409

        existing_bundle = ReportManager.load_json_artifact(report_id, "mission_bundle.json")
        if isinstance(existing_bundle, dict):
            return jsonify({
                "success": True,
                "data": existing_bundle,
            })

        artifacts = ReportManager.list_json_artifacts(report_id)
        artifact_names = [artifact["name"] for artifact in artifacts]
        required_artifacts = {
            "cost_meter.json": ReportManager.load_json_artifact(report_id, "cost_meter.json"),
            "power_selection.json": ReportManager.load_json_artifact(report_id, "power_selection.json"),
            "power_persona_context.json": ReportManager.load_json_artifact(report_id, "power_persona_context.json"),
            "forecast_ledger.json": ReportManager.load_json_artifact(report_id, "forecast_ledger.json"),
        }
        missing_artifacts = [
            name
            for name, payload in required_artifacts.items()
            if payload is None
        ]
        if missing_artifacts:
            return jsonify({
                "success": False,
                "error": "Pacote final aguardando arquivos essenciais",
                "data": {
                    "arquivos_pendentes": missing_artifacts,
                },
            }), 409

        cost_meter = required_artifacts["cost_meter.json"] or {}
        power_selection = required_artifacts["power_selection.json"] or {}
        persona_selection = required_artifacts["power_persona_context.json"] or {}
        forecast_ledger = required_artifacts["forecast_ledger.json"] or {}
        enriched_forecast_ledger = _enrich_forecast_ledger_payload(forecast_ledger)
        if enriched_forecast_ledger != forecast_ledger:
            ReportManager.save_json_artifact(report_id, "forecast_ledger.json", enriched_forecast_ledger)
            forecast_ledger = enriched_forecast_ledger

        bundle = MissionBundle().gerar_manifesto(
            report_id=report.report_id,
            simulation_id=report.simulation_id,
            custo=cost_meter,
            poderes=power_selection.get("poderes_selecionados", []),
            personas=persona_selection.get("items", []),
            previsoes=forecast_ledger.get("previsoes", []),
            arquivos=artifact_names,
        )
        ReportManager.save_json_artifact(report_id, "mission_bundle.json", bundle)

        return jsonify({
            "success": True,
            "data": bundle,
        })
    except Exception as e:
        logger.error(f"Falha ao gerar bundle da missao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id: str):
    """
    Baixar relatorio (formato Markdown)

    Retorna arquivo Markdown
    """
    try:
        report = ReportManager.get_report(report_id)

        if not report:
            return jsonify({
                "success": False,
                "error": f"Relatório não encontrado: {report_id}"
            }), 404

        md_path = ReportManager._get_report_markdown_path(report_id)

        if not os.path.exists(md_path):
            # Se o arquivo MD nao existe, gerar um arquivo temporario
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(report.markdown_content)
                temp_path = f.name

            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f"{report_id}.md"
            )

        return send_file(
            md_path,
            as_attachment=True,
            download_name=f"{report_id}.md"
        )

    except Exception as e:
        logger.error(f"Falha ao baixar relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id: str):
    """Excluir relatorio"""
    try:
        success = ReportManager.delete_report(report_id)

        if not success:
            return jsonify({
                "success": False,
                "error": f"Relatório não encontrado: {report_id}"
            }), 404

        return jsonify({
            "success": True,
            "message": f"Relatório removido: {report_id}"
        })

    except Exception as e:
        logger.error(f"Falha ao excluir relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de conversa com Report Agent ==============

@report_bp.route('/chat', methods=['POST'])
def chat_with_report_agent():
    """
    Conversar com o Report Agent

    O Report Agent pode chamar autonomamente ferramentas de busca durante a conversa para responder perguntas

    Requisicao (JSON):
        {
            "simulation_id": "sim_xxxx",        // Obrigatorio, ID da simulacao
            "message": "Explique a evolução da opinião pública",    // Obrigatorio: mensagem do usuario
            "chat_history": [                   // Opcional, historico da conversa
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    Retorno:
        {
            "success": true,
            "data": {
                "response": "Resposta do Agent...",
                "tool_calls": [lista de ferramentas chamadas],
                "sources": [fontes de informacao]
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        message = data.get('message')
        chat_history = data.get('chat_history', [])
        tool_mode = data.get('tool_mode')

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Informe o simulation_id"
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "error": "Informe a mensagem"
            }), 400

        # Obter informacoes da simulacao e do projeto
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulação não encontrada: {simulation_id}"
            }), 404

        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto não encontrado: {state.project_id}"
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "ID do grafo ausente"
            }), 400

        simulation_requirement = project.simulation_requirement or ""

        # Criar Agent e realizar conversa
        agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement
        )

        result = agent.chat(message=message, chat_history=chat_history, tool_mode=tool_mode)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Falha na conversa: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interfaces de progresso e secoes do relatorio ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
def get_report_progress(report_id: str):
    """
    Obter progresso da geracao do relatorio (tempo real)

    Retorno:
        {
            "success": true,
            "data": {
                "status": "generating",
                "progress": 45,
                "message": "Gerando seção: descobertas principais",
                "current_section": "Descobertas principais",
                "completed_sections": ["Resumo executivo", "Contexto da simulacao"],
                "updated_at": "2025-12-09T..."
            }
        }
    """
    try:
        progress = ReportManager.get_progress(report_id)

        if not progress:
            return jsonify({
                "success": False,
                "error": f"Relatório não encontrado ou informações de progresso indisponíveis: {report_id}"
            }), 404

        return jsonify({
            "success": True,
            "data": progress
        })

    except Exception as e:
        logger.error(f"Falha ao obter progresso do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/sections', methods=['GET'])
def get_report_sections(report_id: str):
    """
    Obter lista de secoes ja geradas (saida por secoes)

    O frontend pode consultar esta interface para obter o conteudo das secoes ja geradas,
    sem precisar esperar o relatorio completo

    Retorno:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "sections": [
                    {
                        "filename": "section_01.md",
                        "section_index": 1,
                        "content": "## Resumo executivo\\n\\n..."
                    },
                    ...
                ],
                "total_sections": 3,
                "is_complete": false
            }
        }
    """
    try:
        sections = ReportManager.get_generated_sections(report_id)

        # Obter estado do relatorio
        report = ReportManager.get_report(report_id)
        is_complete = report is not None and report.status == ReportStatus.COMPLETED

        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "sections": sections,
                "total_sections": len(sections),
                "is_complete": is_complete
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter lista de secoes: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
def get_single_section(report_id: str, section_index: int):
    """
    Obter conteudo de uma unica secao

    Retorno:
        {
            "success": true,
            "data": {
                "filename": "section_01.md",
                "content": "## Resumo executivo\\n\\n..."
            }
        }
    """
    try:
        section_path = ReportManager._get_section_path(report_id, section_index)

        if not os.path.exists(section_path):
            return jsonify({
                "success": False,
                "error": f"Seção não encontrada: section_{section_index:02d}.md"
            }), 404

        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            "success": True,
            "data": {
                "filename": f"section_{section_index:02d}.md",
                "section_index": section_index,
                "content": content
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter conteudo da secao: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de verificacao de estado do relatorio ==============

@report_bp.route('/check/<simulation_id>', methods=['GET'])
def check_report_status(simulation_id: str):
    """
    Verificar se a simulacao possui relatorio e seu estado

    Usado pelo frontend para determinar se a funcionalidade de Interview esta desbloqueada

    Retorno:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "has_report": true,
                "report_status": "completed",
                "report_id": "report_xxxx",
                "interview_unlocked": true
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None

        # Interview so e desbloqueado apos conclusao do relatorio
        interview_unlocked = has_report and report.status == ReportStatus.COMPLETED

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "has_report": has_report,
                "report_status": report_status,
                "report_id": report_id,
                "interview_unlocked": interview_unlocked
            }
        })

    except Exception as e:
        logger.error(f"Falha ao verificar estado do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de log do Agent ==============

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
def get_agent_log(report_id: str):
    """
    Obter log detalhado de execucao do Report Agent

    Obtem em tempo real cada acao durante a geracao do relatorio, incluindo:
    - Inicio do relatorio, inicio/conclusao do planejamento
    - Inicio de cada secao, chamadas de ferramentas, respostas do LLM, conclusao
    - Conclusao ou falha do relatorio

    Parametros de query:
        from_line: A partir de qual linha comecar a leitura (opcional, padrao 0, para obtencao incremental)

    Retorno:
        {
            "success": true,
            "data": {
                "logs": [
                    {
                        "timestamp": "2025-12-13T...",
                        "elapsed_seconds": 12.5,
                        "report_id": "report_xxxx",
                        "action": "tool_call",
                        "stage": "generating",
                        "section_title": "Resumo executivo",
                        "section_index": 1,
                        "details": {
                            "tool_name": "insight_forge",
                            "parameters": {...},
                            ...
                        }
                    },
                    ...
                ],
                "total_lines": 25,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)

        log_data = ReportManager.get_agent_log(report_id, from_line=from_line)

        return jsonify({
            "success": True,
            "data": log_data
        })

    except Exception as e:
        logger.error(f"Falha ao obter log do Agent: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/agent-log/stream', methods=['GET'])
def stream_agent_log(report_id: str):
    """
    Obter log completo do Agent (obtencao unica de tudo)

    Retorno:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 25
            }
        }
    """
    try:
        logs = ReportManager.get_agent_log_stream(report_id)

        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter log do Agent: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de log do console ==============

@report_bp.route('/<report_id>/console-log', methods=['GET'])
def get_console_log(report_id: str):
    """
    Obter log de saida do console do Report Agent

    Obtem em tempo real a saida do console durante a geracao do relatorio (INFO, WARNING etc.),
    diferente da interface agent-log que retorna logs JSON estruturados;
    este e um log em formato texto puro estilo console.

    Parametros de query:
        from_line: A partir de qual linha comecar a leitura (opcional, padrao 0, para obtencao incremental)

    Retorno:
        {
            "success": true,
            "data": {
                "logs": [
                    "[19:46:14] INFO: Busca concluida: encontrados 15 fatos relevantes",
                    "[19:46:14] INFO: Busca no grafo: graph_id=xxx, query=...",
                    ...
                ],
                "total_lines": 100,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)

        log_data = ReportManager.get_console_log(report_id, from_line=from_line)

        return jsonify({
            "success": True,
            "data": log_data
        })

    except Exception as e:
        logger.error(f"Falha ao obter log do console: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/console-log/stream', methods=['GET'])
def stream_console_log(report_id: str):
    """
    Obter log completo do console (obtencao unica de tudo)

    Retorno:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 100
            }
        }
    """
    try:
        logs = ReportManager.get_console_log_stream(report_id)

        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })

    except Exception as e:
        logger.error(f"Falha ao obter log do console: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de ferramentas (para depuracao) ==============

@report_bp.route('/tools/search', methods=['POST'])
def search_graph_tool():
    """
    Interface de ferramenta de busca no grafo (para depuracao)

    Requisicao (JSON):
        {
            "graph_id": "mirofish_xxxx",
            "query": "consulta de busca",
            "limit": 10
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')
        query = data.get('query')
        limit = data.get('limit', 10)

        if not graph_id or not query:
            return jsonify({
                "success": False,
                "error": "Informe graph_id e query"
            }), 400

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": result.to_dict()
        })

    except Exception as e:
        logger.error(f"Falha na busca do grafo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/tools/statistics', methods=['POST'])
def get_graph_statistics_tool():
    """
    Interface de ferramenta de estatisticas do grafo (para depuracao)

    Requisicao (JSON):
        {
            "graph_id": "mirofish_xxxx"
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

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.get_graph_statistics(graph_id)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Falha ao obter estatisticas do grafo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
