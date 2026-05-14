from app.services.report_agent import Report, ReportStatus
from app.services.report_method_checklist import evaluate_report_method_checklist


def _publishable_report():
    return Report(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        markdown_content="# Relatorio\n\nConteudo final.",
        quality_gate={"passes_gate": True, "metrics": {}},
        evidence_audit={"passes_gate": True},
    )


def _decision_packet():
    return {
        "schema": "mirofish.decision_packet.v2",
        "conviction_operational": 0.78,
        "method_lock": {"status": "locked"},
        "scenarios": {
            "base": {"probability_percent": 64},
            "optimistic": {"probability_percent": 20},
            "contrary": {"probability_percent": 16},
        },
        "convergence": {"score_percent": 74},
        "red_team": {
            "opposing_thesis": "A tese adversaria ataca o sinal emergente.",
            "reversal_triggers": ["cenario contrario ganha forca"],
        },
    }


def test_method_checklist_blocks_missing_report(monkeypatch):
    monkeypatch.setattr("app.services.report_method_checklist.ReportManager.get_report", lambda report_id: None)

    checklist = evaluate_report_method_checklist("report_missing")

    assert checklist["hard_checks_pass"] is False
    assert checklist["hard_blockers"]
    assert checklist["hard_blockers"][0]["id"] == "report_exists"


def test_method_checklist_requires_publishable_gates_and_full_report(monkeypatch, tmp_path):
    report = _publishable_report()
    full_report_path = tmp_path / "full_report.md"
    full_report_path.write_text(report.markdown_content, encoding="utf-8")

    monkeypatch.setattr("app.services.report_method_checklist.ReportManager.get_report", lambda report_id: report)
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager._get_report_markdown_path",
        lambda report_id: str(full_report_path),
    )
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager.load_json_artifact",
        lambda report_id, filename: {
            "system_gate.json": {"passes_gate": True},
            "evidence_audit.json": {"passes_gate": True},
            "decision_packet.json": _decision_packet(),
            "mission_bundle.json": {"ok": True},
            "forecast_ledger.json": {"ok": True},
            "cost_meter.json": {"ok": True},
        }.get(filename),
    )

    checklist = evaluate_report_method_checklist("report_1")

    assert checklist["hard_checks_pass"] is True
    assert checklist["hard_blockers"] == []
    assert checklist["summary"]["hard_blockers"] == 0


def test_method_checklist_warns_when_enrichment_artifacts_are_missing(monkeypatch, tmp_path):
    report = _publishable_report()
    full_report_path = tmp_path / "full_report.md"
    full_report_path.write_text(report.markdown_content, encoding="utf-8")

    monkeypatch.setattr("app.services.report_method_checklist.ReportManager.get_report", lambda report_id: report)
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager._get_report_markdown_path",
        lambda report_id: str(full_report_path),
    )
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager.load_json_artifact",
        lambda report_id, filename: {
            "system_gate.json": {"passes_gate": True},
            "evidence_audit.json": {"passes_gate": True},
            "decision_packet.json": _decision_packet(),
        }.get(filename),
    )

    checklist = evaluate_report_method_checklist("report_1")

    assert checklist["hard_checks_pass"] is True
    assert {item["id"] for item in checklist["warnings"]} >= {
        "mission_bundle_present",
        "forecast_ledger_present",
        "cost_meter_present",
    }


def test_method_checklist_keeps_markdown_numbered_titles_as_warning_only(monkeypatch, tmp_path):
    report = _publishable_report()
    full_report_path = tmp_path / "full_report.md"
    full_report_path.write_text("# 1. Cenario\n\n## 2. Analise\n\nConteudo.", encoding="utf-8")

    monkeypatch.setattr("app.services.report_method_checklist.ReportManager.get_report", lambda report_id: report)
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager._get_report_markdown_path",
        lambda report_id: str(full_report_path),
    )
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager.load_json_artifact",
        lambda report_id, filename: {
            "system_gate.json": {"passes_gate": True},
            "evidence_audit.json": {"passes_gate": True},
            "decision_packet.json": _decision_packet(),
        }.get(filename),
    )

    checklist = evaluate_report_method_checklist("report_1")

    assert checklist["hard_checks_pass"] is True
    assert any(item["id"] == "numbered_markdown_headings" for item in checklist["warnings"])


def test_method_checklist_bloqueia_decision_packet_ausente(monkeypatch, tmp_path):
    report = _publishable_report()
    full_report_path = tmp_path / "full_report.md"
    full_report_path.write_text(report.markdown_content, encoding="utf-8")

    monkeypatch.setattr("app.services.report_method_checklist.ReportManager.get_report", lambda report_id: report)
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager._get_report_markdown_path",
        lambda report_id: str(full_report_path),
    )
    monkeypatch.setattr(
        "app.services.report_method_checklist.ReportManager.load_json_artifact",
        lambda report_id, filename: {
            "system_gate.json": {"passes_gate": True},
            "evidence_audit.json": {"passes_gate": True},
        }.get(filename),
    )

    checklist = evaluate_report_method_checklist("report_1")

    assert checklist["hard_checks_pass"] is False
    assert any(item["id"] == "decision_packet_locked" for item in checklist["hard_blockers"])
