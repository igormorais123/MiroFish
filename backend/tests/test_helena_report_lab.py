import json

from app.services.helena_report_lab import HELENA_REPORT_THEMES, build_helena_report_lab


def test_helena_report_lab_generates_ten_safe_html_reports(tmp_path):
    manifest = build_helena_report_lab(tmp_path)

    assert manifest["schema"] == "mirofish.helena_report_lab.v1"
    assert manifest["reports_count"] == 10
    assert manifest["passes"] is True
    assert len(manifest["reports"]) == len(HELENA_REPORT_THEMES)
    assert (tmp_path / "index.html").is_file()
    assert (tmp_path / "validation_manifest.json").is_file()

    for report in manifest["reports"]:
        path = tmp_path / report["filename"]
        html = path.read_text(encoding="utf-8")
        assert path.is_file()
        assert "RELATÓRIO DE INTELIGÊNCIA | INTEIA" in html
        assert "Confiança" in html
        assert "Red Team" in html
        assert "<script" not in html.lower()
        assert "javascript:" not in html.lower()
        assert len(report["screenshots_expected"]) == 3
        assert all(check["passes"] is True for check in report["checks"])


def test_helena_report_lab_manifest_matches_disk(tmp_path):
    manifest = build_helena_report_lab(tmp_path)
    saved = json.loads((tmp_path / "validation_manifest.json").read_text(encoding="utf-8"))

    assert saved["reports_count"] == manifest["reports_count"]
    assert saved["oracle_verdict"] == "approved"
    assert saved["index"]["filename"] == "index.html"
    assert saved["index"]["sha256"] == manifest["index"]["sha256"]
