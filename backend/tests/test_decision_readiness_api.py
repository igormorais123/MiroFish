from flask import Flask

from app.api import simulation as simulation_api


def test_get_simulation_readiness_returns_data(monkeypatch):
    app = Flask(__name__)
    captured = {}

    def fake_readiness(simulation_id, *, graph_id=None, delivery_mode=None):
        captured["simulation_id"] = simulation_id
        captured["graph_id"] = graph_id
        captured["delivery_mode"] = delivery_mode
        return {
            "simulation_id": simulation_id,
            "status": "ready_for_report",
            "next_action": "generate_report",
        }

    monkeypatch.setattr(simulation_api, "evaluate_decision_readiness", fake_readiness)

    with app.test_request_context("/api/simulation/sim_1/readiness?graph_id=g1&delivery_mode=client"):
        response, status_code = simulation_api.get_simulation_readiness("sim_1")

    payload = response.get_json()
    assert status_code == 200
    assert payload["success"] is True
    assert payload["data"]["next_action"] == "generate_report"
    assert captured == {
        "simulation_id": "sim_1",
        "graph_id": "g1",
        "delivery_mode": "client",
    }


def test_get_simulation_readiness_returns_404_for_missing(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        simulation_api,
        "evaluate_decision_readiness",
        lambda simulation_id, **kwargs: {"simulation_id": simulation_id, "status": "missing"},
    )

    with app.test_request_context("/api/simulation/sim_missing/readiness"):
        response, status_code = simulation_api.get_simulation_readiness("sim_missing")

    assert status_code == 404
    assert response.get_json()["success"] is False
