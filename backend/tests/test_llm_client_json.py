from types import SimpleNamespace

import pytest

from app.utils.llm_client import LLMClient, parse_llm_json_response


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


def test_llm_client_extrai_tokens_de_cache_openai(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = ""

        @staticmethod
        def json():
            return {
                "choices": [{"message": {"content": "OK", "role": "assistant"}}],
                "usage": {
                    "prompt_tokens": 1_000,
                    "completion_tokens": 50,
                    "prompt_tokens_details": {"cached_tokens": 400},
                },
            }

    monkeypatch.setattr(
        "app.utils.llm_client.http_requests.post",
        lambda *args, **kwargs: FakeResponse(),
    )
    client = LLMClient(api_key="test", base_url="https://example.test/v1", model="test-model")

    response, _, _ = client._try_provider(
        base_url=client.base_url,
        api_key=client.api_key,
        model_override=None,
        provider_name="test",
        model=client.model,
        messages=[{"role": "user", "content": "teste"}],
        stream=False,
    )

    assert response.usage.prompt_tokens == 1_000
    assert response.usage.completion_tokens == 50
    assert response.usage.cached_prompt_tokens == 400


def test_luna_omite_temperatura_customizada(monkeypatch):
    captured = {}
    client = LLMClient(
        api_key="test",
        base_url="https://example.test/v1",
        model="openai/gpt-5.6-luna",
    )

    def fake_request(**kwargs):
        captured.update(kwargs)
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))],
            usage=None,
        )
        return response, 1.0, 1

    monkeypatch.setattr(client, "_request_with_retry", fake_request)
    assert client.chat(
        messages=[{"role": "user", "content": "teste"}],
        temperature=0.3,
    ) == "OK"

    assert "temperature" not in captured
    assert captured["max_completion_tokens"] == 4096


def test_outro_modelo_preserva_temperatura(monkeypatch):
    captured = {}
    client = LLMClient(
        api_key="test",
        base_url="https://example.test/v1",
        model="outro-modelo",
    )

    def fake_request(**kwargs):
        captured.update(kwargs)
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))],
            usage=None,
        )
        return response, 1.0, 1

    monkeypatch.setattr(client, "_request_with_retry", fake_request)
    client.chat(
        messages=[{"role": "user", "content": "teste"}],
        temperature=0.3,
    )

    assert captured["temperature"] == pytest.approx(0.3)
