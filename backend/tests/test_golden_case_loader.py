from __future__ import annotations

import json

from app.services.golden_case_loader import GoldenCaseLoader


def test_load_summary_detecta_mismatch_entre_manifesto_e_json(tmp_path):
    case_dir = tmp_path / "caso_ouro"
    case_dir.mkdir()
    manifesto = case_dir / "manifesto_pacote.md"
    manifesto.write_text(
        "# Manifesto\n\nTotal de documentos: 3\n\nEvidence manifesto text for fixture.",
        encoding="utf-8",
    )
    (case_dir / "documentos_principais.json").write_text(
        json.dumps(
            [
                {"id": "doc-1", "arquivo": "peticao.pdf"},
                {"id": "doc-2", "arquivo": "decisao.pdf"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (case_dir / "peticao.pdf").write_bytes(b"%PDF-1.4")
    (case_dir / "decisao.pdf").write_bytes(b"%PDF-1.4")
    (case_dir / "notas.md").write_text(
        "Texto de apoio para evidencias curtas.\n" * 8,
        encoding="utf-8",
    )
    (case_dir / "simulation_prompt.md").write_text(
        "Prompt de simulacao do caso.",
        encoding="utf-8",
    )
    (case_dir / "strategic_analysis.md").write_text(
        "Analise estrategica do caso.",
        encoding="utf-8",
    )

    loader = GoldenCaseLoader(case_dir)

    summary = loader.load_summary()

    assert summary["case_id"] == "caso_ouro"
    assert summary["manifesto_path"].endswith("manifesto_pacote.md")
    assert summary["declared_documents"] == 3
    assert summary["indexed_documents"] == 2
    assert summary["mismatch"] is True
    assert summary["pdf_count"] == 2
    assert summary["markdown_count"] == 4
    assert "manifesto_pacote.md" in summary["key_files"]
    assert "documentos_principais.json" in summary["key_files"]

    fixture = loader.build_quality_fixture()

    assert fixture["summary"] == summary
    assert fixture["evidence_texts"]
    assert fixture["simulation_prompt"] == "Prompt de simulacao do caso."
    assert fixture["strategic_analysis"] == "Analise estrategica do caso."


def test_load_summary_e_fixture_sao_defensivos_sem_arquivos(tmp_path):
    missing_dir = tmp_path / "caso_sem_arquivos"

    loader = GoldenCaseLoader(missing_dir)

    summary = loader.load_summary()
    fixture = loader.build_quality_fixture()

    assert summary == {
        "case_id": "caso_sem_arquivos",
        "manifesto_path": None,
        "declared_documents": None,
        "indexed_documents": None,
        "mismatch": False,
        "pdf_count": 0,
        "markdown_count": 0,
        "key_files": [],
    }
    assert fixture["summary"] == summary
    assert fixture["evidence_texts"] == []
    assert fixture["simulation_prompt"] is None
    assert fixture["strategic_analysis"] is None
