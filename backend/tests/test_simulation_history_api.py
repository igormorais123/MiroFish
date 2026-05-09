from __future__ import annotations

import json
import os

from flask import Flask

from app.api import simulation as simulation_api
from app.services.simulation_manager import SimulationState, SimulationStatus


class _Project:
    files = [{"filename": "contexto.pdf"}, {"filename": "briefing.md"}]


def _state(simulation_id: str = "sim_fast") -> SimulationState:
    state = SimulationState(
        simulation_id=simulation_id,
        project_id="proj_fast",
        graph_id="graph_fast",
        status=SimulationStatus.READY,
    )
    state.current_round = 3
    state.entities_count = 12
    state.profiles_count = 12
    state.entity_types = ["Pessoa", "OrgaoRegulador"]
    return state


def test_history_limit_1_usa_modo_leve_por_padrao(monkeypatch):
    app = Flask(__name__)
    runtime_called = False
    reports_called = False

    class FakeManager:
        def list_simulations(self, limit=20):
            assert limit == 1
            return [_state()]

        def get_simulation_config(self, simulation_id):
            return {
                "simulation_requirement": "Avaliar reacao publica.",
                "time_config": {
                    "total_simulation_hours": 2,
                    "minutes_per_round": 30,
                },
            }

    def fail_runtime(simulation_id):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime reconciliation should be skipped")

    def fail_report_index():
        nonlocal reports_called
        reports_called = True
        raise AssertionError("report scan should be skipped")

    monkeypatch.setattr(simulation_api, "SimulationManager", FakeManager)
    monkeypatch.setattr(simulation_api.SimulationRunner, "get_run_state", fail_runtime)
    monkeypatch.setattr(simulation_api.ProjectManager, "get_project", lambda project_id: _Project())
    monkeypatch.setattr(simulation_api, "_build_latest_report_index", fail_report_index)

    with app.test_request_context("/api/simulation/history?limit=1", method="GET"):
        response = simulation_api.get_simulation_history()

    payload = response.get_json()
    item = payload["data"][0]

    assert payload["success"] is True
    assert payload["meta"]["include_reports"] is False
    assert payload["meta"]["include_runtime"] is False
    assert item["report_id"] is None
    assert item["current_round"] == 3
    assert item["runner_status"] == "ready"
    assert runtime_called is False
    assert reports_called is False


def test_build_latest_report_index_preserva_report_mais_recente(monkeypatch, tmp_path):
    reports_dir = tmp_path / "reports"
    old_report = reports_dir / "report_old"
    new_report = reports_dir / "report_new"
    other_report = reports_dir / "report_other"
    old_report.mkdir(parents=True)
    new_report.mkdir()
    other_report.mkdir()

    (old_report / "meta.json").write_text(
        json.dumps({"simulation_id": "sim_1", "report_id": "report_old"}),
        encoding="utf-8",
    )
    (new_report / "meta.json").write_text(
        json.dumps({"simulation_id": "sim_1", "report_id": "report_new"}),
        encoding="utf-8",
    )
    (other_report / "meta.json").write_text(
        json.dumps({"simulation_id": "sim_2", "report_id": "report_other"}),
        encoding="utf-8",
    )
    os.utime(old_report / "meta.json", (10, 10))
    os.utime(new_report / "meta.json", (20, 20))
    os.utime(other_report / "meta.json", (15, 15))

    monkeypatch.setattr(simulation_api, "_reports_dir", lambda: str(reports_dir))

    report_index = simulation_api._build_latest_report_index()

    assert report_index["sim_1"] == "report_new"
    assert report_index["sim_2"] == "report_other"
