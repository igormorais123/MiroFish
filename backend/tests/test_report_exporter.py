import json
from pathlib import Path

import pytest

from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.report_exporter import (
    ReportExportConflict,
    allowed_export_file_path,
    create_report_export,
    list_report_exports,
)


def _publishable_report(report_id="report_1", markdown=None):
    return Report(
        report_id=report_id,
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        markdown_content=markdown or "# Relatorio\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1))",
        quality_gate={"passes_gate": True, "metrics": {}},
        evidence_audit={"passes_gate": True, "quotes": []},
    )


@pytest.fixture
def report_store(monkeypatch, tmp_path):
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(reports_dir))
    return reports_dir


def test_export_creates_draft_with_safe_html_and_manifest(report_store):
    report = _publishable_report()
    ReportManager.save_report(report)

    manifest = create_report_export(report.report_id)

    assert manifest["status"] == "draft"
    assert manifest["export_id"].startswith("export_")
    assert "internal_path" not in manifest
    filenames = {item["filename"] for item in manifest["files"]}
    assert {"full_report.html", "evidence_annex.html", "report_bundle_manifest.json"} <= filenames

    export_dir = report_store / report.report_id / "exports" / manifest["export_id"]
    full_html = (export_dir / "full_report.html").read_text(encoding="utf-8")
    assert "<script>" not in full_html
    assert "&lt;script&gt;" in full_html
    assert "javascript:alert" not in full_html

    bundle_manifest = json.loads((export_dir / "report_bundle_manifest.json").read_text(encoding="utf-8"))
    assert set(bundle_manifest["expected_files"]) == {
        "full_report.html",
        "evidence_annex.html",
        "export_manifest.json",
        "report_bundle_manifest.json",
    }
    assert bundle_manifest["renderer_metadata"]["full_report.html"]["renderer"] == "mirofish_safe_markdown"


def test_list_exports_does_not_expose_internal_path(report_store):
    report = _publishable_report()
    ReportManager.save_report(report)
    create_report_export(report.report_id)

    exports = list_report_exports(report.report_id)

    assert len(exports) == 1
    assert "internal_path" not in exports[0]


def test_export_blocks_unpublishable_report(report_store):
    report = _publishable_report()
    report.quality_gate = {"passes_gate": False, "metrics": {}}
    ReportManager.save_report(report)

    with pytest.raises(ReportExportConflict):
        create_report_export(report.report_id)


def test_download_path_uses_manifest_allowlist(report_store):
    report = _publishable_report()
    ReportManager.save_report(report)
    manifest = create_report_export(report.report_id)

    path = allowed_export_file_path(report.report_id, manifest["export_id"], "full_report.html")

    assert path.name == "full_report.html"
    assert path.is_file()
