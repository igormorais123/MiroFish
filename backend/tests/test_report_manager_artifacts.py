"""Testes dos artefatos auditaveis do ReportManager."""
from __future__ import annotations

from app.services.report_agent import Report, ReportManager, ReportStatus


def test_report_manager_salva_lista_e_carrega_artefato_json(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))

    ReportManager.save_json_artifact("report_1", "system_gate.json", {
        "passes_gate": True,
        "metrics": {"total_actions_count": 12},
    })
    ReportManager.save_json_artifact("report_1", "progress.json", {"progress": 50})

    artifacts = ReportManager.list_json_artifacts("report_1")
    loaded = ReportManager.load_json_artifact("report_1", "system_gate")

    assert [item["name"] for item in artifacts] == ["system_gate.json"]
    assert loaded["passes_gate"] is True
    assert loaded["metrics"]["total_actions_count"] == 12


def test_report_manager_nao_carrega_artefato_inexistente(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))

    assert ReportManager.load_json_artifact("report_ausente", "system_gate") is None
    assert ReportManager.list_json_artifacts("report_ausente") == []


def test_report_delivery_status_exige_gate_e_auditoria():
    report = Report(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="testar cenario",
        status=ReportStatus.COMPLETED,
    )

    assert report.delivery_status() == "legacy_unverified"
    assert report.is_publishable() is False

    report.quality_gate = {"passes_gate": True}
    report.evidence_audit = {"passes_gate": True}

    payload = report.to_dict()
    assert payload["delivery_status"] == "publishable"
    assert payload["publishable"] is True

    report.quality_gate = {
        "passes_gate": True,
        "metrics": {
            "delivery_mode": "demo",
            "delivery_publishable_mode": False,
            "diagnostic_only": True,
        },
    }

    payload = report.to_dict()
    assert payload["delivery_status"] == "diagnostic_only"
    assert payload["publishable"] is False
