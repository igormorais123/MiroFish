from app.services.report_attribution import (
    normalize_report_attribution,
    classify_direct_quotes,
    label_operational_deadlines,
)


def test_unsupported_quote_is_converted_to_simulation_inference():
    content = 'A tese central e: "O foco deve ser a previsibilidade da rotina".'
    result = normalize_report_attribution(content, evidence_texts=["calendario de visitas"])
    assert '"O foco deve ser a previsibilidade da rotina"' not in result["content"]
    assert "[Inferencia da simulacao] O foco deve ser a previsibilidade da rotina" in result["content"]
    assert result["converted_quotes_count"] == 1


def test_supported_quote_remains_literal_with_origin():
    content = 'O documento afirma: "calendario de visitas".'
    result = normalize_report_attribution(content, evidence_texts=["No processo consta calendario de visitas."])
    assert '"calendario de visitas"' in result["content"]
    assert result["converted_quotes_count"] == 0
    quotes = classify_direct_quotes(result["content"], evidence_texts=["No processo consta calendario de visitas."])
    assert quotes[0]["supported"] is True


def test_operational_deadlines_are_labeled_before_numeric_audit():
    content = "Nos proximos 15, 30 e 60 dias, organizar documentos e registros."
    result = label_operational_deadlines(content)
    assert "[Sugestao operacional]" in result


def test_operational_hour_deadlines_are_labeled_before_numeric_audit():
    content = "Em 48 horas, anexar a decisao e as pecas essenciais."
    result = label_operational_deadlines(content)
    assert "[Sugestao operacional]" in result


def test_curly_unsupported_quote_is_converted_to_simulation_inference():
    content = "A sintese registra: “precisamos reorganizar a rotina familiar”."
    result = normalize_report_attribution(content, evidence_texts=["calendario de visitas"])
    assert "“precisamos reorganizar a rotina familiar”" not in result["content"]
    assert "[Inferencia da simulacao] precisamos reorganizar a rotina familiar" in result["content"]
    assert result["converted_quotes_count"] == 1


def test_single_curly_unsupported_quote_is_converted_to_simulation_inference():
    content = "A sintese registra: ‘precisamos reorganizar a rotina familiar’."
    result = normalize_report_attribution(content, evidence_texts=["calendario de visitas"])
    assert "‘precisamos reorganizar a rotina familiar’" not in result["content"]
    assert "[Inferencia da simulacao] precisamos reorganizar a rotina familiar" in result["content"]
    assert result["converted_quotes_count"] == 1


def test_quotes_inside_fenced_code_block_are_preserved():
    content = 'Texto fora.\n\n```md\n"frase inventada sem lastro"\n```\n'
    result = normalize_report_attribution(content, evidence_texts=["calendario de visitas"])
    assert '"frase inventada sem lastro"' in result["content"]
    assert "[Inferencia da simulacao] frase inventada sem lastro" not in result["content"]
    assert result["converted_quotes_count"] == 0


def test_short_quote_below_audit_minimum_is_not_converted():
    content = 'O campo indica "ok".'
    result = normalize_report_attribution(content, evidence_texts=["calendario de visitas"])
    assert '"ok"' in result["content"]
    assert "[Inferencia da simulacao] ok" not in result["content"]
    assert result["converted_quotes_count"] == 0


def test_supported_quote_origin_is_returned_by_normalize_report_attribution():
    evidence = [
        "Primeiro documento sem a citacao.",
        "No processo consta calendario de visitas.",
    ]
    content = 'O documento afirma: "calendario de visitas".'
    result = normalize_report_attribution(content, evidence_texts=evidence)
    assert result["quotes"][0]["supported"] is True
    assert result["quotes"][0]["origin_index"] == 1
    assert result["quotes"][0]["origin_text"] == "No processo consta calendario de visitas."


def test_supported_quote_with_different_punctuation_includes_origin():
    evidence = [
        "Primeiro documento sem a citacao.",
        "No processo consta calendario-de-visitas.",
    ]
    content = 'O documento afirma: "calendario de visitas".'
    result = normalize_report_attribution(content, evidence_texts=evidence)
    quote = result["quotes"][0]
    assert quote["supported"] is True
    assert quote["origin_index"] == 1
    assert quote["origin_text"] == "No processo consta calendario-de-visitas."
