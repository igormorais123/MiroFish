"""Gate estrutural para impedir relatorio fora do sistema consolidado.

Este modulo transforma a promessa operacional da INTEIA em contrato tecnico:
relatorio so pode ser gerado quando intake, grafo, perfis, simulacao executada,
evidencias locais e auditoria estiverem presentes.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from ..config import Config
from ..models.project import ProjectManager
from ..utils.logger import get_logger
from .simulation_data_reader import SimulationDataReader
from .delivery_governance import resolve_delivery_governance
from .simulation_manager import SimulationManager
from .simulation_runner import SimulationRunner

logger = get_logger("mirofish.report_system_gate")


class ReportGateError(RuntimeError):
    """Erro usado quando o relatorio nao pode sair do sistema."""

    def __init__(self, message: str, result: "ReportGateResult"):
        super().__init__(message)
        self.result = result


@dataclass
class ReportGateResult:
    """Resultado da validacao estrutural pre-relatorio."""

    passes_gate: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    contract_layers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passes_gate": self.passes_gate,
            "issues": self.issues,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
            "contract_layers": self.contract_layers,
        }


def _count_json_array(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0


def _count_csv_rows(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        return max(0, len(rows) - 1)
    except Exception:
        return 0


def _file_info(path: str) -> dict[str, Any]:
    exists = os.path.exists(path)
    return {
        "path": path,
        "exists": exists,
        "size": os.path.getsize(path) if exists and os.path.isfile(path) else 0,
    }


def _simulation_dir(simulation_id: str) -> str:
    return os.path.join(Config.UPLOAD_FOLDER, "simulations", simulation_id)


def collect_report_evidence(
    simulation_id: str,
    source_text: Optional[str] = None,
    *,
    max_actions: int = 500,
) -> dict[str, Any]:
    """Coleta corpus local que pode sustentar citacoes e claims do relatorio."""
    evidence_texts: list[str] = []
    evidence_index: list[dict[str, Any]] = []

    if source_text:
        evidence_texts.append(source_text)
        evidence_index.append({
            "kind": "source_text",
            "label": "material-base do projeto",
            "characters": len(source_text),
        })

    reader = SimulationDataReader(simulation_id)
    actions = reader.get_agent_actions()[:max_actions]
    for action in actions:
        content = action.get("action_args", {}).get("content", "")
        if not content:
            continue
        label = (
            f"{action.get('agent_name', 'agente')} "
            f"({action.get('platform', '')}, round {action.get('round_num', action.get('round', 0))})"
        )
        evidence_texts.append(content)
        evidence_index.append({
            "kind": "simulation_action",
            "label": label,
            "action_type": action.get("action_type", ""),
            "characters": len(content),
        })

    try:
        facts = reader.get_facts_for_report(limit=min(max_actions, 200))
        for fact in facts:
            if fact:
                evidence_texts.append(fact)
                evidence_index.append({
                    "kind": "simulation_fact",
                    "label": "fato extraido de actions.jsonl",
                    "characters": len(fact),
                })
    except Exception as exc:
        logger.warning(f"Falha ao coletar fatos locais da simulacao {simulation_id}: {exc}")

    return {
        "simulation_id": simulation_id,
        "evidence_texts": evidence_texts,
        "evidence_index": evidence_index,
        "total_evidence_documents": len(evidence_texts),
    }


def evaluate_report_system_gate(
    simulation_id: str,
    graph_id: Optional[str],
    *,
    source_text: Optional[str] = None,
    min_actions: Optional[int] = None,
    require_completed_simulation: Optional[bool] = None,
    require_source_text: Optional[bool] = None,
    delivery_mode: Optional[str] = None,
) -> ReportGateResult:
    """Valida precondicoes para gerar relatorio Helena/Mirofish."""
    issues: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {"simulation_id": simulation_id, "graph_id": graph_id}
    artifacts: dict[str, Any] = {}

    manager = SimulationManager()
    state = manager.get_simulation(simulation_id)
    if not state:
        issues.append(f"Simulacao nao encontrada: {simulation_id}")
        return ReportGateResult(False, issues, warnings, metrics, artifacts, _contract_layers())

    state_dict = state.to_dict()
    metrics.update({
        "simulation_status": state_dict.get("status"),
        "state_entities_count": state_dict.get("entities_count", 0),
        "state_profiles_count": state_dict.get("profiles_count", 0),
        "project_id": state_dict.get("project_id"),
    })

    if graph_id and state.graph_id and graph_id != state.graph_id:
        issues.append(f"graph_id informado ({graph_id}) difere do graph_id da simulacao ({state.graph_id})")
    if not (graph_id or state.graph_id):
        issues.append("graph_id ausente")

    project = ProjectManager.get_project(state.project_id)
    if not project:
        issues.append(f"Projeto nao encontrado: {state.project_id}")
    else:
        metrics["project_status"] = project.status.value if hasattr(project.status, "value") else project.status
        metrics["source_text_characters"] = len(source_text or "")
        if not project.simulation_requirement:
            issues.append("Projeto sem simulation_requirement")
        if not project.graph_id:
            warnings.append("Projeto sem graph_id persistido")

    sim_dir = _simulation_dir(simulation_id)
    config_path = os.path.join(sim_dir, "simulation_config.json")
    reddit_profiles_path = os.path.join(sim_dir, "reddit_profiles.json")
    twitter_profiles_path = os.path.join(sim_dir, "twitter_profiles.csv")
    twitter_actions_path = os.path.join(sim_dir, "twitter", "actions.jsonl")
    reddit_actions_path = os.path.join(sim_dir, "reddit", "actions.jsonl")
    simulation_config: dict[str, Any] = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            if isinstance(loaded_config, dict):
                simulation_config = loaded_config
        except Exception as exc:
            warnings.append(f"simulation_config.json existe, mas nao foi possivel ler: {exc}")

    delivery_policy = resolve_delivery_governance(
        simulation_config,
        requested_mode=delivery_mode,
        min_actions=min_actions,
        require_completed_simulation=require_completed_simulation,
        require_source_text=require_source_text,
    )
    min_actions = delivery_policy.min_actions
    require_completed = delivery_policy.require_completed_simulation
    require_source = delivery_policy.require_source_text
    metrics.update({
        "delivery_mode": delivery_policy.mode,
        "delivery_label": delivery_policy.label,
        "delivery_publishable_mode": delivery_policy.publishable,
        "diagnostic_only": not delivery_policy.publishable,
        "min_actions": min_actions,
        "require_completed_simulation": require_completed,
        "require_source_text": require_source,
        "delivery_policy": delivery_policy.to_dict(),
    })
    if not delivery_policy.publishable:
        warnings.append(
            "Modo diagnostico/smoke: resultado permitido apenas para avaliacao tecnica interna; nao publicavel."
        )

    if require_source and not (source_text or "").strip():
        issues.append("Texto-base do projeto ausente; relatorio ficaria sem corpus factual de referencia")

    artifacts.update({
        "simulation_dir": _file_info(sim_dir),
        "simulation_config": _file_info(config_path),
        "reddit_profiles": _file_info(reddit_profiles_path),
        "twitter_profiles": _file_info(twitter_profiles_path),
        "twitter_actions": _file_info(twitter_actions_path),
        "reddit_actions": _file_info(reddit_actions_path),
    })

    if not os.path.exists(config_path):
        issues.append("simulation_config.json ausente")

    reddit_profiles = _count_json_array(reddit_profiles_path)
    twitter_profiles = _count_csv_rows(twitter_profiles_path)
    profiles_total = max(reddit_profiles, twitter_profiles, state.profiles_count or 0)
    metrics.update({
        "reddit_profiles_count": reddit_profiles,
        "twitter_profiles_count": twitter_profiles,
        "profiles_count": profiles_total,
    })
    if profiles_total <= 0:
        issues.append("Nenhum perfil sintetico encontrado para sustentar agentes")

    run_state = SimulationRunner.get_run_state(simulation_id)
    if not run_state:
        issues.append("run_state.json ausente; simulacao nao tem execucao auditavel")
        run_dict = {}
    else:
        run_dict = run_state.to_detail_dict()
        metrics.update({
            "runner_status": run_dict.get("runner_status"),
            "total_rounds": run_dict.get("total_rounds", 0),
            "current_round": run_dict.get("current_round", 0),
            "total_actions_count_run_state": run_dict.get("total_actions_count", 0),
        })
        if require_completed and run_dict.get("runner_status") != "completed":
            issues.append(f"Simulacao nao concluida: runner_status={run_dict.get('runner_status')}")

    reader = SimulationDataReader(simulation_id)
    actions = reader.get_agent_actions()
    total_actions = len(actions) or int(run_dict.get("total_actions_count", 0) or 0)
    metrics["total_actions_count"] = total_actions

    if total_actions < min_actions:
        issues.append(
            f"Evidencia insuficiente: {total_actions} acoes de agentes; minimo operacional={min_actions}"
        )

    diversity = reader.get_diversity_metrics()
    metrics["diversity"] = diversity

    if diversity.get("generated_texts_count", 0) <= 0 and total_actions >= min_actions:
        issues.append("Simulacao sem textos gerados; nao ha conteudo semantico para analisar")

    if total_actions >= min_actions:
        if diversity.get("distinct_2", 0.0) < Config.REPORT_MIN_DISTINCT_2:
            issues.append(
                "Diversidade semantica baixa: "
                f"Distinct-2={diversity.get('distinct_2', 0.0):.2f}; "
                f"minimo={Config.REPORT_MIN_DISTINCT_2:.2f}"
            )

        if diversity.get("agent_activity_entropy_norm", 0.0) < Config.REPORT_MIN_AGENT_ACTIVITY_ENTROPY:
            issues.append(
                "Participacao concentrada demais: "
                f"entropia_agentes={diversity.get('agent_activity_entropy_norm', 0.0):.2f}; "
                f"minimo={Config.REPORT_MIN_AGENT_ACTIVITY_ENTROPY:.2f}"
            )

        behavior_entropy = diversity.get("action_type_entropy_norm", 0.0)
        if behavior_entropy < Config.REPORT_MIN_BEHAVIOR_ENTROPY:
            message = (
                "Baixa diversidade de tipos de acao: "
                f"entropia_acoes={behavior_entropy:.2f}; "
                f"minimo={Config.REPORT_MIN_BEHAVIOR_ENTROPY:.2f}. "
                "Isto pode indicar simulacao de monologo/postagem, nao opiniao publica."
            )
            if Config.REPORT_REQUIRE_ACTION_TYPE_DIVERSITY:
                issues.append(message)
            else:
                warnings.append(message)

        oasis_trace = diversity.get("oasis_trace", {}) or {}
        if (
            oasis_trace.get("db_files_found", 0) > 0
            and oasis_trace.get("interactive_actions_total", 0) <= 0
            and oasis_trace.get("dynamic_create_posts_estimate", 0) <= 0
        ):
            issues.append(
                "Trace OASIS sem comportamento social pos-estimulo: "
                "nao foram detectados comentarios, curtidas, repostagens, follows ou novas postagens alem dos estimulos iniciais"
            )

        if diversity.get("entity_type_coverage", 0) < 2:
            warnings.append("Baixa cobertura de papeis/entity_types; agentes podem estar pouco heterogeneos")

    if metrics.get("total_rounds", 0) and metrics.get("current_round", 0) < metrics.get("total_rounds", 0):
        warnings.append("Rodadas executadas abaixo do total configurado")

    passes_gate = not issues
    if not passes_gate:
        logger.warning(f"Gate de relatorio bloqueado para {simulation_id}: {issues}")

    return ReportGateResult(
        passes_gate=passes_gate,
        issues=issues,
        warnings=warnings,
        metrics=metrics,
        artifacts=artifacts,
        contract_layers=_contract_layers(),
    )


def assert_report_system_ready(
    simulation_id: str,
    graph_id: Optional[str],
    *,
    source_text: Optional[str] = None,
    delivery_mode: Optional[str] = None,
) -> ReportGateResult:
    """Falha fechado se o sistema nao estiver pronto para gerar relatorio."""
    result = evaluate_report_system_gate(
        simulation_id=simulation_id,
        graph_id=graph_id,
        source_text=source_text,
        delivery_mode=delivery_mode,
    )
    if not result.passes_gate:
        raise ReportGateError(
            "Relatorio bloqueado pelo gate estrutural INTEIA: " + "; ".join(result.issues),
            result,
        )
    return result


def _contract_layers() -> dict[str, str]:
    return {
        "intake_diagnostico": "Projeto, texto-base, contexto estruturado e simulation_requirement persistidos.",
        "agentes_sinteticos": "Perfis OASIS gerados a partir de entidades do grafo/fallback LLM.",
        "replica_digital": "simulation_config.json e execucao OASIS com run_state auditavel.",
        "verificacao": "Gate de prontidao, QC de overlap/grounding e auditoria de citacoes.",
        "entrega": "Relatorio Helena salvo com manifesto de evidencias e limites explicitos.",
    }


def compact_evidence_for_manifest(evidence_index: Iterable[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    """Mantem manifesto pequeno o bastante para JSON legivel."""
    return list(evidence_index or [])[:limit]
