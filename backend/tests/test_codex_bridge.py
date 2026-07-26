"""Ponte HTTP Codex CLI: traducao OpenAI <-> `codex exec`, sem invocar o binario."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import codex_bridge as cb  # noqa: E402


@pytest.fixture
def cliente():
    cb.app.config["TESTING"] = True
    with cb.app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def _binario_falso(monkeypatch):
    monkeypatch.setattr(cb, "codex_path", lambda: "/usr/bin/codex")


class _Completed:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _stream(*events):
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in events)


def _fala(texto):
    return {"type": "item.completed", "item": {"type": "agent_message", "text": texto}}


def _ok(texto="pronto", entrada=10, saida=5):
    return _Completed(stdout=_stream(
        {"type": "thread.started", "thread_id": "t1"},
        _fala(texto),
        {"type": "turn.completed", "usage": {"input_tokens": entrada, "output_tokens": saida}},
    ))


# --- separacao de modelo e esforco ---

def test_sufixo_do_modelo_define_o_esforco():
    assert cb.split_model("gpt-5.6-luna-high") == ("gpt-5.6-luna", "high")
    assert cb.split_model("gpt-5.6-luna-minimal") == ("gpt-5.6-luna", "minimal")


def test_modelo_sem_sufixo_usa_o_esforco_padrao():
    modelo, esforco = cb.split_model("gpt-5.6-luna")
    assert (modelo, esforco) == ("gpt-5.6-luna", cb.DEFAULT_EFFORT)


def test_modelo_vazio_cai_no_padrao():
    assert cb.split_model("")[0] == cb.split_model(None)[0] == cb.DEFAULT_MODEL


# --- montagem do prompt ---

def test_sistema_vem_antes_do_usuario():
    """O contrato precede o dado; invertido, o modelo trata instrucao como texto."""
    prompt = cb.build_prompt([
        {"role": "user", "content": "qual o clima"},
        {"role": "system", "content": "voce e um meteorologista"},
    ], wants_json=False)

    assert prompt.index("meteorologista") < prompt.index("qual o clima")


def test_conteudo_multimodal_aproveita_so_o_texto():
    prompt = cb.build_prompt([
        {"role": "user", "content": [
            {"type": "text", "text": "descreva"},
            {"type": "image_url", "image_url": {"url": "http://x/y.png"}},
        ]},
    ], wants_json=False)

    assert "descreva" in prompt
    assert "y.png" not in prompt


def test_pedido_de_json_acrescenta_a_instrucao():
    assert "SOMENTE com o objeto JSON" in cb.build_prompt(
        [{"role": "user", "content": "x"}], wants_json=True
    )
    assert "SOMENTE com o objeto JSON" not in cb.build_prompt(
        [{"role": "user", "content": "x"}], wants_json=False
    )


def test_mensagens_vazias_sao_descartadas():
    prompt = cb.build_prompt([
        {"role": "user", "content": "   "},
        {"role": "user", "content": "conteudo real"},
    ], wants_json=False)

    assert "conteudo real" in prompt


# --- leitura do fluxo de eventos ---

def test_vale_a_ultima_fala_do_agente():
    stdout = _stream(_fala("rascunho"), {"type": "turn.started"}, _fala("final"))
    assert cb.extract_message(stdout) == "final"


def test_fluxo_sem_fala_do_agente_nao_vira_resposta_vazia():
    stdout = _stream({"type": "item.completed", "item": {"type": "error", "message": "falhou"}})
    assert cb.extract_message(stdout) is None


def test_usage_ausente_vira_zero():
    assert cb.extract_usage(_stream(_fala("x")))["total_tokens"] == 0


# --- endpoint ---

def test_resposta_no_formato_openai(cliente, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _ok("ola", 10, 5))

    r = cliente.post("/v1/chat/completions", json={
        "model": "gpt-5.6-luna-high",
        "messages": [{"role": "user", "content": "oi"}],
    })

    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["choices"][0]["message"]["content"] == "ola"
    assert corpo["choices"][0]["message"]["role"] == "assistant"
    assert corpo["choices"][0]["finish_reason"] == "stop"
    assert corpo["usage"]["total_tokens"] == 15
    assert corpo["object"] == "chat.completion"


def test_esforco_do_modelo_chega_ao_comando(cliente, monkeypatch):
    capturado = {}

    def fake_run(command, **kwargs):
        capturado["command"] = command
        capturado["input"] = kwargs.get("input")
        return _ok()

    monkeypatch.setattr(subprocess, "run", fake_run)
    cliente.post("/v1/chat/completions", json={
        "model": "gpt-5.6-luna-high",
        "messages": [{"role": "user", "content": "oi"}],
    })

    assert "model_reasoning_effort=high" in capturado["command"]
    assert capturado["command"][capturado["command"].index("-m") + 1] == "gpt-5.6-luna"
    # Prompt por stdin: como argumento, o escaping do Windows o trunca.
    assert capturado["command"][-1] == "-"
    assert "oi" in capturado["input"]


def test_roda_isolado_e_sem_escrita(cliente, monkeypatch):
    capturado = {}

    def fake_run(command, **kwargs):
        capturado["command"] = command
        capturado["cwd"] = kwargs.get("cwd")
        return _ok()

    monkeypatch.setattr(subprocess, "run", fake_run)
    cliente.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "oi"}]})

    comando = capturado["command"]
    assert comando[comando.index("--sandbox") + 1] == "read-only"
    assert "--ignore-user-config" in comando
    assert "codex-bridge-" in str(capturado["cwd"])


def test_messages_ausente_e_erro_do_cliente(cliente):
    r = cliente.post("/v1/chat/completions", json={"model": "gpt-5.6-luna"})
    assert r.status_code == 400


def test_falha_do_codex_vira_502(cliente, monkeypatch):
    """Erro de credencial nao pode virar 200 com texto de erro no conteudo."""
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: _Completed(stdout="", stderr="auth expirada", returncode=1),
    )

    r = cliente.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "oi"}]})

    assert r.status_code == 502
    assert "codigo 1" in r.get_json()["error"]["message"]


def test_timeout_vira_502(cliente, monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="codex", timeout=300)

    monkeypatch.setattr(subprocess, "run", fake_run)
    r = cliente.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "oi"}]})

    assert r.status_code == 502
    assert "excedeu" in r.get_json()["error"]["message"]


def test_binario_ausente_derruba_o_health(cliente, monkeypatch):
    monkeypatch.setattr(cb, "codex_path", lambda: None)
    r = cliente.get("/health")
    assert r.status_code == 503
    assert r.get_json()["ok"] is False


def test_health_reporta_a_concorrencia(cliente):
    corpo = cliente.get("/health").get_json()
    assert corpo["ok"] is True
    assert corpo["concorrencia_maxima"] == cb.MAX_CONCURRENCY


# --- cobranca pela assinatura, nunca pela API paga ---

def test_credencial_de_api_nao_chega_ao_subprocesso(monkeypatch):
    """Com OPENAI_API_KEY no ambiente, o CLI atenderia pela API paga."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-secreta")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://gateway/v1")
    monkeypatch.setenv("PATH", "/usr/bin")

    env = cb.subprocess_env()

    assert "OPENAI_API_KEY" not in env
    assert "OPENAI_BASE_URL" not in env
    # O resto do ambiente precisa sobreviver, senao o binario nem e encontrado.
    assert env["PATH"] == "/usr/bin"


def test_codex_home_configurado_e_repassado(monkeypatch):
    monkeypatch.setenv("CODEX_BRIDGE_CODEX_HOME", "/caminho/.codex-pro")
    assert cb.subprocess_env()["CODEX_HOME"] == "/caminho/.codex-pro"


def test_chamada_real_roda_sem_credencial_de_api(cliente, monkeypatch):
    capturado = {}

    def fake_run(command, **kwargs):
        capturado["env"] = kwargs.get("env")
        return _ok()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-secreta")
    monkeypatch.setattr(subprocess, "run", fake_run)
    cliente.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "oi"}]})

    assert "OPENAI_API_KEY" not in capturado["env"]


def test_health_denuncia_variaveis_de_api_presentes(cliente, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-secreta")
    corpo = cliente.get("/health").get_json()

    assert corpo["cobranca"] == "assinatura"
    assert "OPENAI_API_KEY" in corpo["variaveis_de_api_removidas"]
    # O valor da credencial nunca pode aparecer no diagnostico.
    assert "sk-proj-secreta" not in cliente.get("/health").get_data(as_text=True)


def test_models_lista_as_variantes_de_esforco(cliente):
    ids = [m["id"] for m in cliente.get("/v1/models").get_json()["data"]]
    assert any(i.endswith("-high") for i in ids)
    assert any(i.endswith("-low") for i in ids)


def test_concorrencia_limitada_pelo_semaforo(monkeypatch):
    """Sem o limite, uma simulacao dispara centenas de processos de uma vez."""
    import threading

    pico = {"atual": 0, "maximo": 0}
    trava = threading.Lock()
    barreira = threading.Event()

    def fake_run(*a, **k):
        with trava:
            pico["atual"] += 1
            pico["maximo"] = max(pico["maximo"], pico["atual"])
        barreira.wait(timeout=5)
        with trava:
            pico["atual"] -= 1
        return _ok()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(cb, "_slots", threading.Semaphore(3))

    threads = [
        threading.Thread(target=lambda: cb.run_codex("p", "m", "low"))
        for _ in range(10)
    ]
    for t in threads:
        t.start()
    # Deixa as vagas encherem antes de liberar, para o pico ser observavel.
    threading.Event().wait(0.3)
    barreira.set()
    for t in threads:
        t.join(timeout=10)

    assert pico["maximo"] <= 3
