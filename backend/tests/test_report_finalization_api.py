from flask import Flask

from app.api import report as report_api
from app.services.report_finalization import ReportFinalizationConflict, ReportFinalizationNotFound


def test_repair_report_finalization_endpoint_returns_data(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "repair_report_finalization",
        lambda report_id: {"report_id": report_id, "status": "repaired"},
    )

    with app.test_request_context("/api/report/report_1/finalization/repair", method="POST"):
        response, status_code = report_api.repair_report_finalization_route("report_1")

    payload = response.get_json()
    assert status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == "repaired"


def test_repair_report_finalization_endpoint_returns_409_while_generating(monkeypatch):
    app = Flask(__name__)

    def _raise_conflict(report_id):
        raise ReportFinalizationConflict("Relatorio ainda em geracao.")

    monkeypatch.setattr(report_api, "repair_report_finalization", _raise_conflict)

    with app.test_request_context("/api/report/report_1/finalization/repair", method="POST"):
        response, status_code = report_api.repair_report_finalization_route("report_1")

    assert status_code == 409
    assert response.get_json()["success"] is False


def test_repair_report_finalization_endpoint_returns_404_for_missing_report(monkeypatch):
    app = Flask(__name__)

    def _raise_not_found(report_id):
        raise ReportFinalizationNotFound(f"Relatorio nao encontrado: {report_id}")

    monkeypatch.setattr(report_api, "repair_report_finalization", _raise_not_found)

    with app.test_request_context("/api/report/report_missing/finalization/repair", method="POST"):
        response, status_code = report_api.repair_report_finalization_route("report_missing")

    assert status_code == 404
    assert response.get_json()["success"] is False
