"""Bundle final da missao com manifesto e hashes deterministicos."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_item(value: Any) -> str:
    """Calcula hash de texto ou JSON usando representacao canonica."""
    if isinstance(value, str):
        raw = value
    else:
        raw = _canonical_json(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _freeze_forecasts(previsoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    congeladas: list[dict[str, Any]] = []
    for previsao in previsoes or []:
        item = dict(previsao)
        if item.get("status", "congelada") == "congelada":
            item["status"] = "congelada"
            congeladas.append(item)
    return congeladas


class MissionBundle:
    """Monta o manifesto final sem depender de arquivos fisicos."""

    def gerar_manifesto(
        self,
        *,
        report_id: str,
        simulation_id: str,
        custo: Any,
        poderes: list[Any],
        personas: list[Any],
        previsoes: list[dict[str, Any]],
        arquivos: list[Any],
        criado_em: str | None = None,
    ) -> dict[str, Any]:
        previsoes_congeladas = _freeze_forecasts(previsoes)
        manifesto_base = {
            "titulo": "Manifesto final da missao",
            "report_id": report_id,
            "simulation_id": simulation_id,
            "custo_total": custo,
            "poderes_mobilizados": poderes,
            "participantes": personas,
            "previsoes_congeladas": previsoes_congeladas,
            "arquivos": arquivos,
            "criado_em": criado_em or _utc_now_iso(),
        }
        item_hashes = {
            "report_id": sha256_item(report_id),
            "simulation_id": sha256_item(simulation_id),
            "custo_total": sha256_item(custo),
            "poderes_mobilizados": sha256_item(poderes),
            "participantes": sha256_item(personas),
            "previsoes_congeladas": sha256_item(previsoes_congeladas),
            "arquivos": sha256_item(arquivos),
        }
        stable_manifest = {
            key: value
            for key, value in manifesto_base.items()
            if key != "criado_em"
        }
        manifest_hash = sha256_item({**stable_manifest, "hashes": {"itens": item_hashes}})

        return {
            **manifesto_base,
            "hashes": {
                "itens": item_hashes,
                "manifesto": manifest_hash,
            },
        }


def gerar_mission_bundle(**kwargs: Any) -> dict[str, Any]:
    """Atalho funcional para gerar o manifesto final."""
    return MissionBundle().gerar_manifesto(**kwargs)
