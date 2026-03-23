"""
Cliente unificado de LLM.

Opera sobre provedores compativeis com a API OpenAI e prioriza a configuracao
OmniRoute-first definida no backend INTEIA.
"""

import json
import re
import time
from typing import Optional, Dict, Any, List

from openai import OpenAI

from ..config import Config
from .token_tracker import TokenTracker

_tracker = TokenTracker()


class LLMClient:
    """Cliente de LLM com suporte a alias de modelos, timeout e retry."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = Config.resolve_model_name(model or Config.LLM_MODEL_NAME)
        self.timeout = Config.LLM_TIMEOUT_SECONDS
        self.max_retries = Config.LLM_MAX_RETRIES

        if not self.api_key:
            raise ValueError("LLM_API_KEY ou OMNIROUTE_API_KEY nao configurada")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def _request_with_retry(self, **kwargs):
        """Executa a chamada ao provider com retry simples e observabilidade minima."""
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            started_at = time.perf_counter()
            try:
                response = self.client.chat.completions.create(**kwargs)
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 1)
                return response, elapsed_ms, attempt
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(1 * attempt, 3))  # Backoff: 1s, 2s, 3s

        raise last_error

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Envia uma requisicao de chat e retorna o texto final limpo."""
        model_name = Config.resolve_model_name(self.model)
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
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

        # Extrair usage de tokens da resposta
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
        """Envia requisicao em modo JSON e retorna o objeto desserializado."""
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            session_id=session_id,
        )
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM retornou JSON invalido: {cleaned_response}")
