"""Pacote de decisao de entrega para relatorios."""

from __future__ import annotations

from typing import Any

from .report_agent import ReportManager


def _artifact_names(report_id: str) -> list[str]:
    return [
        str(item.get("name"))
        for item in ReportManager.list_json_artifacts(report_id)
        if item.get("name")
    ]


def _verified_bundle(report_id: str) -> dict[str, Any] | None:
    verification = ReportManager.load_json_artifact(report_id, "report_bundle_verification.json")
    if not isinstance(verification, dict):
        return None
    if verification.get("passes") is True or verification.get("bundle_verified") is True:
        return verification
    return None


def build_report_delivery_packet(report_id: str) -> dict[str, Any]:
    """Consolida estado de entrega sem promover rascunho a entrega cliente."""
    report = ReportManager.get_report(report_id)
    if not report:
        return {
            "report_id": report_id,
            "status": "missing",
            "next_action": "select_report",
            "report_publishable": False,
            "bundle_verified": False,
            "client_deliverable": False,
            "blockers": [f"Relatorio nao encontrado: {report_id}"],
            "warnings": [],
            "artifacts": [],
        }

    delivery_status = report.delivery_status()
    artifacts = _artifact_names(report_id)
    bundle_verification = _verified_bundle(report_id)
    bundle_verified = bundle_verification is not None
    report_publishable = report.is_publishable()
    blockers: list[str] = []
    warnings: list[str] = []

    if delivery_status == "failed":
        blockers.append(report.error or "Relatorio falhou.")
    elif delivery_status == "in_progress":
        blockers.append("Relatorio ainda esta em geracao.")
    elif delivery_status == "legacy_unverified":
        blockers.append("Relatorio antigo sem gate/auditoria persistidos.")
    elif delivery_status == "blocked_by_system_gate":
        blockers.extend((report.quality_gate or {}).get("issues") or ["Gate estrutural bloqueou o relatorio."])
    elif delivery_status == "blocked_by_evidence_audit":
        blockers.extend((report.evidence_audit or {}).get("unsupported_quotes") or ["Auditoria de evidencias bloqueou o relatorio."])
    elif delivery_status == "diagnostic_only":
        warnings.append("Relatorio em modo diagnostico; nao e entrega cliente.")

    if report_publishable and not bundle_verified:
        warnings.append("Bundle verificavel ainda nao foi gerado/aprovado.")

    client_deliverable = report_publishable and bundle_verified
    if client_deliverable:
        status = "client_deliverable"
        next_action = "download_verified_bundle"
    elif report_publishable:
        status = "ready_for_export"
        next_action = "generate_export_bundle"
    elif delivery_status == "diagnostic_only":
        status = "diagnostic_only"
        next_action = "review_diagnostic_or_rerun_client_mode"
    elif delivery_status == "in_progress":
        status = "report_in_progress"
        next_action = "wait_report"
    else:
        status = "blocked"
        next_action = "repair_or_review_blockers"

    return {
        "report_id": report.report_id,
        "simulation_id": report.simulation_id,
        "graph_id": report.graph_id,
        "status": status,
        "next_action": next_action,
        "report_status": getattr(report.status, "value", report.status),
        "delivery_status": delivery_status,
        "report_publishable": report_publishable,
        "bundle_verified": bundle_verified,
        "client_deliverable": client_deliverable,
        "blockers": blockers,
        "warnings": warnings,
        "artifacts": artifacts,
        "bundle_verification": bundle_verification,
    }
