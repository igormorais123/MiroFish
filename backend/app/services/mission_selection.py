"""Selecao persistente de poderes e personas de uma missao."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from ..config import Config
from .power_catalog import PowerCatalog
from .power_persona_catalog import PowerPersonaCatalog


class MissionSelection:
    """Grava e recupera escolhas comerciais e sinteticas por simulacao."""

    FILENAME = "mission_selection.json"
    CONTEXT_LIMIT = 4000

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or Config.OASIS_SIMULATION_DATA_DIR

    def save(self, simulation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        selection = self.build(payload)
        selection["simulation_id"] = simulation_id
        selection["updated_at"] = datetime.now().isoformat()

        sim_dir = self._simulation_dir(simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        path = os.path.join(sim_dir, self.FILENAME)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(selection, f, ensure_ascii=False, indent=2)
        return selection

    def load(self, simulation_id: str) -> dict[str, Any]:
        path = os.path.join(self._simulation_dir(simulation_id), self.FILENAME)
        if not os.path.exists(path):
            return self.empty(simulation_id)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return self.empty(simulation_id)
        data.setdefault("simulation_id", simulation_id)
        return data

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        power_ids = self._extract_ids(payload, "selected_power_ids", "selected_powers")
        persona_ids = self._extract_ids(
            payload,
            "selected_power_persona_ids",
            "selected_personas",
            "selected_ids",
        )

        powers = PowerCatalog().estimate_selection(
            power_ids,
            base_tokens=payload.get("base_tokens", 0),
            base_value_brl=payload.get("base_value_brl", 0),
        )

        persona_catalog = PowerPersonaCatalog(max_files=PowerPersonaCatalog.DEFAULT_MAX_FILES)
        catalog = persona_catalog.build_catalog()
        selected_personas = persona_catalog.select_items(catalog, persona_ids, tipo=payload.get("tipo"))
        persona_context = persona_catalog.build_context_pack(selected_personas, max_chars=self.CONTEXT_LIMIT)

        return {
            "selected_power_ids": power_ids,
            "selected_power_persona_ids": persona_ids,
            "poderes": powers,
            "personas": {
                "count": len(selected_personas),
                "items": selected_personas,
                "contexto": persona_context,
            },
            "modo_custo": payload.get("modo_custo", "premium"),
        }

    def empty(self, simulation_id: str) -> dict[str, Any]:
        return {
            "simulation_id": simulation_id,
            "selected_power_ids": [],
            "selected_power_persona_ids": [],
            "poderes": PowerCatalog().estimate_selection([]),
            "personas": {"count": 0, "items": [], "contexto": ""},
            "modo_custo": "premium",
        }

    def _simulation_dir(self, simulation_id: str) -> str:
        return os.path.join(self.base_dir, simulation_id)

    def _extract_ids(self, payload: dict[str, Any], *keys: str) -> list[str]:
        ids: list[str] = []
        seen: set[str] = set()
        for key in keys:
            value = payload.get(key)
            if not isinstance(value, list):
                continue
            for item in value:
                item_id = item.get("id") if isinstance(item, dict) else item
                if item_id is None:
                    continue
                item_id = str(item_id)
                if item_id not in seen:
                    ids.append(item_id)
                    seen.add(item_id)
        return ids
