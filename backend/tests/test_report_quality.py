"""Testes de unidade para app.utils.report_quality (Phase 3)."""
from __future__ import annotations

import pytest

from app.utils.report_quality import (
    evaluate_section_grounding,
    jaccard_similarity,
    measure_overlap,
    render_qc_block,
)


def test_jaccard_disjoint_returns_zero():
    a = "Igor advogado Brasilia trabalha SEEDF"
    b = "Sergipe mar dunas Aracaju capital Nordeste"
    assert jaccard_similarity(a, b, ngram=5) == 0.0


def test_jaccard_identical_returns_one():
    text = "Igor advogado Brasilia trabalha SEEDF doutorando IDP fundador INTEIA Colmeia"
    assert jaccard_similarity(text, text, ngram=5) == pytest.approx(1.0)


def test_jaccard_normaliza_acentos():
    """NFKD garante que palavras com/sem acento batem."""
    a = "Brasilia capital federal politica nacional saude educacao"
    b = "Brasília capital federal política nacional saúde educação"
    score = jaccard_similarity(a, b, ngram=3)
    assert score > 0.5, f"esperado > 0.5, obtido {score}"


def test_jaccard_short_text_returns_zero():
    """Texto curto demais para n-grama pedido retorna 0."""
    assert jaccard_similarity("oi tudo bem", "oi tudo bem", ngram=10) == 0.0


def test_measure_overlap_alert_dispara_acima_threshold():
    text = "Igor advogado Brasilia trabalha SEEDF doutorando IDP fundador INTEIA Colmeia"
    o = measure_overlap(text, text, threshold=0.30)
    assert o["alert"] is True
    assert o["jaccard_5gram"] > 0.30


def test_measure_overlap_alert_nao_dispara_em_textos_diferentes():
    o = measure_overlap("Igor advogado Brasilia trabalha SEEDF", "Sergipe mar dunas", threshold=0.30)
    assert o["alert"] is False
    assert o["jaccard_5gram"] == 0.0


def test_grounding_aprova_secao_com_numero_quote_entidade():
    content = 'Em 2024, 35% dos eleitores apoiaram Ibaneis. "Vai ganhar de novo" disse o analista.'
    result = evaluate_section_grounding(content, known_entities=["Ibaneis", "Leandro Grass"])
    assert result["passes_gate"] is True
    assert result["has_number"] is True
    assert result["has_quote"] is True
    assert result["entity_hits"] == 1


def test_grounding_rejeita_secao_narrativa_generica():
    content = "Os agentes podem reagir de varias formas no cenario simulado, dependendo do contexto."
    result = evaluate_section_grounding(content, [])
    assert result["passes_gate"] is False
    assert result["score"] == 0.0


def test_grounding_aprova_so_com_numero_e_entidade():
    """Secao sem aspas mas com numero (0.4) + 2 entidades (0.2) = 0.6 -> passa."""
    content = "Em 2024, Ibaneis perdeu apoio para Leandro Grass na pesquisa."
    result = evaluate_section_grounding(content, ["Ibaneis", "Leandro Grass"])
    assert result["score"] >= 0.5
    assert result["passes_gate"] is True


def test_grounding_ignora_entidades_curtas():
    """Entidades com <3 chars sao ignoradas para evitar falsos positivos."""
    content = "Algo sobre PT e SP em 2024."
    result = evaluate_section_grounding(content, ["PT", "SP"])
    assert result["entity_hits"] == 0


def test_render_qc_block_inclui_alerta_quando_overlap_alto():
    overlap = {"jaccard_5gram": 0.45, "jaccard_3gram": 0.55, "alert": True, "threshold": 0.30, "tokens_report": 1000, "tokens_upload": 800}
    md = render_qc_block(overlap)
    assert "ALTO" in md
    assert "QC" in md
    assert "45.0%" in md


def test_render_qc_block_sem_alerta_quando_overlap_baixo():
    overlap = {"jaccard_5gram": 0.05, "jaccard_3gram": 0.15, "alert": False, "threshold": 0.30, "tokens_report": 1000, "tokens_upload": 800}
    md = render_qc_block(overlap)
    assert "OK" in md
    assert "ALTO" not in md


def test_render_qc_block_lista_secoes_quando_fornecidas():
    overlap = {"jaccard_5gram": 0.10, "jaccard_3gram": 0.20, "alert": False, "threshold": 0.30, "tokens_report": 500, "tokens_upload": 500}
    sections = [
        {"score": 0.8, "passes_gate": True, "has_number": True, "has_quote": True, "entity_hits": 2},
        {"score": 0.0, "passes_gate": False, "has_number": False, "has_quote": False, "entity_hits": 0},
    ]
    md = render_qc_block(overlap, sections)
    assert "1/2" in md
    assert "Gate editorial" in md
