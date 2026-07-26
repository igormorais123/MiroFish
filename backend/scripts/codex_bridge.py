"""
Ponte HTTP compativel com a API OpenAI que atende pela assinatura do Codex CLI.

Por que existe: o sistema inteiro (agentes CAMEL da simulacao, LLMClient,
gerador de relatorio) fala `POST /v1/chat/completions` contra uma base_url.
Apontando essa base_url para c, o OmniRoute sai do caminho e todo o trafego
passa a usar a assinatura local do `codex`, sem tocar em nenhuma das
integracoes.

Medido nesta maquina (gpt-5.6-luna, prompt curto, esforco baixo):

    paralelismo  sucesso  latencia mediana  vazao
     8           8/8       13.3s            21.3 chamadas/min
    16          16/16      20.1s            39.6 chamadas/min
    32          32/32      34.3s            45.0 chamadas/min

A vazao satura entre 16 e 32 enquanto a latencia por chamada quase dobra, e
por isso o limite padrao e 16: e onde a fila para de pagar por si mesma.

Uso:
    python scripts/codex_bridge.py            # escuta em 127.0.0.1:5099

Depois, no backend e nos scripts de simulacao:
    LLM_BASE_URL=http://127.0.0.1:5099/v1
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request

HOST = os.environ.get("CODEX_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("CODEX_BRIDGE_PORT", "5099"))
MAX_CONCURRENCY = int(os.environ.get("CODEX_BRIDGE_CONCURRENCY", "16"))
TIMEOUT_SECONDS = int(os.environ.get("CODEX_BRIDGE_TIMEOUT", "300"))
DEFAULT_MODEL = os.environ.get("CODEX_BRIDGE_MODEL", "gpt-5.6-luna")
DEFAULT_EFFORT = os.environ.get("CODEX_BRIDGE_EFFORT", "low")

# Sufixo no nome do modelo escolhe o esforco de raciocinio: quem pede
# profundidade (Helena, relatorio) usa `-high`; agente de simulacao usa o
# padrao barato.
EFFORT_SUFFIXES = ("high", "medium", "low", "minimal")

app = Flask(__name__)
_slots = threading.Semaphore(MAX_CONCURRENCY)
_stats_lock = threading.Lock()
_stats = {"recebidas": 0, "concluidas": 0, "falhas": 0, "em_voo": 0, "segundos": 0.0}


def codex_path() -> Optional[str]:
    """Caminho do binario; no Windows o `codex` do PATH e um wrapper .CMD."""
    configured = os.environ.get("CODEX_BRIDGE_BIN", "").strip()
    if configured:
        return configured if os.path.isfile(configured) else shutil.which(configured)
    return shutil.which("codex")


# Presentes no ambiente, estas variaveis fazem o CLI atender pela API paga em
# vez da assinatura — que e justamente o que esta ponte existe para evitar.
# `codex doctor` acusa isso como "mixed auth signals".
VARIAVEIS_DE_API = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_ORGANIZATION", "OPENAI_PROJECT")


def subprocess_env() -> Dict[str, str]:
    """Ambiente do subprocesso, sem credencial de API e com o CODEX_HOME certo."""
    env = {k: v for k, v in os.environ.items() if k not in VARIAVEIS_DE_API}
    codex_home = os.environ.get("CODEX_BRIDGE_CODEX_HOME", "").strip()
    if codex_home:
        env["CODEX_HOME"] = codex_home
    return env


def split_model(model: str) -> Tuple[str, str]:
    """Separa `gpt-5.6-luna-high` em (modelo, esforco)."""
    model = (model or "").strip() or DEFAULT_MODEL
    for suffix in EFFORT_SUFFIXES:
        if model.endswith(f"-{suffix}"):
            return model[: -(len(suffix) + 1)], suffix
    return model, DEFAULT_EFFORT


def build_prompt(messages: List[Dict[str, Any]], wants_json: bool) -> str:
    """
    Achata a conversa num unico prompt.

    O `codex exec` recebe um turno so, entao os papeis viram rotulos. As
    instrucoes de sistema vem primeiro porque definem o contrato; o conteudo
    de usuario vem depois, como dado.
    """
    sistema, corpo = [], []
    for msg in messages or []:
        papel = (msg.get("role") or "user").lower()
        conteudo = msg.get("content")
        if isinstance(conteudo, list):
            # Formato multimodal: aproveita so as partes de texto.
            conteudo = " ".join(
                p.get("text", "") for p in conteudo if isinstance(p, dict)
            )
        conteudo = (conteudo or "").strip()
        if not conteudo:
            continue
        if papel == "system":
            sistema.append(conteudo)
        elif papel == "assistant":
            corpo.append(f"[resposta anterior do assistente]\n{conteudo}")
        else:
            corpo.append(conteudo)

    partes = list(sistema)
    partes.append(
        "Responda diretamente a partir do texto abaixo. Nao explore o ambiente, "
        "nao liste arquivos e nao execute comandos: nao ha nada util no disco "
        "para esta tarefa."
    )
    if wants_json:
        partes.append(
            "Responda SOMENTE com o objeto JSON pedido, sem cerca de codigo e "
            "sem texto ao redor."
        )
    partes.extend(corpo)
    return "\n\n".join(partes)


def extract_message(stdout: str) -> Optional[str]:
    """Ultima fala do agente no fluxo JSONL do `codex exec --json`."""
    message = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            message = item["text"]
    return message


def extract_usage(stdout: str) -> Dict[str, int]:
    """Contagem de tokens do evento de fim de turno, quando o CLI a informa."""
    usage: Dict[str, int] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    entrada = int(usage.get("input_tokens") or 0)
    saida = int(usage.get("output_tokens") or 0)
    return {
        "prompt_tokens": entrada,
        "completion_tokens": saida,
        "total_tokens": entrada + saida,
    }


def run_codex(prompt: str, model: str, effort: str) -> Tuple[str, Dict[str, int]]:
    """
    Executa uma chamada, respeitando o limite de concorrencia.

    O prompt vai por stdin porque, como argumento, o JSON com aspas sofre com
    as regras de escaping da linha de comando do Windows e chega truncado.
    """
    binary = codex_path()
    if not binary:
        raise RuntimeError("binario codex nao encontrado na maquina")

    command = [
        binary,
        "exec",
        "-m", model,
        "-c", f"model_reasoning_effort={effort}",
        "--ignore-user-config",
        "--sandbox", "read-only",
        "--skip-git-repo-check",
        "--json",
        "-",
    ]

    with _slots:
        with _stats_lock:
            _stats["em_voo"] += 1
        inicio = time.time()
        try:
            with tempfile.TemporaryDirectory(prefix="codex-bridge-") as workdir:
                completed = subprocess.run(
                    command,
                    cwd=workdir,
                    input=prompt,
                    env=subprocess_env(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=TIMEOUT_SECONDS,
                    shell=False,
                )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"codex excedeu {TIMEOUT_SECONDS}s") from exc
        finally:
            with _stats_lock:
                _stats["em_voo"] -= 1
                _stats["segundos"] += time.time() - inicio

    if completed.returncode != 0:
        raise RuntimeError(
            f"codex saiu com codigo {completed.returncode}: "
            f"{(completed.stderr or '')[:300]}"
        )

    message = extract_message(completed.stdout or "")
    if message is None:
        raise RuntimeError("codex nao retornou mensagem do agente")
    return message, extract_usage(completed.stdout or "")


@app.post("/v1/chat/completions")
def chat_completions():
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    if not messages:
        return jsonify({"error": {"message": "messages ausente", "type": "invalid_request_error"}}), 400

    model, effort = split_model(payload.get("model"))
    fmt = payload.get("response_format") or {}
    wants_json = isinstance(fmt, dict) and "json" in str(fmt.get("type", "")).lower()

    with _stats_lock:
        _stats["recebidas"] += 1

    try:
        texto, usage = run_codex(build_prompt(messages, wants_json), model, effort)
    except RuntimeError as exc:
        with _stats_lock:
            _stats["falhas"] += 1
        app.logger.warning("falha na chamada: %s", exc)
        return jsonify({"error": {"message": str(exc), "type": "upstream_error"}}), 502

    with _stats_lock:
        _stats["concluidas"] += 1

    return jsonify({
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": f"{model}-{effort}",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": texto},
            "finish_reason": "stop",
        }],
        "usage": usage,
    })


@app.get("/v1/models")
def models():
    base, _ = split_model(DEFAULT_MODEL)
    dados = [
        {"id": base, "object": "model", "owned_by": "codex-cli"},
    ] + [
        {"id": f"{base}-{s}", "object": "model", "owned_by": "codex-cli"}
        for s in EFFORT_SUFFIXES
    ]
    return jsonify({"object": "list", "data": dados})


@app.get("/health")
def health():
    binary = codex_path()
    with _stats_lock:
        atual = dict(_stats)
    concluidas = atual["concluidas"]
    atual["latencia_media_s"] = round(atual["segundos"] / concluidas, 1) if concluidas else None
    atual.pop("segundos", None)
    env = subprocess_env()
    return jsonify({
        "ok": bool(binary),
        "codex": binary,
        "codex_home": env.get("CODEX_HOME") or os.environ.get("CODEX_HOME"),
        "cobranca": "assinatura",
        "variaveis_de_api_removidas": [
            k for k in VARIAVEIS_DE_API if k in os.environ
        ],
        "concorrencia_maxima": MAX_CONCURRENCY,
        "modelo_padrao": DEFAULT_MODEL,
        "esforco_padrao": DEFAULT_EFFORT,
        **atual,
    }), (200 if binary else 503)


if __name__ == "__main__":
    binario = codex_path()
    if not binario:
        raise SystemExit(
            "codex nao encontrado no PATH. Instale o CLI e faca login antes de subir a ponte."
        )
    print(f"codex: {binario}")
    print(f"ponte em http://{HOST}:{PORT}/v1  (concorrencia {MAX_CONCURRENCY})")
    app.run(host=HOST, port=PORT, threaded=True, debug=False)
