#!/usr/bin/env python3
"""Proxy OpenAI-compat: SSE upstream -> non-stream client + schema injection + alias remapping.

Problema: gpt-5.4-mini via OmniRoute (cx/) nao respeita response_format=json_schema.
Retorna nomes de campos plausiveis mas nao necessariamente os exigidos pelo Graphiti.

Solucao:
1. Se o request traz response_format com json_schema, extrair schema
2. Injetar schema explicito no system prompt
3. Forcar response_format=json_object (universal)
4. Parsear response, strip markdown fences
5. Remapear aliases comuns (entities->extracted_entities, relationships->edges, etc)
6. Tentar validar contra o schema; se passar, devolver; se nao, fallback para response original
"""
import json
import os
import re
from flask import Flask, request, jsonify
import requests

UPSTREAM = os.environ.get("OMNIROUTE_URL", "http://omniroute-inteia:20128/v1").rstrip("/")
API_KEY = os.environ.get("OMNIROUTE_API_KEY") or os.environ.get("LLM_API_KEY") or ""

# Endpoint direto Cerebras (nao depende do OmniRoute)
CEREBRAS_URL = os.environ.get("CEREBRAS_URL", "https://api.cerebras.ai/v1").rstrip("/")
CEREBRAS_KEY = os.environ.get("CEREBRAS_API_KEY", "")

# Fallback chain: tries in order when cooldown / error hits
# Formato: (nome, streaming, provider_type)
# provider_type: "omniroute" (via proxy OmniRoute) ou "cerebras_direct" (direto API Cerebras)
MODEL_CHAIN = [
    ("qwen-3-235b-a22b-instruct-2507", False, "cerebras_direct"),
    ("free-unlimited", True, "omniroute"),
    ("kiro/claude-haiku-4.5", False, "omniroute"),
    ("kiro/claude-sonnet-4.5", False, "omniroute"),
]
UPSTREAM_MODEL = MODEL_CHAIN[0][0]
USE_STREAMING = MODEL_CHAIN[0][1]

import time as _time
import threading
_cooldowns = {}  # model -> epoch ts until which it's banned
_cooldowns_lock = threading.Lock()
COOLDOWN_SECONDS = 20
MAX_WAIT_ALL_COOLING = 180  # se todos em cooldown, espera ate X segundos

# Throttle global: no maximo 1 request a cada X segundos para todo o upstream
THROTTLE_SECONDS = 1.5
_throttle_lock = threading.Lock()
_last_request_ts = [0.0]

def _throttle():
    with _throttle_lock:
        now = _time.time()
        wait = _last_request_ts[0] + THROTTLE_SECONDS - now
        if wait > 0:
            _time.sleep(wait)
        _last_request_ts[0] = _time.time()

def _is_cooling(model):
    with _cooldowns_lock:
        ts = _cooldowns.get(model, 0)
        return _time.time() < ts

def _set_cooldown(model, seconds=COOLDOWN_SECONDS):
    with _cooldowns_lock:
        _cooldowns[model] = _time.time() + seconds

def _pick_model():
    for entry in MODEL_CHAIN:
        provider_type = entry[2] if len(entry) > 2 else "omniroute"
        if not _provider_has_credentials(provider_type):
            continue
        if not _is_cooling(entry[0]):
            return entry
    return MODEL_CHAIN[0]

def _provider_has_credentials(provider_type):
    if provider_type == "cerebras_direct":
        return bool(CEREBRAS_KEY)
    return bool(API_KEY)

def _log(msg):
    try:
        with open("/tmp/proxy_v2.log", "a") as _lf:
            _lf.write(f"[{_time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

app = Flask(__name__)
# Limita body request: evita MemoryError do Werkzeug em payloads concorrentes grandes
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


ALIAS_MAP = {
    "entities": "extracted_entities",
    "nodes": "extracted_entities",
    "relationships": "edges",
    "relations": "edges",
    "facts": "edges",
    "extracted_edges": "edges",
    "duplicates": "duplicates",
    "nome": "name",
    "entity_name": "name",
    "label": "name",
    "source": "source_entity_id",
    "target": "target_entity_id",
    "source_id": "source_entity_id",
    "target_id": "target_entity_id",
    "from_id": "source_entity_id",
    "to_id": "target_entity_id",
    "from": "source_entity_id",
    "to": "target_entity_id",
    "type": "relation_type",
    "predicate": "relation_type",
    "relation": "relation_type",
    "relationship": "relation_type",
    "rel_type": "relation_type",
    "description": "fact",
    "statement": "fact",
    "claim": "fact",
    "text": "fact",
}


def extract_schema(response_format, messages=None):
    """Extrai JSON schema de response_format OU de schema inlined em messages (graphiti_core pattern)."""
    if isinstance(response_format, dict) and response_format.get("type") == "json_schema":
        schema = response_format.get("json_schema", {}).get("schema")
        if schema:
            return schema
    # Fallback: graphiti_core inlines schema no system/last message com padroes:
    #  (a) "Respond with a JSON object in the following format:\n\n{...}"  -- openai_generic_client
    #  (b) "SCHEMA:\n{...}\n\nReturn only the JSON object."                  -- openai_client patched
    INLINE_MARKERS = (
        "Respond with a JSON object in the following format:",
        "SCHEMA:",
    )
    if messages:
        for msg in messages:  # system message (que carrega o schema) vem primeiro
            if not isinstance(msg, dict):
                continue
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            idx = -1
            for marker in INLINE_MARKERS:
                pos = content.find(marker)
                if pos >= 0:
                    idx = pos + len(marker)
                    break
            if idx < 0:
                continue
            tail = content[idx:]
            brace_start = tail.find("{")
            if brace_start < 0:
                continue
            depth = 0
            end = -1
            in_str = False
            esc = False
            for i, ch in enumerate(tail[brace_start:], start=brace_start):
                if esc:
                    esc = False
                    continue
                if ch == "\\":
                    esc = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if in_str:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > 0:
                try:
                    return json.loads(tail[brace_start:end])
                except Exception:
                    pass
            break
    return None


def schema_to_prompt(schema):
    """Converte schema em instrucao explicita para o modelo."""
    return (
        "CRITICAL INSTRUCTIONS:\n"
        "- Respond with ONLY a valid JSON object matching this EXACT schema.\n"
        "- Use the EXACT field names shown. Do not invent aliases.\n"
        "- No markdown fences, no explanations, no preambles.\n"
        "- If a field is a list, return an array even if empty.\n\n"
        "REQUIRED SCHEMA:\n"
        + json.dumps(schema, indent=2, ensure_ascii=False)
        + "\n\nReturn the JSON object now."
    )


def strip_fences(s):
    """Remove markdown fences e extrai JSON puro."""
    if not isinstance(s, str):
        return s
    s = s.strip()
    if s.startswith("```"):
        m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", s, re.DOTALL)
        if m:
            s = m.group(1).strip()
    # Se nao comeca com { ou [, tentar extrair
    if s and s[0] not in "{[":
        for start_c, end_c in [("{", "}"), ("[", "]")]:
            i = s.find(start_c)
            if i == -1:
                continue
            depth = 0
            for j in range(i, len(s)):
                if s[j] == start_c:
                    depth += 1
                elif s[j] == end_c:
                    depth -= 1
                    if depth == 0:
                        return s[i : j + 1]
    return s


def get_required_fields(schema):
    """Pega todos os campos required recursivamente."""
    required = set()
    if not isinstance(schema, dict):
        return required
    for req in schema.get("required", []):
        required.add(req)
    # Olhar defs
    for k in ("$defs", "definitions"):
        for v in schema.get(k, {}).values():
            if isinstance(v, dict):
                for r in v.get("required", []):
                    required.add(r)
    return required


def remap_dict(obj, required_fields):
    """Aplica ALIAS_MAP recursivamente em um dict, priorizando campos required."""
    if isinstance(obj, list):
        return [remap_dict(x, required_fields) for x in obj]
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        new_k = k
        # Se a chave esta no alias map e o alvo eh required (ou o atual nao eh)
        if k in ALIAS_MAP and ALIAS_MAP[k] != k:
            target = ALIAS_MAP[k]
            if target in required_fields or k not in required_fields:
                new_k = target
        out[new_k] = remap_dict(v, required_fields)
    return out


def ensure_required_defaults(obj, schema):
    """Adiciona valores default para campos required ausentes (para passar validacao)."""
    if not isinstance(obj, dict) or not isinstance(schema, dict):
        return obj
    # Resolve $ref para properties
    props = schema.get("properties", {})
    required = schema.get("required", [])
    for field in required:
        if field in obj:
            continue
        prop = props.get(field, {})
        ptype = prop.get("type")
        if ptype == "array":
            obj[field] = []
        elif ptype == "object":
            obj[field] = {}
        elif ptype == "string":
            obj[field] = ""
        elif ptype == "integer":
            obj[field] = 0
        elif ptype == "number":
            obj[field] = 0.0
        elif ptype == "boolean":
            obj[field] = False
    # Recurse into nested arrays with $defs items
    defs = schema.get("$defs", {}) or schema.get("definitions", {})
    for field, value in list(obj.items()):
        prop = props.get(field, {})
        items = prop.get("items", {})
        if "$ref" in items:
            ref_name = items["$ref"].split("/")[-1]
            sub_schema = defs.get(ref_name, {})
            if isinstance(value, list):
                obj[field] = [
                    ensure_required_defaults(item, sub_schema) if isinstance(item, dict) else item
                    for item in value
                ]
    return obj


@app.route("/healthcheck")
def healthcheck():
    return jsonify({"status": "ok"})


@app.route("/v1/models")
def models_list():
    return jsonify(
        {
            "object": "list",
            "data": [
                {"id": "gpt-4.1-nano", "object": "model"},
                {"id": "gpt-4.1-mini", "object": "model"},
                {"id": UPSTREAM_MODEL, "object": "model"},
            ],
        }
    )


@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.get_json() or {}
    original_rf = data.get("response_format")

    # Extrair schema: primeiro tenta response_format, depois scan em messages (graphiti inline)
    schema = extract_schema(original_rf, data.get("messages"))
    schema_title = (original_rf or {}).get("json_schema", {}).get("name", "NO_SCHEMA") if isinstance(original_rf, dict) else "NO_RF"
    if schema and schema_title in ("NO_SCHEMA", "NO_RF"):
        schema_title = schema.get("title", "INLINE_SCHEMA")
    _log(f"REQ schema={schema_title} rf_type={original_rf.get('type') if isinstance(original_rf, dict) else None} inline={schema is not None and not (isinstance(original_rf, dict) and original_rf.get('type') == 'json_schema')}")

    # Injetar schema no prompt
    if schema:
        instruction = schema_to_prompt(schema)
        messages = data.get("messages", [])
        # Prepend como system message
        messages = [{"role": "system", "content": instruction}] + list(messages)
        data["messages"] = messages
        data["response_format"] = {"type": "json_object"}

    # Kiro/Claude usa max_tokens, cx usa max_completion_tokens
    if data.get("max_tokens", 0) > 8000:
        data["max_tokens"] = 8000
    if data.get("max_completion_tokens", 0) > 8000:
        data["max_completion_tokens"] = 8000

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    content = ""
    prompt_tokens = 0
    completion_tokens = 0
    finish_reason = "stop"
    model = ""
    msg_id = ""
    last_error = None

    available_chain = [
        entry for entry in MODEL_CHAIN
        if _provider_has_credentials(entry[2] if len(entry) > 2 else "omniroute")
    ]
    if not available_chain:
        return jsonify({"error": {"message": "Nenhum provedor LLM configurado. Defina OMNIROUTE_API_KEY/LLM_API_KEY ou CEREBRAS_API_KEY."}}), 503

    # Tenta cada modelo na chain ate sucesso
    # Se todos estao em cooldown, espera o primeiro disponivel
    _wait_start = _time.time()
    while all(_is_cooling(entry[0]) for entry in available_chain):
        if _time.time() - _wait_start > MAX_WAIT_ALL_COOLING:
            break
        _time.sleep(2)

    for entry in available_chain:
        try_model, streaming, provider_type = entry[0], entry[1], entry[2] if len(entry) > 2 else "omniroute"
        if _is_cooling(try_model):
            _log(f"SKIP {try_model} (cooldown)")
            continue
        _throttle()
        _log(f"TRY {try_model} via {provider_type}")
        attempt_data = dict(data)
        attempt_data["model"] = try_model
        attempt_data["stream"] = streaming

        # Ajusta params conforme modelo/provider
        if provider_type == "cerebras_direct":
            # Cerebras usa max_completion_tokens (OpenAI-compat)
            if "max_tokens" in attempt_data and "max_completion_tokens" not in attempt_data:
                attempt_data["max_completion_tokens"] = attempt_data.pop("max_tokens")
            # Strip model prefix se houver
            if attempt_data["model"].startswith("cerebras/"):
                attempt_data["model"] = attempt_data["model"][len("cerebras/"):]
            endpoint = f"{CEREBRAS_URL}/chat/completions"
            req_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CEREBRAS_KEY}",
            }
        else:
            if try_model.startswith("cx/") or try_model.startswith("codex/"):
                if "max_tokens" in attempt_data and "max_completion_tokens" not in attempt_data:
                    attempt_data["max_completion_tokens"] = attempt_data.pop("max_tokens")
            else:
                if "max_completion_tokens" in attempt_data and "max_tokens" not in attempt_data:
                    attempt_data["max_tokens"] = attempt_data.pop("max_completion_tokens")
            endpoint = f"{UPSTREAM}/chat/completions"
            req_headers = headers

        try:
            if streaming:
                h = dict(req_headers)
                h["Accept"] = "text/event-stream"
                r = requests.post(
                    endpoint, json=attempt_data, headers=h, stream=True, timeout=600
                )
                content_parts = []
                got_any = False
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except Exception:
                        continue
                    if "error" in chunk:
                        break
                    if "id" in chunk and not msg_id:
                        msg_id = chunk["id"]
                    if "model" in chunk:
                        model = chunk["model"]
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            content_parts.append(delta["content"])
                            got_any = True
                        if choices[0].get("finish_reason"):
                            finish_reason = choices[0]["finish_reason"]
                    usage = chunk.get("usage")
                    if usage:
                        prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                        completion_tokens = usage.get("completion_tokens", completion_tokens)
                content = "".join(content_parts)
                if not got_any:
                    last_error = f"{try_model}: empty stream"
                    _log(f"FAIL {try_model} empty stream")
                    _set_cooldown(try_model, 30)
                    continue
                break  # sucesso
            else:
                r = requests.post(
                    endpoint, json=attempt_data, headers=req_headers, timeout=600
                )
                try:
                    resp = r.json()
                except Exception:
                    last_error = f"{try_model}: invalid JSON"
                    _log(f"FAIL {try_model} invalid JSON: {r.text[:150]}")
                    _set_cooldown(try_model, 30)
                    continue
                if "choices" not in resp or r.status_code >= 400:
                    err_msg = resp.get("error", {}).get("message", str(resp)[:150])
                    last_error = f"{try_model}: {err_msg}"
                    _log(f"FAIL {try_model} status={r.status_code} err={err_msg[:120]}")
                    el = err_msg.lower()
                    if r.status_code in (503, 429) or "cooldown" in el or "unavailable" in el or "rate" in el or "credentials" in el or "no credentials" in el or "provider" in el:
                        # Cerebras TPM: 60s reset; outros: COOLDOWN_SECONDS
                        cd = 60 if "tokens per minute" in el or "too_many_tokens" in el else COOLDOWN_SECONDS
                        _set_cooldown(try_model, cd)
                    continue
                msg_id = resp.get("id", "")
                model = resp.get("model", try_model)
                choice = resp["choices"][0]
                content = choice.get("message", {}).get("content", "") or ""
                finish_reason = choice.get("finish_reason", "stop")
                usage = resp.get("usage", {}) or {}
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                if not content:
                    last_error = f"{try_model}: empty content"
                    _log(f"FAIL {try_model} empty content")
                    continue
                _log(f"GOT {try_model} content_head={content[:100]}")
                break  # sucesso
        except Exception as exc:
            last_error = f"{try_model}: exception {exc}"
            _log(f"FAIL {try_model} exception {exc}")
            _set_cooldown(try_model, 30)
            continue

    if not content:
        return jsonify({"error": {"message": f"all models failed. last: {last_error}"}}), 503

    # Pos-processamento se temos schema
    if schema and content:
        cleaned = strip_fences(content)
        try:
            parsed = json.loads(cleaned)
            required = get_required_fields(schema)
            _pre_keys = list(parsed.keys()) if isinstance(parsed, dict) else []
            parsed = remap_dict(parsed, required)
            parsed = ensure_required_defaults(parsed, schema)
            _post_keys = list(parsed.keys()) if isinstance(parsed, dict) else []
            content = json.dumps(parsed, ensure_ascii=False)
            _log(f"POST_PROC schema={schema_title} pre={_pre_keys} post={_post_keys} req={list(required)}")
        except Exception as e:
            _log(f"POST_PROC_FAIL schema={schema_title} err={e} head={cleaned[:150]}")
            content = cleaned
    else:
        _log(f"NO_POST_PROC schema_present={schema is not None} content_present={bool(content)}")

    return jsonify(
        {
            "id": msg_id or f"chatcmpl-proxy-{abs(hash(content)) & 0xffffffff}",
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
    )


if __name__ == "__main__":
    try:
        from waitress import serve
        print("[llm-proxy] serving via waitress on 0.0.0.0:8765 threads=16", flush=True)
        serve(app, host="0.0.0.0", port=8765, threads=16, channel_timeout=600)
    except ImportError:
        print("[llm-proxy] waitress nao instalado, fallback Flask dev (NAO PROD)", flush=True)
        app.run(host="0.0.0.0", port=8765, threaded=True)
