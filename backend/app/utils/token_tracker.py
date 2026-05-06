"""Rastreamento de consumo de tokens, custo tecnico e valor INTEIA."""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

PRICEBOOK_NAME = "gpt-5.5-pro-rapido-referencia"
PRICE_INPUT_USD_PER_1M_TOKENS = 5.00
PRICE_OUTPUT_USD_PER_1M_TOKENS = 20.00
INTEIA_MARKUP_MULTIPLIER = 5.0
DEFAULT_USD_BRL_EXCHANGE_RATE = 5.80

# Compatibilidade com imports existentes: USD por token.
PRICE_INPUT_PER_TOKEN = PRICE_INPUT_USD_PER_1M_TOKENS / 1_000_000
PRICE_OUTPUT_PER_TOKEN = PRICE_OUTPUT_USD_PER_1M_TOKENS / 1_000_000


def _round_usd(value: float) -> float:
    return round(value, 6)


def _round_brl(value: float) -> float:
    return round(value, 4)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    start_time: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def api_reference_usd(self) -> float:
        return (self.prompt_tokens * PRICE_INPUT_PER_TOKEN +
                self.completion_tokens * PRICE_OUTPUT_PER_TOKEN)

    @property
    def api_reference_brl(self) -> float:
        return self.api_reference_usd * DEFAULT_USD_BRL_EXCHANGE_RATE

    @property
    def inteia_value_usd(self) -> float:
        return self.api_reference_usd * INTEIA_MARKUP_MULTIPLIER

    @property
    def inteia_value_brl(self) -> float:
        return self.inteia_value_usd * DEFAULT_USD_BRL_EXCHANGE_RATE

    @property
    def cost_usd(self) -> float:
        return self.api_reference_usd

    @property
    def cost_brl(self) -> float:
        return self.api_reference_brl

    @property
    def elapsed_seconds(self) -> float:
        end_time = self.finished_at if self.finished_at is not None else time.time()
        return end_time - self.start_time

    @property
    def state(self) -> str:
        return "concluida" if self.finished_at is not None else "em_andamento"

    def finish(self):
        self.finished_at = time.time()

    def add_tokens(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_requests += 1

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "cost_usd": _round_usd(self.cost_usd),
            "cost_brl": _round_brl(self.cost_brl),
            "api_reference_usd": _round_usd(self.api_reference_usd),
            "api_reference_brl": _round_brl(self.api_reference_brl),
            "inteia_value_usd": _round_usd(self.inteia_value_usd),
            "inteia_value_brl": _round_brl(self.inteia_value_brl),
            "markup_multiplier": INTEIA_MARKUP_MULTIPLIER,
            "pricebook": PRICEBOOK_NAME,
            "rotulo_valor": "Valor operacional INTEIA",
            "rotulo_custo": "Custo tecnico de referencia da API",
            "estado": self.state,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "cost_per_minute_usd": round(
                self.cost_usd / max(self.elapsed_seconds / 60, 0.1), 6
            ),
        }


@dataclass
class TokenPhase(TokenUsage):
    phase_id: str = ""
    label: str = ""

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "phase_id": self.phase_id,
            "label": self.label,
            "rotulo": self.label,
        })
        return data


class TokenTracker:
    """Singleton thread-safe para rastrear tokens globalmente e por sessao."""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._global = TokenUsage()
                    cls._instance._sessions: Dict[str, TokenUsage] = {}
                    cls._instance._phases: Dict[str, Dict[str, TokenPhase]] = {}
        if not hasattr(cls._instance, "_phases"):
            cls._instance._phases = {}
        return cls._instance

    def track(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: Optional[str] = None,
        phase_id: Optional[str] = None,
    ):
        with self._lock:
            self._global.add_tokens(prompt_tokens, completion_tokens)
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = TokenUsage()
                self._sessions[session_id].add_tokens(prompt_tokens, completion_tokens)

                if phase_id:
                    phases = self._phases.setdefault(session_id, {})
                    if phase_id not in phases:
                        phases[phase_id] = TokenPhase(
                            phase_id=phase_id,
                            label=f"Fase {phase_id}",
                        )
                    phases[phase_id].add_tokens(prompt_tokens, completion_tokens)

    def start_phase(self, session_id: str, phase_id: str, label: str):
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = TokenUsage()
            phases = self._phases.setdefault(session_id, {})
            if phase_id in phases:
                if label:
                    phases[phase_id].label = label
                return
            phases[phase_id] = TokenPhase(
                phase_id=phase_id,
                label=label or f"Fase {phase_id}",
            )

    def finish_phase(self, session_id: str, phase_id: str):
        with self._lock:
            phase = self._phases.get(session_id, {}).get(phase_id)
            if phase:
                phase.finish()

    def track_error(self, session_id: Optional[str] = None):
        with self._lock:
            self._global.total_errors += 1
            if session_id and session_id in self._sessions:
                self._sessions[session_id].total_errors += 1

    def get_global(self) -> dict:
        with self._lock:
            return self._global.to_dict()

    def get_session(self, session_id: str) -> dict:
        with self._lock:
            if session_id in self._sessions:
                data = self._sessions[session_id].to_dict()
            else:
                data = TokenUsage().to_dict()
            data["phases"] = self._session_phases_to_dict(session_id)
            return data

    def get_all_sessions(self) -> dict:
        with self._lock:
            return {
                sid: self.get_session(sid)
                for sid in list(self._sessions)
            }

    def reset_global(self):
        with self._lock:
            self._global = TokenUsage()

    def start_session(self, session_id: str):
        with self._lock:
            self._sessions[session_id] = TokenUsage()
            self._phases[session_id] = {}

    def reset_all(self):
        with self._lock:
            self._global = TokenUsage()
            self._sessions.clear()
            self._phases.clear()

    def _session_phases_to_dict(self, session_id: str) -> dict:
        with self._lock:
            return {
                phase_id: phase.to_dict()
                for phase_id, phase in self._phases.get(session_id, {}).items()
            }
