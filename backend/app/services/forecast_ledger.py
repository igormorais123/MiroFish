"""Livro deterministico de previsoes operacionais."""

from __future__ import annotations

import hashlib
import json
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
    ) -> dict[str, Any]:
        """Registra uma previsao e retorna a entrada existente quando houver duplicata."""
        if status not in VALID_FORECAST_STATUSES:
            raise ValueError(f"status de previsao invalido: {status}")

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

