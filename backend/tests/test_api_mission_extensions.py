"""Testes diretos das rotas de missao, poderes e pacote final."""
from __future__ import annotations

from flask import Flask

from app.api import report as report_api
from app.api import simulation as simulation_api
from app.services.report_agent import Report, ReportManager, ReportStatus


def test_get_mission_bundle_gera_e_salva_manifesto(monkeypatch):
    app = Flask(__name__)
    saved = {}
    artifacts = [{"name": "cost_meter.json"}, {"name": "forecast_ledger.json"}]
    payloads = {
        "mission_bundle.json": None,
        "cost_meter.json": {"inteia_value_brl": 1200},
        "power_selection.json": {"poderes_selecionados": [{"id": "modo_rapido", "nome": "Modo Rápido"}]},
        "power_persona_context.json": {"items": [{"id": "persona_1", "nome": "Persona 1"}]},
        "forecast_ledger.json": {"previsoes": [{"titulo": "Cenario A", "status": "congelada"}]},
    }
    report = Report(
        report_id="report_api_bundle",
        simulation_id="sim_api_bundle",
        graph_id="graph_api_bundle",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
    )

    monkeypatch.setattr(ReportManager, "get_report", lambda report_id: report)
    monkeypatch.setattr(ReportManager, "list_json_artifacts", lambda report_id: artifacts)
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda report_id, filename: payloads.get(filename),
    )
    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved.__setitem__((report_id, filename), payload),
    )

    with app.test_request_context("/api/report/report_api_bundle/mission-bundle"):
        response = report_api.get_mission_bundle("report_api_bundle")

    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["report_id"] == "report_api_bundle"
    assert data["data"]["poderes_mobilizados"][0]["nome"] == "Modo Rápido"
    assert data["data"]["previsoes_congeladas"][0]["titulo"] == "Cenario A"
    assert saved[("report_api_bundle", "mission_bundle.json")] == data["data"]


def test_get_mission_bundle_retorna_existente_sem_regravar(monkeypatch):
    app = Flask(__name__)
    saved = {}
    existing = {"report_id": "report_api_bundle_ready", "hashes": {"manifesto": "abc"}}
    report = Report(
        report_id="report_api_bundle_ready",
        simulation_id="sim_api_bundle_ready",
        graph_id="graph_api_bundle_ready",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
    )

    monkeypatch.setattr(ReportManager, "get_report", lambda report_id: report)
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda report_id, filename: existing if filename == "mission_bundle.json" else None,
    )
    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved.__setitem__((report_id, filename), payload),
    )

    with app.test_request_context("/api/report/report_api_bundle_ready/mission-bundle"):
        response = report_api.get_mission_bundle("report_api_bundle_ready")

    data = response.get_json()
    assert data["success"] is True
    assert data["data"] == existing
    assert saved == {}


def test_get_mission_bundle_aguarda_arquivos_essenciais(monkeypatch):
    app = Flask(__name__)
    saved = {}
    report = Report(
        report_id="report_api_bundle_missing",
        simulation_id="sim_api_bundle_missing",
        graph_id="graph_api_bundle_missing",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
    )

    monkeypatch.setattr(ReportManager, "get_report", lambda report_id: report)
    monkeypatch.setattr(ReportManager, "list_json_artifacts", lambda report_id: [])
    monkeypatch.setattr(ReportManager, "load_json_artifact", lambda report_id, filename: None)
    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved.__setitem__((report_id, filename), payload),
    )

    with app.test_request_context("/api/report/report_api_bundle_missing/mission-bundle"):
        response, status_code = report_api.get_mission_bundle("report_api_bundle_missing")

    data = response.get_json()
    assert status_code == 409
    assert data["success"] is False
    assert "cost_meter.json" in data["data"]["arquivos_pendentes"]
    assert saved == {}


def test_get_mission_bundle_aguarda_relatorio_concluido(monkeypatch):
    app = Flask(__name__)
    saved = {}
    report = Report(
        report_id="report_api_bundle_wait",
        simulation_id="sim_api_bundle_wait",
        graph_id="graph_api_bundle_wait",
        simulation_requirement="teste",
        status=ReportStatus.GENERATING,
    )

    monkeypatch.setattr(ReportManager, "get_report", lambda report_id: report)
    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved.__setitem__((report_id, filename), payload),
    )

    with app.test_request_context("/api/report/report_api_bundle_wait/mission-bundle"):
        response, status_code = report_api.get_mission_bundle("report_api_bundle_wait")

    data = response.get_json()
    assert status_code == 409
    assert data["success"] is False
    assert data["data"]["status"] == "generating"
    assert saved == {}


def test_get_mission_bundle_retorna_404_quando_relatorio_nao_existe(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(ReportManager, "get_report", lambda report_id: None)

    with app.test_request_context("/api/report/report_ausente/mission-bundle"):
        response, status_code = report_api.get_mission_bundle("report_ausente")

    assert status_code == 404
    assert response.get_json()["success"] is False


def test_save_mission_selection_rota_salva_payload(monkeypatch):
    app = Flask(__name__)
    saved = {}

    class FakeState:
        project_id = "proj_1"

    class FakeSimulationManager:
        def get_simulation(self, simulation_id):
            return FakeState()

    class FakeMissionSelection:
        def save(self, simulation_id, payload):
            saved["simulation_id"] = simulation_id
            saved["payload"] = payload
            return {
                "simulation_id": simulation_id,
                "selected_power_ids": payload.get("selected_power_ids", []),
                "selected_power_persona_ids": payload.get("selected_power_persona_ids", []),
            }

    monkeypatch.setattr(simulation_api, "SimulationManager", FakeSimulationManager)
    monkeypatch.setattr(simulation_api, "MissionSelection", FakeMissionSelection)

    with app.test_request_context(
        "/api/simulation/sim_1/mission-selection",
        method="POST",
        json={
            "selected_power_ids": ["modo_rapido"],
            "selected_power_persona_ids": ["persona_1"],
        },
    ):
        response = simulation_api.save_mission_selection("sim_1")

    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["selected_power_ids"] == ["modo_rapido"]
    assert saved["simulation_id"] == "sim_1"
    assert saved["payload"]["simulation_id"] == "sim_1"
