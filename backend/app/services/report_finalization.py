"""Reparo deterministico da finalizacao de relatorios."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .report_agent import ReportManager, ReportStatus
from .report_method_checklist import evaluate_report_method_checklist


class ReportFinalizationError(Exception):
    """Erro base de finalizacao."""


class ReportFinalizationNotFound(ReportFinalizationError):
    """Relatorio nao encontrado."""


class ReportFinalizationConflict(ReportFinalizationError):
    """Relatorio ainda esta sendo gerado ou nao pode ser reparado agora."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _preview(content: str, limit: int = 500) -> str:
    text = (content or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def repair_report_finalization(report_id: str) -> dict[str, Any]:
    """Reconstrui artefatos finais sem chamar LLM nem alterar evidencias brutas."""
    report = ReportManager.get_report(report_id)
    if not report:
        raise ReportFinalizationNotFound(f"Relatorio nao encontrado: {report_id}")

    if report.status in {ReportStatus.PENDING, ReportStatus.PLANNING, ReportStatus.GENERATING}:
        raise ReportFinalizationConflict("Relatorio ainda em geracao.")

    if report.status == ReportStatus.FAILED:
        raise ReportFinalizationConflict("Relatorio falhou; reparo automatico nao deve mascarar erro de geracao.")

    full_report = ""
    full_report_rebuilt = False
    if report.outline:
        full_report = ReportManager.assemble_full_report(report_id, report.outline)
        full_report_rebuilt = bool((full_report or "").strip())
        report.markdown_content = full_report
        ReportManager.save_report(report)
    elif report.markdown_content:
        full_report = report.markdown_content

    checklist = evaluate_report_method_checklist(report_id)
    ReportManager.save_json_artifact(report_id, "report_method_checklist.json", checklist)

    result = {
        "report_id": report_id,
        "status": "repaired",
        "repaired_at": _now_iso(),
        "full_report_rebuilt": full_report_rebuilt,
        "method_checklist_passed": checklist.get("hard_checks_pass") is True,
        "hard_blockers": checklist.get("hard_blockers", []),
        "warnings": checklist.get("warnings", []),
        "full_report_preview": _preview(full_report),
    }
    ReportManager.save_json_artifact(report_id, "finalization_repair.json", result)
    return result
