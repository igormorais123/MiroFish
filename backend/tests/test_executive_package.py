import json

import pytest

from app.services.executive_package import (
    ExecutivePackageConflict,
    ExecutivePackageInvalidPath,
    ExecutivePackageNotFound,
    allowed_executive_package_file_path,
    build_executive_package,
)
from app.services.report_agent import Report, ReportManager, ReportStatus


@pytest.fixture
def report_store(monkeypatch, tmp_path):
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(reports_dir))
    return reports_dir


def _report(report_id="report_1", *, publishable=True):
    return Report(
        report_id=report_id,
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        markdown_content="# Relatorio\n\nConteudo <script>alert(1)</script>",
        quality_gate={"passes_gate": publishable, "metrics": {"delivery_publishable_mode": True}},
        evidence_audit={"passes_gate": publishable, "quotes": []},
    )


def test_executive_package_blocks_missing_report(report_store):
    with pytest.raises(ExecutivePackageNotFound):
        build_executive_package("missing_report")


def test_executive_package_blocks_non_publishable_report(report_store):
    report = _report(publishable=False)
    ReportManager.save_report(report)

    with pytest.raises(ExecutivePackageConflict):
        build_executive_package(report.report_id)


def test_executive_package_creates_manifest_and_html(report_store):
    report = _report()
    ReportManager.save_report(report)
    ReportManager.save_json_artifact(report.report_id, "evidence_manifest.json", {"claims": []})
    ReportManager.save_json_artifact(report.report_id, "forecast_ledger.json", {"previsoes": []})

    manifest = build_executive_package(report.report_id)

    assert manifest["schema"] == "mirofish.executive_package_manifest.v1"
    assert manifest["report_id"] == report.report_id
    assert manifest["source_delivery_status"] == "publishable"
    assert "internal_path" not in manifest
    assert {"executive_summary.html", "evidence_annex.html"} <= {
        item["filename"] for item in manifest["files"]
    }
    assert "evidence_manifest.json" in manifest["artifact_inputs"]
    assert "forecast_ledger.json" in manifest["artifact_inputs"]

    package_dir = report_store / report.report_id / "executive_package"
    summary = (package_dir / "executive_summary.html").read_text(encoding="utf-8")
    annex = (package_dir / "evidence_annex.html").read_text(encoding="utf-8")
    saved_manifest = json.loads((package_dir / "executive_package_manifest.json").read_text(encoding="utf-8"))

    assert "<script>" not in summary
    assert "&lt;script&gt;" in summary
    assert "evidence_manifest.json" in annex
    assert saved_manifest["report_id"] == report.report_id
    manifest_file = next(
        item for item in saved_manifest["files"]
        if item["filename"] == "executive_package_manifest.json"
    )
    assert manifest_file["sha256"] is None
    assert manifest_file["hash_note"]
    assert ReportManager.load_json_artifact(report.report_id, "executive_package_manifest.json")["status"] == "created"


def test_executive_package_download_path_uses_manifest_allowlist(report_store):
    report = _report()
    ReportManager.save_report(report)
    build_executive_package(report.report_id)

    path = allowed_executive_package_file_path(report.report_id, "executive_summary.html")

    assert path.name == "executive_summary.html"
    assert path.is_file()


def test_executive_package_download_path_blocks_unlisted_file(report_store):
    report = _report()
    ReportManager.save_report(report)
    build_executive_package(report.report_id)

    with pytest.raises(ExecutivePackageInvalidPath):
        allowed_executive_package_file_path(report.report_id, "../meta.json")


def test_executive_package_api_returns_manifest(monkeypatch):
    from app import create_app
    import app.api.report as report_api

    monkeypatch.setattr(
        report_api,
        "build_executive_package",
        lambda report_id: {
            "schema": "mirofish.executive_package_manifest.v1",
            "report_id": report_id,
            "status": "created",
            "files": [],
        },
    )

    client = create_app().test_client()
    response = client.post("/api/report/report_1/executive-package")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["report_id"] == "report_1"


def test_executive_package_api_maps_conflict(monkeypatch):
    from app import create_app
    import app.api.report as report_api

    def raise_conflict(report_id):
        raise ExecutivePackageConflict("Pacote executivo exige relatorio publicavel")

    monkeypatch.setattr(report_api, "build_executive_package", raise_conflict)

    response = create_app().test_client().post("/api/report/report_1/executive-package")

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_executive_package_api_maps_missing_report(monkeypatch):
    from app import create_app
    import app.api.report as report_api

    def raise_missing(report_id):
        raise ExecutivePackageNotFound("Relatorio nao encontrado")

    monkeypatch.setattr(report_api, "build_executive_package", raise_missing)

    response = create_app().test_client().post("/api/report/missing/executive-package")

    assert response.status_code == 404
    assert response.get_json()["success"] is False


def test_executive_package_api_downloads_allowlisted_file(monkeypatch, tmp_path):
    from app import create_app
    import app.api.report as report_api

    package_file = tmp_path / "executive_summary.html"
    package_file.write_text("<html>ok</html>", encoding="utf-8")
    monkeypatch.setattr(
        report_api,
        "allowed_executive_package_file_path",
        lambda report_id, filename: package_file,
    )

    response = create_app().test_client().get("/api/report/report_1/executive-package/executive_summary.html")

    assert response.status_code == 200
    assert response.data == b"<html>ok</html>"


def test_executive_package_api_blocks_invalid_download(monkeypatch):
    from app import create_app
    import app.api.report as report_api

    def raise_invalid(report_id, filename):
        raise ExecutivePackageInvalidPath("Arquivo nao permitido")

    monkeypatch.setattr(report_api, "allowed_executive_package_file_path", raise_invalid)

    response = create_app().test_client().get("/api/report/report_1/executive-package/meta.json")

    assert response.status_code == 400
    assert response.get_json()["success"] is False
