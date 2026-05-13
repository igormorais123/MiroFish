"""Testes do contrato interno do harness MiroFish para consumidores service-to-service."""
from __future__ import annotations

from flask import Flask

from app.api import internal as internal_api
from app.api import internal_bp
from app.config import Config
from app.services.report_agent import Report, ReportManager, ReportStatus


def _app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(internal_bp, url_prefix="/api/internal/v1")
    return app


def test_harness_evidence_bundle_exige_token(monkeypatch):
    monkeypatch.setattr(Config, "INTERNAL_API_TOKEN", "token-seguro")
    client = _app().test_client()

    response = client.get("/api/internal/v1/harness/evidence-bundles/sim_123")

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_harness_evidence_bundle_retorna_contrato_para_vox(monkeypatch):
    monkeypatch.setattr(Config, "INTERNAL_API_TOKEN", "token-seguro")

    report = Report(
        report_id="report_vox",
        simulation_id="sim_vox",
        graph_id="graph_vox",
        simulation_requirement="Avaliar aceitacao de proposta publica.",
        status=ReportStatus.COMPLETED,
        markdown_content="# Diagnostico\n\nA proposta mostra tracao entre agentes moderados.",
        quality_gate={"passes_gate": True, "metrics": {"delivery_publishable_mode": True}},
        evidence_audit={"passes_gate": True},
        completed_at="2026-05-13T10:00:00",
    )

    artifacts = [{"name": "forecast_ledger.json"}, {"name": "system_gate.json"}]
    payloads = {
        "forecast_ledger.json": {
            "previsoes": [
                {
                    "titulo": "Aderencia inicial",
                    "horizonte": "30 dias",
                    "probabilidade": 0.68,
                    "incerteza": "media",
                    "premissas": ["Base simulada consolidada"],
                    "status": "congelada",
                }
            ]
        },
        "system_gate.json": {"passes_gate": True},
    }

    monkeypatch.setattr(ReportManager, "get_report_by_simulation", lambda simulation_id: report)
    monkeypatch.setattr(ReportManager, "list_json_artifacts", lambda report_id: artifacts)
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda report_id, filename: payloads.get(filename),
    )

    client = _app().test_client()
    response = client.get(
        "/api/internal/v1/harness/evidence-bundles/sim_vox",
        headers={"X-Internal-Token": "token-seguro"},
        base_url="https://mirofish.inteia.test",
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["source"] == "mirofish"
    assert data["missionId"] == "sim_vox"
    assert data["generatedAt"].endswith("Z")
    assert data["evidence"][0]["sourceUri"] == "https://mirofish.inteia.test/api/report/report_vox"
    assert data["evidence"][0]["collectedAt"] == "2026-05-13T10:00:00Z"
    assert data["evidence"][0]["confidence"] >= 0.8
    assert data["forecasts"][0]["horizon"] == "30 dias"
    assert data["forecasts"][0]["probability"] == 0.68
    assert data["forecasts"][0]["uncertainty"] == 0.5
    assert data["graph"]["nodes"][0]["id"] == "sim_vox"
    assert "publishable" in data["limitations"][0]


def test_harness_evidence_bundle_404_sem_relatorio(monkeypatch):
    monkeypatch.setattr(Config, "INTERNAL_API_TOKEN", "token-seguro")
    monkeypatch.setattr(ReportManager, "get_report_by_simulation", lambda simulation_id: None)

    client = _app().test_client()
    response = client.get(
        "/api/internal/v1/harness/evidence-bundles/sim_ausente",
        headers={"X-Internal-Token": "token-seguro"},
    )

    data = response.get_json()
    assert response.status_code == 404
    assert data["success"] is False
    assert "sim_ausente" in data["error"]


def test_harness_runs_alias_dispara_pipeline_com_token(monkeypatch):
    monkeypatch.setattr(Config, "INTERNAL_API_TOKEN", "token-seguro")

    def fake_run_preset():
        from flask import jsonify

        return jsonify({"success": True, "data": {"task_id": "task_vox"}}), 202

    monkeypatch.setattr(internal_api, "run_preset", fake_run_preset)
    client = _app().test_client()

    response = client.post(
        "/api/internal/v1/harness/runs",
        headers={"X-Internal-Token": "token-seguro"},
        json={"name": "Pesquisa Vox", "preset": "smoke"},
    )

    data = response.get_json()
    assert response.status_code == 202
    assert data["success"] is True
    assert data["data"]["task_id"] == "task_vox"
