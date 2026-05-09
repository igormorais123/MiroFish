import json
from pathlib import Path

from flask import Flask

from app.api import report as report_api
from app.services.report_agent import Report, ReportManager, ReportOutline, ReportSection, ReportStatus


def _blocked_report(report_id="report_content_repair"):
    return Report(
        report_id=report_id,
        simulation_id="sim_repair",
        graph_id="graph_repair",
        simulation_requirement="teste de reparo",
        status=ReportStatus.COMPLETED,
        outline=ReportOutline(
            title="Relatorio",
            summary="Resumo: nao ha agentes ativos na base.",
            sections=[ReportSection(title="Analise Estrategica")],
        ),
        markdown_content="Resumo: nao ha agentes ativos na base.",
        quality_gate={"passes_gate": True, "metrics": {"delivery_publishable_mode": True}},
        evidence_audit={"passes_gate": True},
    )


def test_repair_report_content_limpa_contradicoes_e_desbloqueia(monkeypatch, tmp_path):
    from app.services.report_content_repair import repair_report_content

    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _blocked_report()
    ReportManager.save_report(report)
    ReportManager.save_json_artifact(
        report.report_id,
        "system_gate.json",
        {
            "passes_gate": True,
            "metrics": {
                "profiles_count": 5,
                "total_rounds": 72,
                "current_round": 72,
                "diversity": {"platform_counts": {"twitter": 10, "reddit": 10}},
            },
        },
    )

    section_text = "\n".join(
        [
            "## Analise Estrategica",
            "",
            "**Analise Estrategica**",
            "",
            "[Sugestao operacional] | **Base** | 45% | A demonstracao exige nova rodada. | Logs em 30 dias. |",
            "",
            "- [Fato] A base informada nao tem agentes, rodadas e plataformas conhecidos.",
            "",
            "> [Inferencia da simulacao] Veiculos de midia amplificam o primeiro enquadramento narrativo.",
            "> [Inferencia da simulacao] Veiculos de midia amplificam o primeiro enquadramento narrativo.",
            "> [Inferencia da simulacao] Veiculos de midia amplificam o primeiro enquadramento narrativo.",
            "",
            "## QC — Cobertura e Grounding",
            "- interno",
        ]
    )
    report_folder = Path(ReportManager._get_report_folder(report.report_id))
    (report_folder / "section_01.md").write_text(section_text, encoding="utf-8")

    result = repair_report_content(report.report_id)

    updated = ReportManager.get_report(report.report_id)
    artifact = ReportManager.load_json_artifact(report.report_id, "content_repair.json")
    consistency = ReportManager.load_json_artifact(report.report_id, "content_consistency.json")
    section_after = (report_folder / "section_01.md").read_text(encoding="utf-8")

    assert result["status"] == "repaired"
    assert result["after"]["passes_gate"] is True
    assert consistency["passes_gate"] is True
    assert artifact["changed"] is True
    assert "nao ha agentes ativos" not in updated.markdown_content
    assert "nao tem agentes" not in updated.markdown_content
    assert "## QC" not in updated.markdown_content
    assert "[Sugestao operacional] |" not in updated.markdown_content
    assert "| **Base** | 45%" in updated.markdown_content
    assert "**Analise Estrategica**" not in section_after
    assert section_after.count("Veiculos de midia amplificam") == 1
    assert (report_folder / "content_repair_backup.md").exists()


def test_repair_report_content_route_returns_payload(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(
        report_api,
        "repair_report_content",
        lambda report_id: {
            "report_id": report_id,
            "status": "repaired",
            "after": {"passes_gate": True},
        },
    )

    with app.test_request_context("/api/report/report_1/content/repair", method="POST"):
        response, status_code = report_api.repair_report_content_route("report_1")

    payload = response.get_json()
    assert status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == "repaired"
