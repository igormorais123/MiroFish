import pytest

from app.services.report_agent import Report, ReportOutline, ReportSection, ReportStatus
from app.services.report_finalization import (
    ReportFinalizationConflict,
    ReportFinalizationNotFound,
    repair_report_finalization,
)


def _completed_report():
    return Report(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        outline=ReportOutline(
            title="Relatorio",
            summary="Resumo",
            sections=[ReportSection(title="Base"), ReportSection(title="Conclusao")],
        ),
        markdown_content="",
        quality_gate={"passes_gate": True, "metrics": {}},
        evidence_audit={"passes_gate": True},
    )


def test_repair_reassembles_full_report_and_saves_checklist(monkeypatch):
    saved = {}
    report = _completed_report()

    monkeypatch.setattr("app.services.report_finalization.ReportManager.get_report", lambda report_id: report)
    monkeypatch.setattr(
        "app.services.report_finalization.ReportManager.assemble_full_report",
        lambda report_id, outline: "# Relatorio\n\n## Base\n\nTexto\n\n## Secao extra\n\nTexto",
    )
    monkeypatch.setattr(
        "app.services.report_finalization.evaluate_report_method_checklist",
        lambda report_id: {"report_id": report_id, "hard_checks_pass": True, "hard_blockers": [], "warnings": []},
    )
    monkeypatch.setattr(
        "app.services.report_finalization.ReportManager.save_json_artifact",
        lambda report_id, filename, payload: saved.__setitem__(filename, payload),
    )
    monkeypatch.setattr("app.services.report_finalization.ReportManager.save_report", lambda report: None)

    result = repair_report_finalization("report_1")

    assert result["status"] == "repaired"
    assert result["full_report_rebuilt"] is True
    assert "Secao extra" in result["full_report_preview"]
    assert saved["report_method_checklist.json"]["hard_checks_pass"] is True
    assert saved["finalization_repair.json"]["status"] == "repaired"


def test_repair_blocks_report_still_generating(monkeypatch):
    report = _completed_report()
    report.status = ReportStatus.GENERATING
    monkeypatch.setattr("app.services.report_finalization.ReportManager.get_report", lambda report_id: report)

    with pytest.raises(ReportFinalizationConflict):
        repair_report_finalization("report_1")


def test_repair_missing_report_raises_not_found(monkeypatch):
    monkeypatch.setattr("app.services.report_finalization.ReportManager.get_report", lambda report_id: None)

    with pytest.raises(ReportFinalizationNotFound):
        repair_report_finalization("report_missing")
