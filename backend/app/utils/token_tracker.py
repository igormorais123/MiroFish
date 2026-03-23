"""Rastreamento de consumo de tokens e custo por simulacao."""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

# Precos GPT-5.4-mini (USD por token)
PRICE_INPUT_PER_TOKEN = 0.30 / 1_000_000   # $0.30 / 1M tokens
PRICE_OUTPUT_PER_TOKEN = 1.20 / 1_000_000  # $1.20 / 1M tokens


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        return (self.prompt_tokens * PRICE_INPUT_PER_TOKEN +
                self.completion_tokens * PRICE_OUTPUT_PER_TOKEN)

    @property
    def cost_brl(self) -> float:
        return self.cost_usd * 5.80  # taxa aproximada

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "cost_usd": round(self.cost_usd, 6),
            "cost_brl": round(self.cost_brl, 4),
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "cost_per_minute_usd": round(
                self.cost_usd / max(self.elapsed_seconds / 60, 0.1), 6
            ),
        }


class TokenTracker:
    """Singleton thread-safe para rastrear tokens globalmente e por sessao."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._global = TokenUsage()
                    cls._instance._sessions: Dict[str, TokenUsage] = {}
        return cls._instance

    def track(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: Optional[str] = None,
    ):
        with self._lock:
            self._global.prompt_tokens += prompt_tokens
            self._global.completion_tokens += completion_tokens
            self._global.total_requests += 1
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = TokenUsage()
                sess = self._sessions[session_id]
                sess.prompt_tokens += prompt_tokens
                sess.completion_tokens += completion_tokens
                sess.total_requests += 1

    def track_error(self, session_id: Optional[str] = None):
        with self._lock:
            self._global.total_errors += 1
            if session_id and session_id in self._sessions:
                self._sessions[session_id].total_errors += 1

    def get_global(self) -> dict:
        return self._global.to_dict()

    def get_session(self, session_id: str) -> dict:
        if session_id in self._sessions:
            return self._sessions[session_id].to_dict()
        return TokenUsage().to_dict()

    def get_all_sessions(self) -> dict:
        return {sid: usage.to_dict() for sid, usage in self._sessions.items()}

    def reset_global(self):
        with self._lock:
            self._global = TokenUsage()

    def start_session(self, session_id: str):
        with self._lock:
            self._sessions[session_id] = TokenUsage()
