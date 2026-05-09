"""Readiness para evolucao de analise pos-relatorio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .report_agent import Report, ReportManager
from ..utils.report_quality import audit_report_content_consistency


RECOMMENDED_TOOLS = [
    "quick_search",
    "panorama_search",
    "insight_forge",
    "interview_agents",
]


def _artifact(report_id: str, name: str) -> dict[str, Any]:
    payload = ReportManager.load_json_artifact(report_id, name)
    return payload if isinstance(payload, dict) else {}


def _quality_metrics(report: Report) -> dict[str, Any]:
    system_gate = _artifact(report.report_id, "system_gate.json")
    gate_metrics = system_gate.get("metrics") if isinstance(system_gate, dict) else None
    if isinstance(gate_metrics, dict):
        return gate_metrics
    quality_gate = report.quality_gate or {}
    metrics = quality_gate.get("metrics") if isinstance(quality_gate, dict) else None
    return metrics if isinstance(metrics, dict) else {}


def _content_consistency(report: Report, metrics: dict[str, Any]) -> dict[str, Any]:
    artifact = _artifact(report.report_id, "content_consistency.json")
    if isinstance(artifact, dict) and "passes_gate" in artifact:
        return artifact

    quality_gate = report.quality_gate or {}
    embedded = quality_gate.get("content_consistency") if isinstance(quality_gate, dict) else None
    if isinstance(embedded, dict) and "passes_gate" in embedded:
        return embedded

    return audit_report_content_consistency(report.markdown_content or "", metrics)


def _count_evolution_runs(report_id: str) -> int:
    root = Path(ReportManager._get_report_folder(report_id)) / "evolution_runs"
    if not root.exists() or not root.is_dir():
        return 0
    return sum(1 for path in root.iterdir() if path.is_dir())


def _latest_run_status(report_id: str) -> str | None:
    root = Path(ReportManager._get_report_folder(report_id)) / "evolution_runs"
    if not root.exists() or not root.is_dir():
        return None
    run_dirs = sorted((path for path in root.iterdir() if path.is_dir()), key=lambda p: p.name)
    if not run_dirs:
        return None
    metrics_path = run_dirs[-1] / "METRICS.json"
    if not metrics_path.exists():
        return None
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    status = payload.get("status")
    return str(status) if status else None


def _blockers(report: Report, delivery_status: str, content_consistency: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if delivery_status != "publishable":
        blockers.append(f"Relatorio ainda nao esta publicavel: {delivery_status}.")
    quality_gate = report.quality_gate or {}
    evidence_audit = report.evidence_audit or {}
    blockers.extend(str(issue) for issue in quality_gate.get("issues") or [])
    unsupported_numbers = evidence_audit.get("unsupported_numbers") or []
    unsupported_quotes = evidence_audit.get("unsupported_quotes") or []
    if unsupported_numbers:
        blockers.append("Auditoria numerica ainda tem claims sem suporte.")
    if unsupported_quotes:
        blockers.append("Auditoria de citacoes ainda tem aspas sem suporte.")
    if content_consistency and content_consistency.get("passes_gate") is False:
        blockers.append("Auditoria de consistencia de conteudo encontrou problemas no relatorio final.")
        for issue in (content_consistency.get("issues") or [])[:5]:
            message = issue.get("message") if isinstance(issue, dict) else str(issue)
            if message:
                blockers.append(str(message))
    return blockers


def _gaps(metrics: dict[str, Any], evolution_runs_count: int) -> list[str]:
    gaps: list[str] = []
    nodes = int(metrics.get("graph_nodes_count") or metrics.get("state_entities_count") or 0)
    actions = int(metrics.get("total_actions_count") or metrics.get("total_actions_count_run_state") or 0)
    rounds = int(metrics.get("total_rounds") or 0)
    if nodes and nodes < 10:
        gaps.append("Grafo pequeno; ampliar entidades/relacoes antes de conclusao forte.")
    if actions and actions < 30:
        gaps.append("Amostra de acoes limitada; comparar nova rodada antes de extrapolar.")
    if rounds and rounds < 72:
        gaps.append("Simulacao curta; validar estabilidade temporal em novo ciclo.")
    if evolution_runs_count == 0:
        gaps.append("Nenhum ciclo RalphLoop registrado para esta analise.")
    return gaps


def build_report_evolution_readiness(report_id: str) -> dict[str, Any]:
    """Retorna estado read-only para decidir se a analise pode evoluir."""
    report = ReportManager.get_report(report_id)
    if not report:
        return {
            "report_id": report_id,
            "status": "missing",
            "can_deep_research": False,
            "can_create_ralph_run": False,
            "next_action": "open_report",
            "blockers": ["Relatorio nao encontrado."],
        }

    delivery_status = report.delivery_status()
    metrics = _quality_metrics(report)
    content_consistency = _content_consistency(report, metrics)
    evolution_runs_count = _count_evolution_runs(report_id)
    blockers = _blockers(report, delivery_status, content_consistency)
    ready = delivery_status == "publishable" and not blockers
    can_autoresearch = ready and evolution_runs_count >= 3

    return {
        "schema": "mirofish.report_evolution_readiness.v1",
        "report_id": report.report_id,
        "simulation_id": report.simulation_id,
        "graph_id": report.graph_id,
        "status": "ready_for_evolution" if ready else "blocked",
        "delivery_status": delivery_status,
        "can_deep_research": ready,
        "can_create_ralph_run": ready,
        "can_autoresearch_review": can_autoresearch,
        "next_action": "run_autoresearch_review" if can_autoresearch else ("run_deep_research" if ready else "repair_report"),
        "recommended_tools": RECOMMENDED_TOOLS,
        "metrics": {
            "graph_nodes_count": metrics.get("graph_nodes_count") or metrics.get("state_entities_count") or 0,
            "graph_edges_count": metrics.get("graph_edges_count") or metrics.get("graph_relationships_count") or 0,
            "total_rounds": metrics.get("total_rounds") or 0,
            "current_round": metrics.get("current_round") or 0,
            "total_actions_count": metrics.get("total_actions_count") or metrics.get("total_actions_count_run_state") or 0,
            "profiles_count": metrics.get("profiles_count") or metrics.get("state_profiles_count") or 0,
        },
        "evolution_runs_count": evolution_runs_count,
        "latest_evolution_run_status": _latest_run_status(report_id),
        "content_consistency": content_consistency,
        "gaps": _gaps(metrics, evolution_runs_count),
        "blockers": blockers,
    }
