import json
from pathlib import Path

from flask import Flask

from app.api import report as report_api
from app.services.report_agent import Report, ReportManager, ReportStatus


def _publishable_report(report_id="report_ready"):
    return Report(
        report_id=report_id,
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste evolutivo",
        status=ReportStatus.COMPLETED,
        markdown_content="# Relatorio",
        quality_gate={"passes_gate": True, "metrics": {"delivery_publishable_mode": True}},
        evidence_audit={"passes_gate": True},
    )


def test_report_evolution_readiness_libera_deepresearch_e_ralph_run(monkeypatch, tmp_path):
    from app.services.report_evolution_readiness import build_report_evolution_readiness

    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _publishable_report()
    ReportManager.save_report(report)
    ReportManager.save_json_artifact(
        report.report_id,
        "system_gate.json",
        {
            "passes_gate": True,
            "metrics": {
                "graph_nodes_count": 5,
                "graph_edges_count": 5,
                "total_rounds": 72,
                "current_round": 72,
                "total_actions_count": 20,
            },
        },
    )
    ReportManager.save_json_artifact(report.report_id, "evidence_audit.json", {"passes_gate": True})
    run_dir = Path(ReportManager._get_report_folder(report.report_id)) / "evolution_runs" / "run_1"
    run_dir.mkdir(parents=True)
    (run_dir / "METRICS.json").write_text(
        json.dumps({"status": "done", "autoresearch": {"method_signal": "none"}}),
        encoding="utf-8",
    )

    readiness = build_report_evolution_readiness(report.report_id)

    assert readiness["status"] == "ready_for_evolution"
    assert readiness["can_deep_research"] is True
    assert readiness["can_create_ralph_run"] is True
    assert readiness["next_action"] == "run_deep_research"
    assert readiness["metrics"]["graph_nodes_count"] == 5
    assert readiness["evolution_runs_count"] == 1
    assert "quick_search" in readiness["recommended_tools"]


def test_report_evolution_readiness_bloqueia_relatorio_nao_publicavel(monkeypatch, tmp_path):
    from app.services.report_evolution_readiness import build_report_evolution_readiness

    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _publishable_report(report_id="report_blocked")
    report.evidence_audit = {"passes_gate": False, "unsupported_numbers": [{"number": "85%"}]}
    ReportManager.save_report(report)

    readiness = build_report_evolution_readiness(report.report_id)

    assert readiness["status"] == "blocked"
    assert readiness["can_deep_research"] is False
    assert readiness["can_create_ralph_run"] is False
    assert readiness["next_action"] == "repair_report"
    assert readiness["blockers"]


def test_report_evolution_readiness_bloqueia_inconsistencia_de_conteudo(monkeypatch, tmp_path):
    from app.services.report_evolution_readiness import build_report_evolution_readiness

    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _publishable_report(report_id="report_content_blocked")
    report.markdown_content = "Resumo: nao ha agentes ativos na base."
    ReportManager.save_report(report)
    ReportManager.save_json_artifact(
        report.report_id,
        "system_gate.json",
        {
            "passes_gate": True,
            "metrics": {
                "profiles_count": 5,
                "total_rounds": 72,
                "diversity": {"platform_counts": {"twitter": 10, "reddit": 10}},
            },
        },
    )

    readiness = build_report_evolution_readiness(report.report_id)

    assert readiness["status"] == "blocked"
    assert readiness["can_deep_research"] is False
    assert readiness["next_action"] == "repair_report"
    assert readiness["content_consistency"]["passes_gate"] is False
    assert any("conteudo" in blocker.lower() for blocker in readiness["blockers"])


def test_get_report_evolution_readiness_route_returns_data(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "build_report_evolution_readiness",
        lambda report_id: {
            "report_id": report_id,
            "status": "ready_for_evolution",
            "next_action": "run_deep_research",
        },
    )

    with app.test_request_context("/api/report/report_1/evolution-readiness"):
        response, status_code = report_api.get_report_evolution_readiness("report_1")

    payload = response.get_json()
    assert status_code == 200
    assert payload["success"] is True
    assert payload["data"]["next_action"] == "run_deep_research"


def test_get_report_evolution_readiness_route_returns_404_for_missing(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "build_report_evolution_readiness",
        lambda report_id: {"report_id": report_id, "status": "missing"},
    )

    with app.test_request_context("/api/report/report_missing/evolution-readiness"):
        response, status_code = report_api.get_report_evolution_readiness("report_missing")

    assert status_code == 404
    assert response.get_json()["success"] is False
