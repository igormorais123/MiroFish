"""Testes do contrato interno do harness MiroFish para consumidores service-to-service."""
from __future__ import annotations

from flask import Flask

from app.api import internal as internal_api
from app.api import internal_bp
from app.config import Config
from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.harness_evidence_bundle import _build_methodology


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

    artifacts = [
        {"name": "forecast_ledger.json"},
        {"name": "system_gate.json"},
        {"name": "methodology_manifest.json"},
        {"name": "baseline_registry.json"},
        {"name": "harness_science_gate.json"},
    ]
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
        "methodology_manifest.json": {
            "population": "Servidores publicos federais ativos",
            "calibration_mode": "public_data_and_existing_assets",
        },
        "baseline_registry.json": {
            "anchors": [
                {"name": "PEP/MGI"},
                {"name": "Pesquisa Vozes/MGI-Enap"},
            ]
        },
        "harness_science_gate.json": {"passes_gate": True},
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
    assert data["methodology"]["contractVersion"] == "mirofish.vox_science.v1"
    assert data["methodology"]["readiness"] == "blocked"
    assert data["methodology"]["calibrationMode"] == "unverified_no_calibration"
    assert data["methodology"]["claimLevel"] is None
    assert data["methodology"]["newHumanCollection"] is None
    assert data["methodology"]["population"] is None
    assert data["methodology"]["publicDataAnchors"] == []
    assert data["methodology"]["robustness"] is None
    assert data["qualityGates"][0]["status"] == "review"
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


def test_public_methodology_never_falls_back_to_raw_unverified_calibration():
    projection = {
        "verified": False,
        "verification_status": "unverified",
        "passes_execution_gate": False,
        "claim_level": None,
        "calibration_mode": "unverified_no_calibration",
        "calibration_evidence": None,
        "new_human_collection": None,
    }
    raw = {
        "methodology_manifest.json": {"population": "forged population"},
        "baseline_registry.json": {"anchors": [{"name": "forged anchor"}]},
        "fidelity_report.json": {"overall_score": 1.0},
        "harness_science_gate.json": {"passes_execution_gate": True},
    }

    methodology = _build_methodology(list(raw), raw, projection)

    assert methodology["mode"] == "public_data_grounded_synthetic_harness"
    assert methodology["calibrationMode"] == "unverified_no_calibration"
    assert methodology["authority"]["status"] == "diagnostic_only"
    assert methodology["population"] is None
    assert methodology["publicDataAnchors"] == []
    assert methodology["robustness"] is None


def test_public_methodology_distinguishes_verified_c0_c1_and_c2_plus():
    base = {
        "verified": True,
        "verification_status": "verified",
        "new_human_collection": False,
    }
    cases = [
        ({**base, "passes_execution_gate": False, "claim_level": "C0", "calibration_mode": "unverified_no_calibration", "calibration_evidence": None}, "unverified_no_calibration", "C0"),
        ({**base, "passes_execution_gate": True, "claim_level": "C1", "calibration_mode": "synthetic_trace_only", "calibration_evidence": None}, "synthetic_trace_only", "C1"),
        ({**base, "passes_execution_gate": True, "claim_level": "C2", "calibration_mode": "materialized_external_baseline", "calibration_evidence": {"baseline_snapshot_sha256": "a" * 64}}, "materialized_external_baseline", "C2"),
    ]

    for projection, mode, level in cases:
        methodology = _build_methodology([], {}, projection)
        assert methodology["mode"] == "public_data_grounded_synthetic_harness"
        assert methodology["calibrationMode"] == mode
        assert methodology["claimLevel"] == level
        assert methodology["authority"]["status"] == "server_verified"


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
