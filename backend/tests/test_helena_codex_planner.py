"""Planejador da Helena via Codex CLI (sem invocar o binario de verdade)."""

import json
import subprocess

import pytest

from app.config import Config
from app.services import helena_codex_planner as hcp


SYSTEM = "Voce e Helena. Retorne {summary,rationale,actions}."
PAYLOAD = {"command": "explique a simulacao", "allowed_tools": ["ask_analysis"]}


def _stream(*events: dict) -> str:
    """Monta um fluxo JSONL como o do `codex exec --json`."""
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in events)


def _agent_message(text: str) -> dict:
    return {"type": "item.completed", "item": {"id": "i1", "type": "agent_message", "text": text}}


class _Completed:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.fixture(autouse=True)
def _fake_binary(monkeypatch):
    monkeypatch.setattr(hcp, "codex_cli_path", lambda: "/usr/bin/codex")


def test_extrai_plano_do_fluxo_de_eventos(monkeypatch):
    """O fluxo mistura eventos de sessao e erro; vale a ultima fala do agente."""
    plano = {"summary": "Explicar estado", "rationale": "ok", "actions": [{"tool": "ask_analysis"}]}
    stdout = _stream(
        {"type": "thread.started", "thread_id": "abc"},
        {"type": "item.completed", "item": {"id": "i0", "type": "error", "message": "aviso de hook"}},
        {"type": "turn.started"},
        _agent_message(json.dumps(plano, ensure_ascii=False)),
        {"type": "turn.completed", "usage": {"output_tokens": 10}},
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed(stdout=stdout))

    resultado = hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)

    assert resultado["summary"] == "Explicar estado"
    assert resultado["actions"][0]["tool"] == "ask_analysis"


def test_aceita_json_em_cerca_de_codigo(monkeypatch):
    plano = {"summary": "s", "rationale": "r", "actions": []}
    texto = f"```json\n{json.dumps(plano)}\n```"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed(stdout=_stream(_agent_message(texto))))

    assert hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)["summary"] == "s"


def test_prompt_vai_por_stdin_com_contexto(monkeypatch):
    """Como argumento, o JSON quebra no escaping da linha de comando do Windows."""
    capturado = {}

    def fake_run(command, **kwargs):
        capturado["command"] = command
        capturado["input"] = kwargs.get("input")
        capturado["cwd"] = kwargs.get("cwd")
        return _Completed(stdout=_stream(_agent_message('{"summary":"s","rationale":"r","actions":[]}')))

    monkeypatch.setattr(subprocess, "run", fake_run)
    hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)

    assert capturado["command"][-1] == "-"
    assert "explique a simulacao" in capturado["input"]
    assert SYSTEM in capturado["input"]


def test_roda_isolado_e_sem_escrita(monkeypatch):
    """Sandbox de leitura, config do usuario fora e diretorio temporario."""
    capturado = {}

    def fake_run(command, **kwargs):
        capturado["command"] = command
        capturado["cwd"] = kwargs.get("cwd")
        return _Completed(stdout=_stream(_agent_message('{"summary":"s","rationale":"r","actions":[]}')))

    monkeypatch.setattr(subprocess, "run", fake_run)
    hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)

    comando = capturado["command"]
    assert "--sandbox" in comando and comando[comando.index("--sandbox") + 1] == "read-only"
    assert "--ignore-user-config" in comando
    assert f"model_reasoning_effort={Config.LLM_HELENA_REASONING_EFFORT}" in comando
    # Diretorio de trabalho temporario, nunca o repositorio
    assert "helena-codex-" in str(capturado["cwd"])


def test_binario_ausente_e_indisponibilidade(monkeypatch):
    monkeypatch.setattr(hcp, "codex_cli_path", lambda: None)

    with pytest.raises(hcp.CodexPlannerUnavailable, match="nao encontrado"):
        hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)


def test_timeout_vira_indisponibilidade(monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="codex", timeout=180)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(hcp.CodexPlannerUnavailable, match="excedeu"):
        hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)


def test_saida_sem_mensagem_do_agente(monkeypatch):
    """Um turno que so produziu erro nao pode virar plano vazio silencioso."""
    stdout = _stream({"type": "item.completed", "item": {"type": "error", "message": "falhou"}})
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed(stdout=stdout))

    with pytest.raises(hcp.CodexPlannerUnavailable, match="mensagem do agente"):
        hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)


def test_texto_nao_json_vira_indisponibilidade(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: _Completed(stdout=_stream(_agent_message("desculpe, nao consegui")))
    )

    with pytest.raises(hcp.CodexPlannerUnavailable, match="JSON invalido"):
        hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)


def test_codigo_de_saida_diferente_de_zero(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: _Completed(stdout="", stderr="auth expirada", returncode=1)
    )

    with pytest.raises(hcp.CodexPlannerUnavailable, match="codigo 1"):
        hcp.plan_with_codex_cli(SYSTEM, PAYLOAD)
