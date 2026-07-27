"""Prova o modelo LLM efetivo sem expor credenciais.

O healthcheck comum confirma apenas que o gateway responde. Este comando faz
uma chamada mínima e falha quando o provedor devolve um modelo diferente do
esperado, protegendo o deploy contra aliases e fallbacks silenciosos.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable
from urllib import error, request


CHECK_MARKER = "MIROFISH_MODEL_CHECK_OK"


class ModelCheckError(RuntimeError):
    """Falha operacional sanitizada da verificacao de modelo."""


class ModelMismatch(ModelCheckError):
    """O gateway respondeu com um modelo diferente do esperado."""


@dataclass(frozen=True)
class ModelCheckResult:
    ok: bool
    http_status: int
    requested_model: str
    expected_model: str
    effective_model: str
    content_matches: bool


def _response_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    return content if isinstance(content, str) else ""


def decode_chat_response(body: str, content_type: str = "") -> tuple[str, str]:
    """Retorna ``(modelo, conteudo)`` para JSON comum ou SSE OpenAI-compatible."""

    if "text/event-stream" not in content_type.lower() and not body.lstrip().startswith("data:"):
        payload = json.loads(body)
        return str(payload.get("model") or ""), _response_content(payload)

    model = ""
    content_parts: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        raw_event = line[5:].strip()
        if not raw_event or raw_event == "[DONE]":
            continue
        try:
            event = json.loads(raw_event)
        except json.JSONDecodeError:
            continue

        model = str(event.get("model") or model)
        choices = event.get("choices") or []
        if not choices:
            continue
        choice = choices[0] or {}
        delta = choice.get("delta") or choice.get("message") or {}
        chunk = delta.get("content")
        if isinstance(chunk, str):
            content_parts.append(chunk)

    return model, "".join(content_parts)


def check_model(
    *,
    base_url: str,
    api_key: str,
    requested_model: str,
    expected_model: str,
    timeout: float = 90,
    opener: Callable[..., Any] | None = None,
) -> ModelCheckResult:
    """Faz uma chamada minima e exige o modelo efetivo configurado."""

    if not base_url or not api_key or not requested_model or not expected_model:
        raise ModelCheckError(
            "LLM_BASE_URL, LLM_API_KEY, modelo solicitado e modelo esperado sao obrigatorios"
        )

    payload: dict[str, Any] = {
        "model": requested_model,
        "messages": [{"role": "user", "content": f"Return exactly {CHECK_MARKER}"}],
        "max_completion_tokens": 32,
        "stream": False,
    }
    if "gpt-5.6-luna" in requested_model.lower():
        payload["reasoning_effort"] = "low"

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    open_request = opener or request.urlopen

    try:
        with open_request(req, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            body = response.read().decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        detail = detail.replace(api_key, "[REDACTED]")
        raise ModelCheckError(f"gateway respondeu HTTP {exc.code}: {detail}") from exc
    except (error.URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        raise ModelCheckError(f"gateway indisponivel: {reason}") from exc

    try:
        effective_model, content = decode_chat_response(body, content_type)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ModelCheckError("gateway devolveu uma resposta LLM invalida") from exc
    result = ModelCheckResult(
        ok=effective_model == expected_model and content.strip() == CHECK_MARKER,
        http_status=status,
        requested_model=requested_model,
        expected_model=expected_model,
        effective_model=effective_model,
        content_matches=content.strip() == CHECK_MARKER,
    )

    if effective_model != expected_model:
        raise ModelMismatch(
            f"fallback silencioso detectado: esperado {expected_model}, recebido {effective_model or '<vazio>'}"
        )
    if content.strip() != CHECK_MARKER:
        raise ModelCheckError("o modelo respondeu, mas nao devolveu o marcador de verificacao")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Confirma o modelo LLM efetivo do MiroFish")
    parser.add_argument("--base-url", default=os.getenv("LLM_BASE_URL", ""))
    parser.add_argument("--requested-model", default=os.getenv("LLM_MODEL_NAME", ""))
    parser.add_argument("--expected-model", default=os.getenv("LLM_EXPECTED_EFFECTIVE_MODEL", ""))
    parser.add_argument("--timeout", type=float, default=90)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    requested_model = args.requested_model.strip()
    expected_model = args.expected_model.strip() or requested_model.rsplit("/", 1)[-1]
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OMNIROUTE_API_KEY", "")

    try:
        result = check_model(
            base_url=args.base_url.strip(),
            api_key=api_key.strip(),
            requested_model=requested_model,
            expected_model=expected_model,
            timeout=args.timeout,
        )
    except ModelCheckError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
