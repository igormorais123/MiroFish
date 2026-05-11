from pathlib import Path

from app.services.report_agent import ReportManager, ReportOutline, ReportSection
from app.services.report_diagrams import (
    DIAGRAM_SECTION_TITLE,
    MIN_REPORT_DIAGRAMS,
    count_report_diagrams,
    paperbanana_diagram_metadata,
)


def test_assemble_full_report_appends_paperbanana_diagram_section(monkeypatch, tmp_path):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report_id = "report_diagrams"
    outline = ReportOutline(
        title="Relatorio de teste",
        summary="Resumo da simulacao",
        sections=[ReportSection(title="Resumo executivo", content="")],
    )

    ReportManager.save_section(
        report_id,
        1,
        ReportSection(title="Resumo executivo", content="[Simulacao] Conteudo sem diagrama."),
    )

    content = ReportManager.assemble_full_report(report_id, outline)

    assert f"## {DIAGRAM_SECTION_TITLE}" in content
    assert count_report_diagrams(content) >= MIN_REPORT_DIAGRAMS

    diagram_section_path = Path(ReportManager._get_section_path(report_id, 2))
    assert diagram_section_path.exists()
    assert DIAGRAM_SECTION_TITLE in diagram_section_path.read_text(encoding="utf-8")


def test_paperbanana_diagram_metadata_reports_minimum():
    markdown = "\n\n".join(
        [
            "```mermaid\nflowchart LR\nA-->B\n```",
            "```mermaid\nflowchart TD\nC-->D\n```",
            "```mermaid\nflowchart LR\nE-->F\n```",
        ]
    )

    metadata = paperbanana_diagram_metadata(markdown)

    assert metadata["diagram_count"] == MIN_REPORT_DIAGRAMS
    assert metadata["passes_minimum"] is True
