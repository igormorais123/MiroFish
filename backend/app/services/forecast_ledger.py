"""Livro deterministico de previsoes operacionais."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


VALID_FORECAST_STATUSES = {"congelada", "em_observacao", "confirmada", "revertida"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_forecast_id(
    enunciado: str,
    janela: str,
    base: Any,
    sinais: Any,
    grau_confianca_operacional: Any,
) -> str:
    """Gera um id estavel a partir do conteudo essencial da previsao."""
    payload = {
        "base": base,
        "enunciado": enunciado,
        "grau_confianca_operacional": grau_confianca_operacional,
        "janela": janela,
        "sinais": sinais,
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"prev_{digest[:16]}"


@dataclass(frozen=True)
class ForecastEntry:
    id: str
    enunciado: str
    janela: str
    base: Any
    sinais: Any
    grau_confianca_operacional: Any
    status: str
    criado_em: str
    probability: float | None = None
    prior: float | None = None
    base_rate: float | None = None
    reference_class: str | None = None
    indicators: Any = None
    resolution_source: str | None = None
    resolved_at: str | None = None
    outcome: bool | None = None
    brier_score: float | None = None
    log_loss: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ForecastLedger:
    """Registro em memoria com deduplicacao por id estavel."""

    def __init__(self, previsoes: list[dict[str, Any]] | None = None) -> None:
        self._entries: dict[str, ForecastEntry] = {}
        for previsao in previsoes or []:
            self.registrar_previsao(**previsao)

    def registrar_previsao(
        self,
        *,
        enunciado: str,
        janela: str,
        base: Any,
        sinais: Any,
        grau_confianca_operacional: Any,
        status: str = "congelada",
        criado_em: str | None = None,
        id: str | None = None,
        probability: float | None = None,
        prior: float | None = None,
        base_rate: float | None = None,
        reference_class: str | None = None,
        indicators: Any = None,
        resolution_source: str | None = None,
        resolved_at: str | None = None,
        outcome: bool | None = None,
        brier_score: float | None = None,
        log_loss: float | None = None,
    ) -> dict[str, Any]:
        """Registra uma previsao e retorna a entrada existente quando houver duplicata."""
        if status not in VALID_FORECAST_STATUSES:
            raise ValueError(f"status de previsao invalido: {status}")
        probability = _validate_probability(probability, "probability")
        prior = _validate_probability(prior, "prior")
        base_rate = _validate_probability(base_rate, "base_rate")
        brier_score = _validate_optional_number(brier_score, "brier_score")
        log_loss = _validate_optional_number(log_loss, "log_loss")
        if brier_score is None:
            brier_score = _brier_score(probability, outcome)
        if log_loss is None:
            log_loss = _log_loss(probability, outcome)

        forecast_id = id or stable_forecast_id(
            enunciado=enunciado,
            janela=janela,
            base=base,
            sinais=sinais,
            grau_confianca_operacional=grau_confianca_operacional,
        )
        if forecast_id in self._entries:
            return self._entries[forecast_id].to_dict()

        entry = ForecastEntry(
            id=forecast_id,
            enunciado=enunciado,
            janela=janela,
            base=base,
            sinais=sinais,
            grau_confianca_operacional=grau_confianca_operacional,
            status=status,
            criado_em=criado_em or _utc_now_iso(),
            probability=probability,
            prior=prior,
            base_rate=base_rate,
            reference_class=reference_class,
            indicators=indicators,
            resolution_source=resolution_source,
            resolved_at=resolved_at,
            outcome=outcome,
            brier_score=brier_score,
            log_loss=log_loss,
        )
        self._entries[forecast_id] = entry
        return entry.to_dict()

    def listar_previsoes(self) -> list[dict[str, Any]]:
        """Retorna previsoes em ordem deterministica por id."""
        return [self._entries[key].to_dict() for key in sorted(self._entries)]

    def exportar_resumo(self) -> str:
        """Exporta uma sintese em portugues com contagens por status."""
        counts = Counter(entry.status for entry in self._entries.values())
        total = len(self._entries)
        partes = [
            f"Livro de previsoes: {total} previsoes registradas.",
            f"Congeladas: {counts['congelada']}.",
            f"Em observacao: {counts['em_observacao']}.",
            f"Confirmadas: {counts['confirmada']}.",
            f"Revertidas: {counts['revertida']}.",
        ]
        return " ".join(partes)

    def exportar_calibracao(self) -> dict[str, Any]:
        """Retorna metricas deterministicas de calibracao para previsoes resolvidas."""
        entries = self.listar_previsoes()
        resolved = [entry for entry in entries if entry.get("outcome") is not None]
        probabilistic = [entry for entry in resolved if entry.get("probability") is not None]
        brier_scores = [entry["brier_score"] for entry in probabilistic if entry.get("brier_score") is not None]
        log_losses = [entry["log_loss"] for entry in probabilistic if entry.get("log_loss") is not None]
        counts = Counter(entry["status"] for entry in entries)

        return {
            "schema": "mirofish.forecast_calibration.v1",
            "total": len(entries),
            "resolved": len(resolved),
            "probabilistic": len(probabilistic),
            "mean_brier_score": _mean(brier_scores),
            "mean_log_loss": _mean(log_losses),
            "status_counts": {status: counts[status] for status in sorted(VALID_FORECAST_STATUSES)},
        }

    def exportar_grafico_deterministico(self) -> dict[str, Any]:
        """Retorna series estaveis para graficos sem depender de bibliotecas externas."""
        calibration = self.exportar_calibracao()
        status_labels = {
            "congelada": "Congeladas",
            "em_observacao": "Em observacao",
            "confirmada": "Confirmadas",
            "revertida": "Revertidas",
        }
        return {
            "schema": "mirofish.forecast_chart_data.v1",
            "series": [
                {
                    "id": "status_counts",
                    "label": "Previsoes por status",
                    "points": [
                        {"label": status_labels[status], "value": calibration["status_counts"][status]}
                        for status in sorted(status_labels)
                    ],
                },
                {
                    "id": "calibration_quality",
                    "label": "Calibracao",
                    "points": [
                        {"label": "Resolvidas", "value": calibration["resolved"]},
                        {"label": "Com probabilidade", "value": calibration["probabilistic"]},
                        {"label": "Brier medio", "value": calibration["mean_brier_score"]},
                        {"label": "Log-loss medio", "value": calibration["mean_log_loss"]},
                    ],
                },
            ],
        }


def _validate_probability(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if numeric < 0 or numeric > 1:
        raise ValueError(f"{field_name} deve estar entre 0 e 1")
    return numeric


def _validate_optional_number(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{field_name} deve ser finito")
    return numeric


def _brier_score(probability: float | None, outcome: bool | None) -> float | None:
    if probability is None or outcome is None:
        return None
    observed = 1.0 if outcome else 0.0
    return round((probability - observed) ** 2, 6)


def _log_loss(probability: float | None, outcome: bool | None) -> float | None:
    if probability is None or outcome is None:
        return None
    observed = 1.0 if outcome else 0.0
    clipped = min(max(probability, 1e-15), 1 - 1e-15)
    loss = -(observed * math.log(clipped) + (1 - observed) * math.log(1 - clipped))
    return round(loss, 6)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)

