"""Esforco de raciocinio da Helena, isolado do resto do sistema."""

import os

import pytest

from app.config import Config
from app.utils.llm_client import LLMClient


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "chave-de-teste")


def _captured_kwargs(client, monkeypatch):
    """Intercepta o payload enviado ao provider."""
    captured = {}

    class _Message:
        content = "ok"

    class _Choice:
        message = _Message()

    class _Response:
        choices = [_Choice()]
        usage = None

    def fake_request(**kwargs):
        captured.update(kwargs)
        return (_Response(), 10, 1)

    monkeypatch.setattr(client, "_request_with_retry", fake_request)
    client.chat(messages=[{"role": "user", "content": "oi"}], max_tokens=100)
    return captured


def test_esforco_explicito_vence_o_padrao_global(monkeypatch):
    """A Helena sobe o proprio esforco sem alterar o dos demais consumidores."""
    monkeypatch.setenv("LUNA_REASONING_EFFORT", "low")

    client = LLMClient(model="codex/gpt-5.6-luna", reasoning_effort="high")
    kwargs = _captured_kwargs(client, monkeypatch)

    assert kwargs["reasoning_effort"] == "high"


def test_sem_esforco_explicito_segue_o_global(monkeypatch):
    """Quem nao pediu nada nao muda de comportamento."""
    monkeypatch.setenv("LUNA_REASONING_EFFORT", "low")

    client = LLMClient(model="codex/gpt-5.6-luna")
    kwargs = _captured_kwargs(client, monkeypatch)

    assert kwargs["reasoning_effort"] == "low"


def test_esforco_invalido_cai_para_low(monkeypatch):
    monkeypatch.setenv("LUNA_REASONING_EFFORT", "low")

    client = LLMClient(model="codex/gpt-5.6-luna", reasoning_effort="turbinado")
    kwargs = _captured_kwargs(client, monkeypatch)

    assert kwargs["reasoning_effort"] == "low"


def test_modelo_nao_luna_nao_recebe_esforco(monkeypatch):
    """reasoning_effort e especifico do Luna; outros modelos recebem temperatura."""
    client = LLMClient(model="opus-tasks", reasoning_effort="high")
    kwargs = _captured_kwargs(client, monkeypatch)

    assert "reasoning_effort" not in kwargs
    assert "temperature" in kwargs


def test_teto_de_tokens_da_helena_cobre_raciocinio_mais_resposta():
    """
    Com esforco alto o raciocinio consome a mesma cota da resposta. O teto
    anterior (1800) fazia a Helena cair no plano de fallback sem falha real.
    """
    assert Config.HELENA_PLAN_MAX_TOKENS >= 8000
    assert Config.LLM_HELENA_REASONING_EFFORT in {"none", "low", "medium", "high", "xhigh"}
