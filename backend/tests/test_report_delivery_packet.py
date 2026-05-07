from app.services.report_agent import Report, ReportStatus
from app.services.report_delivery_packet import build_report_delivery_packet


def _publishable_report():
    return Report(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        quality_gate={"passes_gate": True, "metrics": {}},
        evidence_audit={"passes_gate": True},
    )


def test_delivery_packet_missing_report(monkeypatch):
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.get_report", lambda report_id: None)

    packet = build_report_delivery_packet("report_missing")

    assert packet["status"] == "missing"
    assert packet["client_deliverable"] is False
    assert packet["blockers"]


def test_delivery_packet_publishable_is_not_client_deliverable_without_bundle(monkeypatch):
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.get_report", lambda report_id: _publishable_report())
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.list_json_artifacts", lambda report_id: [])
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.load_json_artifact", lambda report_id, filename: None)
    monkeypatch.setattr(
        "app.services.report_delivery_packet.evaluate_report_method_checklist",
        lambda report_id: {"hard_checks_pass": True, "hard_blockers": [], "warnings": []},
    )

    packet = build_report_delivery_packet("report_1")

    assert packet["status"] == "ready_for_export"
    assert packet["report_publishable"] is True
    assert packet["bundle_verified"] is False
    assert packet["client_deliverable"] is False
    assert packet["next_action"] == "generate_export_bundle"


def test_delivery_packet_client_deliverable_requires_verified_bundle(monkeypatch):
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.get_report", lambda report_id: _publishable_report())
    monkeypatch.setattr(
        "app.services.report_delivery_packet.ReportManager.list_json_artifacts",
        lambda report_id: [{"name": "report_bundle_verification.json"}],
    )
    monkeypatch.setattr(
        "app.services.report_delivery_packet.ReportManager.load_json_artifact",
        lambda report_id, filename: {"passes": True, "checks": []},
    )
    monkeypatch.setattr(
        "app.services.report_delivery_packet.evaluate_report_method_checklist",
        lambda report_id: {"hard_checks_pass": True, "hard_blockers": [], "warnings": []},
    )

    packet = build_report_delivery_packet("report_1")

    assert packet["status"] == "client_deliverable"
    assert packet["bundle_verified"] is True
    assert packet["client_deliverable"] is True


def test_delivery_packet_diagnostic_report_never_client_deliverable(monkeypatch):
    report = _publishable_report()
    report.quality_gate = {
        "passes_gate": True,
        "metrics": {"delivery_publishable_mode": False, "diagnostic_only": True},
    }
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.get_report", lambda report_id: report)
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.list_json_artifacts", lambda report_id: [])
    monkeypatch.setattr(
        "app.services.report_delivery_packet.ReportManager.load_json_artifact",
        lambda report_id, filename: {"passes": True},
    )
    monkeypatch.setattr(
        "app.services.report_delivery_packet.evaluate_report_method_checklist",
        lambda report_id: {"hard_checks_pass": True, "hard_blockers": [], "warnings": []},
    )

    packet = build_report_delivery_packet("report_1")

    assert packet["status"] == "diagnostic_only"
    assert packet["report_publishable"] is False
    assert packet["client_deliverable"] is False
    assert packet["warnings"]


def test_delivery_packet_client_deliverable_requires_method_checklist(monkeypatch):
    monkeypatch.setattr("app.services.report_delivery_packet.ReportManager.get_report", lambda report_id: _publishable_report())
    monkeypatch.setattr(
        "app.services.report_delivery_packet.ReportManager.list_json_artifacts",
        lambda report_id: [{"name": "report_bundle_verification.json"}],
    )
    monkeypatch.setattr(
        "app.services.report_delivery_packet.ReportManager.load_json_artifact",
        lambda report_id, filename: {"passes": True, "checks": []},
    )
    monkeypatch.setattr(
        "app.services.report_delivery_packet.evaluate_report_method_checklist",
        lambda report_id: {
            "hard_checks_pass": False,
            "hard_blockers": [{"id": "full_report_present", "message": "full_report.md ausente ou vazio."}],
            "warnings": [],
        },
    )

    packet = build_report_delivery_packet("report_1")

    assert packet["status"] == "blocked"
    assert packet["method_checks_pass"] is False
    assert packet["client_deliverable"] is False
    assert "full_report.md ausente ou vazio." in packet["blockers"]
