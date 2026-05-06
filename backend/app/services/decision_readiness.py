"""Estado de prontidao de decisao para simulacoes."""

from __future__ import annotations

from typing import Any

from ..models.project import ProjectManager
from .report_agent import ReportManager
from .report_system_gate import evaluate_report_system_gate
from .simulation_manager import SimulationManager


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _next_action(status: str) -> str:
    return {
        "missing": "select_simulation",
        "blocked": "fix_simulation_or_source_material",
        "ready_for_report": "generate_report",
        "report_in_progress": "wait_report",
        "report_blocked": "repair_or_review_blockers",
        "report_diagnostic": "review_diagnostic_only",
        "ready_for_verified_delivery": "open_delivery_package",
    }.get(status, "review_state")


def evaluate_decision_readiness(
    simulation_id: str,
    *,
    graph_id: str | None = None,
    delivery_mode: str | None = None,
) -> dict[str, Any]:
    """Consolida simulacao, gate e relatorio em um estado de produto."""
    manager = SimulationManager()
    state = manager.get_simulation(simulation_id)
    if not state:
        status = "missing"
        return {
            "simulation_id": simulation_id,
            "status": status,
            "next_action": _next_action(status),
            "flags": {
                "simulation_exists": False,
                "gate_passes": False,
                "has_report": False,
                "report_publishable": False,
            },
            "blockers": [f"Simulacao nao encontrada: {simulation_id}"],
            "warnings": [],
            "metrics": {},
            "report": None,
        }

    project = ProjectManager.get_project(state.project_id)
    source_text = ProjectManager.get_extracted_text(state.project_id) if project else None
    effective_graph_id = graph_id or state.graph_id
    gate = evaluate_report_system_gate(
        simulation_id,
        effective_graph_id,
        source_text=source_text,
        delivery_mode=delivery_mode,
    )
    report = ReportManager.get_report_by_simulation(simulation_id)

    if report:
        delivery_status = report.delivery_status()
        if delivery_status == "publishable":
            status = "ready_for_verified_delivery"
        elif delivery_status == "diagnostic_only":
            status = "report_diagnostic"
        elif delivery_status in {"failed", "blocked_by_system_gate", "blocked_by_evidence_audit", "legacy_unverified"}:
            status = "report_blocked"
        else:
            status = "report_in_progress"
    elif gate.passes_gate:
        status = "ready_for_report"
    else:
        status = "blocked"

    report_payload = None
    if report:
        report_payload = {
            "report_id": report.report_id,
            "status": _enum_value(report.status),
            "delivery_status": report.delivery_status(),
            "report_publishable": report.is_publishable(),
        }

    return {
        "simulation_id": simulation_id,
        "project_id": state.project_id,
        "graph_id": effective_graph_id,
        "status": status,
        "next_action": _next_action(status),
        "flags": {
            "simulation_exists": True,
            "gate_passes": gate.passes_gate,
            "has_report": report is not None,
            "report_publishable": bool(report and report.is_publishable()),
            "diagnostic_only": bool(gate.metrics.get("diagnostic_only")),
        },
        "blockers": list(gate.issues),
        "warnings": list(gate.warnings),
        "metrics": {
            **gate.metrics,
            "simulation_status": _enum_value(state.status),
        },
        "report": report_payload,
    }
