"""Proxy OpenAI-compat que usa Codex CLI (OAuth ChatGPT Pro) como backend.

- /v1/chat/completions : chama `codex exec` e envelopa resposta no formato OpenAI.
- /v1/embeddings       : delega ao Ollama local (Codex nao expoe embeddings).
- /v1/models           : lista modelos suportados.

Uso:
    python codex_proxy.py  # escuta em 0.0.0.0:8004
    export CODEX_HOME=/c/Users/IgorPC/.codex-pro
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path

import requests
from flask import Flask, jsonify, request

CODEX_HOME = os.environ.get("CODEX_HOME", r"C:\Users\IgorPC\.codex-pro")
# No Windows, precisa do .cmd porque o `codex` puro e um shim bash nao invocavel via subprocess.
_default_codex = r"C:\Users\IgorPC\AppData\Roaming\fnm\node-versions\v24.15.0\installation\codex.cmd"
CODEX_BIN = os.environ.get("CODEX_BIN", _default_codex if os.path.exists(_default_codex) else "codex")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PORT = int(os.environ.get("CODEX_PROXY_PORT", "8004"))
DEFAULT_MODEL = os.environ.get("CODEX_DEFAULT_MODEL", "gpt-5.5")
_CODEX_RETRIES = int(os.environ.get("CODEX_RETRIES", "2"))
_CODEX_RETRY_BACKOFF = float(os.environ.get("CODEX_RETRY_BACKOFF", "2.0"))
ALLOWED_MODELS = {"gpt-5.5", "gpt-5.4-mini", "gpt-5.4", "gpt-5.4-xhigh"}

app = Flask(__name__)
# Limite de body: evita MemoryError quando Flask cai pro dev server (Werkzeug)
# 8MB cobre prompts grandes (relatorio + grafo serializado) sem dar OOM single-thread.
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

# ---- Cache + concorrencia (2026-04-25 timing fix) ----
# Cache LRU em memoria: hash(prompt+model+want_json) -> (content, elapsed). TTL 30 min.
# Reduz drasticamente runs repetidos do mesmo payload (testes A/B, retries).
_CACHE_MAX = int(os.environ.get("CODEX_CACHE_MAX", "256"))
_CACHE_TTL = int(os.environ.get("CODEX_CACHE_TTL", "1800"))  # segundos
_cache: "OrderedDict[str, tuple[str, float, float]]" = OrderedDict()  # key -> (content, elapsed, ts)
_cache_lock = threading.Lock()
_cache_hits = 0
_cache_misses = 0

# Semaforo limita concurrent codex execs para nao saturar Windows (Node.js + auth pesado)
_MAX_CONCURRENT = int(os.environ.get("CODEX_MAX_CONCURRENT", "8"))
_codex_sem = threading.Semaphore(_MAX_CONCURRENT)

# Metricas globais para debug
_metrics = {"calls": 0, "total_elapsed_s": 0.0, "errors": 0}
_metrics_lock = threading.Lock()


def _cache_key(prompt: str, model: str, want_json: bool) -> str:
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(b"|json=" if want_json else b"|text=")
    h.update(prompt.encode("utf-8", errors="replace"))
    return h.hexdigest()


def _cache_get(key: str):
    global _cache_hits, _cache_misses
    with _cache_lock:
        item = _cache.get(key)
        if item is None:
            _cache_misses += 1
            return None
        content, elapsed, ts = item
        if time.time() - ts > _CACHE_TTL:
            _cache.pop(key, None)
            _cache_misses += 1
            return None
        _cache.move_to_end(key)
        _cache_hits += 1
        return content, elapsed


def _cache_set(key: str, content: str, elapsed: float):
    with _cache_lock:
        _cache[key] = (content, elapsed, time.time())
        while len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)


def _normalize_model(model: str | None) -> str:
    if not model:
        return DEFAULT_MODEL
    m = model.strip()
    # Normaliza aliases comuns do Mirofish
    mapping = {
        "haiku-tasks": "gpt-5.4-mini",
        "sonnet-tasks": "gpt-5.5",
        "opus-tasks": "gpt-5.5",
        "helena-premium": "gpt-5.5",
        "gpt-4o": "gpt-5.4-mini",
        "gpt-4o-mini": "gpt-5.4-mini",
        "text-embedding-3-small": "nomic-embed-text",
    }
    if m in mapping:
        return mapping[m]
    if m in ALLOWED_MODELS:
        return m
    # fallback defensivo
    return DEFAULT_MODEL


def _serialize_messages(messages: list[dict]) -> str:
    """Concatena mensagens no formato que o Codex entende como prompt unico."""
    parts = []
    for msg in messages:
        role = (msg.get("role") or "user").upper()
        content = msg.get("content") or ""
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        parts.append(f"[{role}]\n{content}")
    return "\n\n".join(parts)


def _call_codex(prompt: str, model: str, want_json: bool = False, timeout: int = 300) -> tuple[str, float]:
    """Roda codex exec e retorna (texto, elapsed_s). Com cache LRU + semaforo de concorrencia."""
    cache_key = _cache_key(prompt, model, want_json)
    cached = _cache_get(cache_key)
    if cached is not None:
        content, orig_elapsed = cached
        print(f"[codex-proxy] CACHE HIT model={model} orig_elapsed={orig_elapsed:.1f}s", flush=True)
        return content, 0.01  # quase instantaneo

    env = os.environ.copy()
    env["CODEX_HOME"] = CODEX_HOME

    out_file = tempfile.NamedTemporaryFile(prefix="codex_out_", suffix=".txt", delete=False)
    out_path = out_file.name
    out_file.close()

    cmd = [
        CODEX_BIN, "exec",
        "-m", model,
        "--skip-git-repo-check",
        "--sandbox", "read-only",
        "-o", out_path,
        "--color", "never",
    ]
    cmd.append("-")  # prompt via stdin

    t0 = time.time()
    # Limita concurrent codex execs (Node.js + auth pesados, Windows trava com >10 paralelos)
    last_err = None
    proc = None
    with _codex_sem:
        for attempt in range(_CODEX_RETRIES + 1):
            try:
                use_shell = sys.platform == "win32" and CODEX_BIN.lower().endswith((".cmd", ".bat"))
                proc = subprocess.run(
                    cmd, env=env, input=prompt,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=timeout, text=True, encoding="utf-8", errors="replace",
                    shell=use_shell,
                )
                if proc.returncode == 0:
                    break
                last_err = f"rc={proc.returncode}: {(proc.stderr or '')[-300:]}"
            except subprocess.TimeoutExpired:
                with _metrics_lock:
                    _metrics["errors"] += 1
                try: os.unlink(out_path)
                except Exception: pass
                raise
            except Exception as exc:
                last_err = str(exc)
            if attempt < _CODEX_RETRIES:
                wait = _CODEX_RETRY_BACKOFF * (2 ** attempt)
                print(f"[codex-proxy] retry {attempt+1}/{_CODEX_RETRIES} in {wait:.1f}s err={last_err}", flush=True)
                time.sleep(wait)

    elapsed = time.time() - t0

    if proc is None or proc.returncode != 0:
        try: os.unlink(out_path)
        except Exception: pass
        with _metrics_lock:
            _metrics["errors"] += 1
        raise RuntimeError(f"codex exec falhou apos {_CODEX_RETRIES+1} tentativas: {last_err}")

    try:
        content = Path(out_path).read_text(encoding="utf-8").strip()
    except Exception:
        content = (proc.stdout or "").strip()
    finally:
        try: os.unlink(out_path)
        except Exception: pass

    if want_json:
        # Codex as vezes envolve em ```json ... ```
        if content.startswith("```"):
            content = content.split("```", 2)
            content = content[1] if len(content) > 1 else ""
            if content.startswith("json"):
                content = content[4:].lstrip()
            content = content.rsplit("```", 1)[0].strip()

    _cache_set(cache_key, content, elapsed)
    with _metrics_lock:
        _metrics["calls"] += 1
        _metrics["total_elapsed_s"] += elapsed
    print(f"[codex-proxy] call model={model} elapsed={elapsed:.1f}s json={want_json} chars_in={len(prompt)} chars_out={len(content)}", flush=True)
    return content, elapsed


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages") or []
    if not messages:
        return jsonify({"error": {"message": "messages required", "type": "invalid_request"}}), 400

    model = _normalize_model(data.get("model"))
    response_format = data.get("response_format") or {}
    want_json = isinstance(response_format, dict) and response_format.get("type") == "json_object"

    prompt = _serialize_messages(messages)
    if want_json:
        prompt += "\n\n[INSTRUCAO DO SISTEMA]\nRetorne APENAS um objeto JSON valido, sem qualquer texto antes ou depois, sem markdown."

    try:
        content, elapsed = _call_codex(prompt, model, want_json=want_json, timeout=int(data.get("_timeout", 300)))
    except subprocess.TimeoutExpired:
        return jsonify({"error": {"message": "codex timeout", "type": "timeout"}}), 504
    except Exception as exc:
        return jsonify({"error": {"message": str(exc), "type": "codex_error"}}), 502

    # Envelopa resposta no formato OpenAI
    now = int(time.time())
    return jsonify({
        "id": f"chatcmpl-{uuid.uuid4().hex[:16]}",
        "object": "chat.completion",
        "created": now,
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": len(prompt) // 4,
            "completion_tokens": len(content) // 4,
            "total_tokens": (len(prompt) + len(content)) // 4,
        },
        "_elapsed_s": round(elapsed, 2),
    })


@app.route("/v1/embeddings", methods=["POST"])
def embeddings():
    """Proxy para Ollama (Codex nao fornece embeddings).
    Mapeia nomes OpenAI (text-embedding-3-small/large) para nomic-embed-text do Ollama.
    """
    data = request.get_json(silent=True) or {}
    m = (data.get("model") or "").strip()
    if m.startswith("text-embedding") or m in ("", "openai/text-embedding-3-small"):
        data["model"] = "nomic-embed-text"
    # Se ja for um nome Ollama, deixa como esta
    try:
        r = requests.post(f"{OLLAMA_URL}/v1/embeddings", json=data, timeout=60)
        return (r.text, r.status_code, {"Content-Type": "application/json"})
    except Exception as exc:
        return jsonify({"error": {"message": f"ollama unavailable: {exc}", "type": "embedder_error"}}), 502


@app.route("/v1/models", methods=["GET"])
def models():
    now = int(time.time())
    return jsonify({
        "object": "list",
        "data": [
            {"id": "gpt-5.5", "object": "model", "created": now, "owned_by": "openai-chatgpt"},
            {"id": "gpt-5.4-mini", "object": "model", "created": now, "owned_by": "openai-chatgpt"},
            {"id": "text-embedding-3-small", "object": "model", "created": now, "owned_by": "ollama"},
            {"id": "nomic-embed-text", "object": "model", "created": now, "owned_by": "ollama"},
        ],
    })


@app.route("/health", methods=["GET"])
def health():
    with _metrics_lock:
        m = dict(_metrics)
    avg = (m["total_elapsed_s"] / m["calls"]) if m["calls"] else 0.0
    return {
        "status": "ok",
        "backend": "codex",
        "codex_home": CODEX_HOME,
        "default_model": DEFAULT_MODEL,
        "cache": {"hits": _cache_hits, "misses": _cache_misses, "size": len(_cache), "max": _CACHE_MAX, "ttl_s": _CACHE_TTL},
        "concurrency": {"max": _MAX_CONCURRENT, "available": _codex_sem._value if hasattr(_codex_sem, "_value") else None},
        "metrics": {**m, "avg_elapsed_s": round(avg, 2)},
    }


@app.route("/metrics", methods=["GET"])
def metrics():
    """Metricas detalhadas + reset opcional via ?reset=1"""
    global _cache_hits, _cache_misses
    if request.args.get("reset") == "1":
        with _metrics_lock:
            _metrics["calls"] = 0
            _metrics["total_elapsed_s"] = 0.0
            _metrics["errors"] = 0
        _cache_hits = 0
        _cache_misses = 0
        return {"status": "reset"}
    with _metrics_lock:
        m = dict(_metrics)
    avg = (m["total_elapsed_s"] / m["calls"]) if m["calls"] else 0.0
    return {
        "calls": m["calls"],
        "errors": m["errors"],
        "total_elapsed_s": round(m["total_elapsed_s"], 1),
        "avg_elapsed_s": round(avg, 2),
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
        "cache_hit_rate": round(_cache_hits / max(1, _cache_hits + _cache_misses), 3),
        "cache_size": len(_cache),
    }


if __name__ == "__main__":
    print(f"[codex-proxy] CODEX_HOME={CODEX_HOME} default={DEFAULT_MODEL}", flush=True)
    try:
        from waitress import serve
        print(f"[codex-proxy] serving via waitress on 0.0.0.0:{PORT} threads={_MAX_CONCURRENT*2}", flush=True)
        serve(app, host="0.0.0.0", port=PORT, threads=_MAX_CONCURRENT * 2, channel_timeout=600)
    except ImportError:
        print("[codex-proxy] waitress nao instalado, fallback Flask dev server", flush=True)
        app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
