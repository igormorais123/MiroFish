import pytest

from app.utils.llm_client import parse_llm_json_response


def test_parse_llm_json_response_extrai_objeto_com_texto_em_volta():
    payload = parse_llm_json_response(
        "Segue o resultado:\n```json\n{\"entity_types\": [], \"edge_types\": []}\n```\nFim."
    )

    assert payload == {"entity_types": [], "edge_types": []}


def test_parse_llm_json_response_extrai_primeiro_objeto_balanceado():
    payload = parse_llm_json_response(
        "texto antes {\"ok\": true, \"nested\": {\"value\": 1}} texto depois"
    )

    assert payload["nested"]["value"] == 1


def test_parse_llm_json_response_rejeita_markdown_sem_json():
    with pytest.raises(ValueError):
        parse_llm_json_response("| campo | valor |\n| --- | --- |\n| a | b |")
