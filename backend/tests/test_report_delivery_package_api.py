from flask import Flask

from app.api import report as report_api


def test_get_report_delivery_package_returns_packet(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "build_report_delivery_packet",
        lambda report_id: {
            "report_id": report_id,
            "status": "ready_for_export",
            "client_deliverable": False,
        },
    )

    with app.test_request_context("/api/report/report_1/delivery-package"):
        response, status_code = report_api.get_report_delivery_package("report_1")

    payload = response.get_json()
    assert status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_for_export"


def test_get_report_delivery_package_returns_404_for_missing(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "build_report_delivery_packet",
        lambda report_id: {"report_id": report_id, "status": "missing"},
    )

    with app.test_request_context("/api/report/report_missing/delivery-package"):
        response, status_code = report_api.get_report_delivery_package("report_missing")

    assert status_code == 404
    assert response.get_json()["success"] is False
