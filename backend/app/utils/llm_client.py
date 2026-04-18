"""
Cliente unificado de LLM.

Opera sobre provedores compativeis com a API OpenAI e prioriza a configuracao
OmniRoute-first definida no backend INTEIA.

Usa requests em vez do SDK OpenAI/httpx para compatibilidade com OmniRouter
(httpx trava com SSE streaming quando stream nao esta no body).
"""

import json
import random
import re
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import requests as http_requests

from ..config import Config
from .token_tracker import TokenTracker

_tracker = TokenTracker()


@dataclass
class _ChatMessage:
    content: str = ""
    role: str = "assistant"

@dataclass
class _ChatChoice:
    message: Any = None

@dataclass
class _ChatUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

@dataclass
class _ChatResponse:
    choices: List[Any] = None
    usage: Any = None


class LLMClient:
    """Cliente de LLM com suporte a alias de modelos, timeout e retry."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = (base_url or Config.LLM_BASE_URL).rstrip("/")
        self.model = Config.resolve_model_name(model or Config.LLM_MODEL_NAME)
        self.timeout = Config.LLM_TIMEOUT_SECONDS
        self.max_retries = Config.LLM_MAX_RETRIES

        if not self.api_key:
            raise ValueError("LLM_API_KEY ou OMNIROUTE_API_KEY nao configurada")

    def _request_with_retry(self, **kwargs):
        """Executa chamada ao provider via requests (compativel com OmniRouter)."""
        kwargs["stream"] = False

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Connection": "close",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            started_at = time.perf_counter()
            try:
                resp = http_requests.post(url, headers=headers, json=kwargs, timeout=self.timeout)
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 1)

                if resp.status_code != 200:
                    raise RuntimeError(f"LLM retornou status {resp.status_code}: {resp.text[:300]}")

                data = resp.json()

                # Parse OpenAI-format response
                choices = []
                for c in data.get("choices", []):
                    msg = c.get("message", {})
                    choices.append(_ChatChoice(message=_ChatMessage(
                        content=msg.get("content", ""),
                        role=msg.get("role", "assistant"),
                    )))

                # Parse Anthropic-format response (content array)
                if not choices and data.get("content"):
                    text = "".join(
                        p.get("text", "") for p in data["content"]
                        if isinstance(p, dict) and p.get("type") == "text"
                    )
                    choices = [_ChatChoice(message=_ChatMessage(content=text))]

                usage_data = data.get("usage", {})
                usage = _ChatUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0) or 0,
                    completion_tokens=usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0) or 0,
                )

                return _ChatResponse(choices=choices, usage=usage), elapsed_ms, attempt

            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                # Backoff exponencial 5-30s + jitter (2026-04-18, Phase 2 Task 4)
                # Sobrevive a downtime de ~2min do OmniRoute quando max_retries=8
                base = min(5 * (2 ** (attempt - 1)), 30)
                jitter = random.uniform(0, base * 0.3)
                time.sleep(base + jitter)

        raise last_error

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Envia requisicao de chat e retorna texto limpo."""
        model_name = Config.resolve_model_name(self.model)
        # GPT-5.4+ exige max_completion_tokens em vez de max_tokens
        token_key = "max_completion_tokens" if "gpt-5" in model_name or "o1" in model_name or "o3" in model_name or "o4" in model_name else "max_tokens"
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            token_key: max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        from .logger import get_logger
        _logger = get_logger('mirofish.llm')

        try:
            response, elapsed_ms, attempt = self._request_with_retry(**kwargs)
            if attempt > 1:
                _logger.info(f"LLM respondeu apos {attempt} tentativas ({elapsed_ms}ms)")
        except Exception as exc:
            _tracker.track_error(session_id=session_id)
            _logger.error(f"LLM falhou apos {self.max_retries} tentativas: {str(exc)}")
            raise

        usage = getattr(response, 'usage', None)
        if usage:
            _tracker.track(
                prompt_tokens=getattr(usage, 'prompt_tokens', 0) or 0,
                completion_tokens=getattr(usage, 'completion_tokens', 0) or 0,
                session_id=session_id,
            )

        content = response.choices[0].message.content
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Envia requisicao em modo JSON e retorna objeto desserializado."""
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            session_id=session_id,
        )
        cleaned = response.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"LLM retornou JSON invalido: {cleaned}")
