from flask import Flask

from app.api import report as report_api
from app.services.report_bundle_verifier import ReportBundleVerificationNotFound
from app.services.report_exporter import ReportExportConflict, ReportExportInvalidPath, ReportExportNotFound


def test_create_export_endpoint_returns_manifest_without_internal_path(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "create_report_export",
        lambda report_id: {"report_id": report_id, "export_id": "export_1", "status": "draft"},
    )

    with app.test_request_context("/api/report/report_1/exports", method="POST"):
        response, status_code = report_api.create_report_export_route("report_1")

    payload = response.get_json()
    assert status_code == 201
    assert payload["success"] is True
    assert "internal_path" not in payload["data"]


def test_create_export_endpoint_returns_404_for_missing_report(monkeypatch):
    app = Flask(__name__)

    def _raise_not_found(report_id):
        raise ReportExportNotFound(f"Relatorio nao encontrado: {report_id}")

    monkeypatch.setattr(report_api, "create_report_export", _raise_not_found)

    with app.test_request_context("/api/report/report_missing/exports", method="POST"):
        response, status_code = report_api.create_report_export_route("report_missing")

    assert status_code == 404
    assert response.get_json()["success"] is False


def test_create_export_endpoint_returns_409_for_blocked_report(monkeypatch):
    app = Flask(__name__)

    def _raise_conflict(report_id):
        raise ReportExportConflict("Checklist metodologico bloqueou a exportacao.")

    monkeypatch.setattr(report_api, "create_report_export", _raise_conflict)

    with app.test_request_context("/api/report/report_1/exports", method="POST"):
        response, status_code = report_api.create_report_export_route("report_1")

    assert status_code == 409
    assert response.get_json()["success"] is False


def test_list_exports_endpoint_does_not_expose_internal_path(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "list_report_exports",
        lambda report_id: [{"report_id": report_id, "export_id": "export_1", "status": "draft"}],
    )

    with app.test_request_context("/api/report/report_1/exports"):
        response, status_code = report_api.list_report_exports_route("report_1")

    payload = response.get_json()
    assert status_code == 200
    assert "internal_path" not in payload["data"]["exports"][0]


def test_download_export_rejects_traversal(monkeypatch):
    app = Flask(__name__)

    def _raise_invalid(report_id, export_id, filename):
        raise ReportExportInvalidPath(f"Arquivo nao permitido: {filename}")

    monkeypatch.setattr(report_api, "allowed_export_file_path", _raise_invalid)

    with app.test_request_context("/api/report/report_1/exports/export_1/../meta.json"):
        response, status_code = report_api.download_report_export_file_route(
            "report_1",
            "export_1",
            "../meta.json",
        )

    assert status_code == 400
    assert response.get_json()["success"] is False


def test_verify_export_bundle_endpoint_happy_path(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "verify_report_export_bundle",
        lambda report_id, export_id: {"report_id": report_id, "export_id": export_id, "passes": True},
    )

    with app.test_request_context("/api/report/report_1/exports/export_1/bundle/verify", method="POST"):
        response, status_code = report_api.verify_report_export_bundle_route("report_1", "export_1")

    payload = response.get_json()
    assert status_code == 200
    assert payload["success"] is True
    assert payload["data"]["passes"] is True


def test_verify_export_bundle_endpoint_returns_404(monkeypatch):
    app = Flask(__name__)

    def _raise_not_found(report_id, export_id):
        raise ReportBundleVerificationNotFound(f"Exportacao nao encontrada: {export_id}")

    monkeypatch.setattr(report_api, "verify_report_export_bundle", _raise_not_found)

    with app.test_request_context("/api/report/report_1/exports/export_missing/bundle/verify", method="POST"):
        response, status_code = report_api.verify_report_export_bundle_route("report_1", "export_missing")

    assert status_code == 404
    assert response.get_json()["success"] is False
