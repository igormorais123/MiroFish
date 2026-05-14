"""Checklist metodologico para entrega de relatorios."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

from .report_agent import ReportManager


HARD_BLOCKER = "hard_blocker"
WARNING = "warning"
INFO = "info"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _item(check_id: str, severity: str, passes: bool, message: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "severity": severity,
        "passes": passes,
        "message": message,
    }


def _artifact_passes(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("passes_gate") is True:
        return True
    if payload.get("passes") is True:
        return True
    if payload.get("bundle_verified") is True:
        return True
    return False


def _read_full_report(report_id: str) -> tuple[str, bool]:
    path = ReportManager._get_report_markdown_path(report_id)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        return content, bool(content.strip())
    return "", False


def _numbered_markdown_headings(content: str) -> list[str]:
    headings: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^#{1,6}\s+\d+[\).]\s+\S+", stripped):
            headings.append(stripped)
    return headings


def evaluate_report_method_checklist(report_id: str) -> dict[str, Any]:
    """Avalia se o relatorio tem contrato minimo para entrega executiva."""
    report = ReportManager.get_report(report_id)
    checks: list[dict[str, Any]] = []

    if not report:
        checks.append(_item("report_exists", HARD_BLOCKER, False, f"Relatorio nao encontrado: {report_id}"))
        return _build_payload(report_id, checks)

    checks.append(_item("report_exists", HARD_BLOCKER, True, "Relatorio encontrado."))

    publishable = report.is_publishable()
    checks.append(_item(
        "report_publishable",
        HARD_BLOCKER,
        publishable,
        "Relatorio passou pelos gates de publicacao." if publishable else "Relatorio ainda nao e publicavel para cliente.",
    ))

    system_gate = ReportManager.load_json_artifact(report_id, "system_gate.json") or report.quality_gate
    system_passes = _artifact_passes(system_gate)
    checks.append(_item(
        "system_gate_passed",
        HARD_BLOCKER,
        system_passes,
        "Gate estrutural aprovado." if system_passes else "Gate estrutural ausente ou reprovado.",
    ))

    evidence_audit = ReportManager.load_json_artifact(report_id, "evidence_audit.json") or report.evidence_audit
    evidence_passes = _artifact_passes(evidence_audit)
    checks.append(_item(
        "evidence_audit_passed",
        HARD_BLOCKER,
        evidence_passes,
        "Auditoria de evidencias aprovada." if evidence_passes else "Auditoria de evidencias ausente ou reprovada.",
    ))

    decision_packet = ReportManager.load_json_artifact(report_id, "decision_packet.json")
    decision_packet_passes = _decision_packet_passes(decision_packet)
    checks.append(_item(
        "decision_packet_locked",
        HARD_BLOCKER,
        decision_packet_passes,
        "Pacote de decisao preditiva travado com cenarios, convergencia e red team."
        if decision_packet_passes
        else "decision_packet.json ausente ou incompleto; entrega preditiva fica sem lastro oficial.",
    ))

    full_report_content, has_full_report = _read_full_report(report_id)
    checks.append(_item(
        "full_report_present",
        HARD_BLOCKER,
        has_full_report,
        "Relatorio completo encontrado." if has_full_report else "full_report.md ausente ou vazio.",
    ))

    optional_artifacts = {
        "mission_bundle_present": "mission_bundle.json",
        "forecast_ledger_present": "forecast_ledger.json",
        "cost_meter_present": "cost_meter.json",
    }
    for check_id, filename in optional_artifacts.items():
        present = ReportManager.load_json_artifact(report_id, filename) is not None
        checks.append(_item(
            check_id,
            WARNING,
            present,
            f"{filename} encontrado." if present else f"{filename} ausente; entrega fica menos explicavel.",
        ))

    numbered_headings = _numbered_markdown_headings(full_report_content)
    checks.append(_item(
        "numbered_markdown_headings",
        WARNING,
        not bool(numbered_headings),
        "Titulos Markdown numerados nao detectados."
        if not numbered_headings
        else "Titulos Markdown numerados detectados; manter como aviso e nao bloquear entrega.",
    ))

    return _build_payload(report_id, checks)


def _build_payload(report_id: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    hard_blockers = [
        item for item in checks
        if item["severity"] == HARD_BLOCKER and item["passes"] is not True
    ]
    warnings = [
        item for item in checks
        if item["severity"] == WARNING and item["passes"] is not True
    ]
    info = [item for item in checks if item["severity"] == INFO]

    return {
        "report_id": report_id,
        "generated_at": _now_iso(),
        "hard_checks_pass": not hard_blockers,
        "hard_blockers": hard_blockers,
        "warnings": warnings,
        "info": info,
        "checks": checks,
        "summary": {
            "hard_blockers": len(hard_blockers),
            "warnings": len(warnings),
            "checks": len(checks),
        },
    }


def _decision_packet_passes(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    scenarios = payload.get("scenarios")
    red_team = payload.get("red_team")
    convergence = payload.get("convergence")
    method_lock = payload.get("method_lock")
    if not all(isinstance(item, dict) for item in (scenarios, red_team, convergence, method_lock)):
        return False

    scenario_values = [
        item.get("probability_percent")
        for item in scenarios.values()
        if isinstance(item, dict)
    ]
    try:
        sums_to_100 = sum(int(value) for value in scenario_values) == 100
    except (TypeError, ValueError):
        sums_to_100 = False

    return bool(
        sums_to_100
        and payload.get("conviction_operational") is not None
        and convergence.get("score_percent") is not None
        and red_team.get("opposing_thesis")
        and red_team.get("reversal_triggers")
        and method_lock.get("status") == "locked"
    )
