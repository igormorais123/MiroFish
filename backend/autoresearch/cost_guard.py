"""Controle de custo para experimentos AutoResearch."""

import time
from dataclasses import dataclass, field


# Precos por 1M tokens (USD) — Anthropic pricing mar/2026
MODEL_PRICING = {
    "haiku-tasks": {"input": 0.25, "output": 1.25},
    "sonnet-tasks": {"input": 3.00, "output": 15.00},
    "opus-tasks": {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


@dataclass
class CostGuard:
    """Rastreia gastos e bloqueia quando budget atingido."""

    budget_usd: float = 5.0
    max_hours: float = 8.0
    _total_input_tokens: int = 0
    _total_output_tokens: int = 0
    _total_cost_usd: float = 0.0
    _experiment_count: int = 0
    _start_time: float = field(default_factory=time.time)

    def track(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Registra tokens consumidos e atualiza custo."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["haiku-tasks"])
        cost = (
            input_tokens * pricing["input"] / 1_000_000 +
            output_tokens * pricing["output"] / 1_000_000
        )
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost_usd += cost
        self._experiment_count += 1

    @property
    def budget_remaining(self) -> float:
        return max(0, self.budget_usd - self._total_cost_usd)

    @property
    def hours_elapsed(self) -> float:
        return (time.time() - self._start_time) / 3600

    @property
    def hours_remaining(self) -> float:
        return max(0, self.max_hours - self.hours_elapsed)

    def can_continue(self) -> bool:
        """Retorna True se ainda ha budget e tempo disponivel."""
        return self.budget_remaining > 0.001 and self.hours_remaining > 0

    def summary(self) -> dict:
        return {
            "experiments": self._experiment_count,
            "total_cost_usd": round(self._total_cost_usd, 4),
            "budget_remaining_usd": round(self.budget_remaining, 4),
            "hours_elapsed": round(self.hours_elapsed, 2),
            "hours_remaining": round(self.hours_remaining, 2),
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "cost_per_experiment": round(
                self._total_cost_usd / max(self._experiment_count, 1), 6
            ),
        }
