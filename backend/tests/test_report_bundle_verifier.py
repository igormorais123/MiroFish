import json

import pytest

from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.report_bundle_verifier import verify_report_export_bundle
from app.services.report_exporter import create_report_export


def _publishable_report(report_id="report_1"):
    return Report(
        report_id=report_id,
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        markdown_content="# Relatorio\n\nConteudo final.",
        quality_gate={"passes_gate": True, "metrics": {}},
        evidence_audit={"passes_gate": True},
    )


def _decision_packet():
    return {
        "schema": "mirofish.decision_packet.v2",
        "conviction_operational": 0.78,
        "method_lock": {"status": "locked"},
        "scenarios": {
            "base": {"probability_percent": 64},
            "optimistic": {"probability_percent": 20},
            "contrary": {"probability_percent": 16},
        },
        "convergence": {"score_percent": 74},
        "red_team": {
            "opposing_thesis": "A tese adversaria ataca o sinal emergente.",
            "reversal_triggers": ["cenario contrario ganha forca"],
        },
    }


@pytest.fixture
def report_store(monkeypatch, tmp_path):
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(reports_dir))
    return reports_dir


def _create_export(report_store):
    report = _publishable_report()
    ReportManager.save_report(report)
    ReportManager.save_json_artifact(report.report_id, "decision_packet.json", _decision_packet())
    manifest = create_report_export(report.report_id)
    export_dir = report_store / report.report_id / "exports" / manifest["export_id"]
    return report, manifest, export_dir


def _load_bundle_manifest(export_dir):
    return json.loads((export_dir / "report_bundle_manifest.json").read_text(encoding="utf-8"))


def _write_bundle_manifest(export_dir, payload):
    (export_dir / "report_bundle_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_verifier_accepts_valid_export_bundle(report_store):
    report, manifest, _export_dir = _create_export(report_store)

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is True
    assert result["bundle_verified"] is True
    saved = ReportManager.load_json_artifact(report.report_id, "report_bundle_verification.json")
    assert saved["export_id"] == manifest["export_id"]


def test_verifier_writes_export_scoped_verification_and_is_idempotent(report_store):
    report, manifest, export_dir = _create_export(report_store)

    first = verify_report_export_bundle(report.report_id, manifest["export_id"])
    second = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert first["passes"] is True
    assert second["passes"] is True
    scoped = json.loads((export_dir / "report_bundle_verification.json").read_text(encoding="utf-8"))
    assert scoped["export_id"] == manifest["export_id"]


def test_verifier_rejects_absolute_path_in_manifest(report_store):
    report, manifest, export_dir = _create_export(report_store)
    bundle_manifest = _load_bundle_manifest(export_dir)
    bundle_manifest["expected_files"].append("C:\\temp\\leak.html")
    _write_bundle_manifest(export_dir, bundle_manifest)

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is False
    assert any(item["id"] == "manifest_paths_safe" and item["passes"] is False for item in result["checks"])


def test_verifier_rejects_parent_traversal_in_manifest(report_store):
    report, manifest, export_dir = _create_export(report_store)
    bundle_manifest = _load_bundle_manifest(export_dir)
    bundle_manifest["expected_files"].append("../leak.html")
    _write_bundle_manifest(export_dir, bundle_manifest)

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is False
    assert any(item["id"] == "manifest_paths_safe" and item["passes"] is False for item in result["checks"])


def test_verifier_rejects_unexpected_file(report_store):
    report, manifest, export_dir = _create_export(report_store)
    (export_dir / "extra.txt").write_text("unexpected", encoding="utf-8")

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is False
    assert any(item["id"] == "no_unexpected_files" and item["passes"] is False for item in result["checks"])


def test_verifier_rejects_hash_mismatch(report_store):
    report, manifest, export_dir = _create_export(report_store)
    (export_dir / "full_report.html").write_text("tampered", encoding="utf-8")

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is False
    assert any(item["id"] == "hashes_match" and item["passes"] is False for item in result["checks"])


def test_verifier_rejects_expected_file_without_manifest_hash(report_store):
    report, manifest, export_dir = _create_export(report_store)
    bundle_manifest = _load_bundle_manifest(export_dir)
    bundle_manifest["files"] = [
        item for item in bundle_manifest["files"]
        if item.get("filename") != "full_report.html"
    ]
    _write_bundle_manifest(export_dir, bundle_manifest)
    export_manifest = json.loads((export_dir / "export_manifest.json").read_text(encoding="utf-8"))
    export_manifest["files"] = [
        item for item in export_manifest["files"]
        if item.get("filename") != "full_report.html"
    ]
    (export_dir / "export_manifest.json").write_text(
        json.dumps(export_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is False
    assert any(item["id"] == "hashes_match" and item["passes"] is False for item in result["checks"])


def test_verifier_rejects_missing_renderer_metadata(report_store):
    report, manifest, export_dir = _create_export(report_store)
    bundle_manifest = _load_bundle_manifest(export_dir)
    bundle_manifest["renderer_metadata"].pop("full_report.html")
    _write_bundle_manifest(export_dir, bundle_manifest)

    result = verify_report_export_bundle(report.report_id, manifest["export_id"])

    assert result["passes"] is False
    assert any(item["id"] == "renderer_metadata_present" and item["passes"] is False for item in result["checks"])
