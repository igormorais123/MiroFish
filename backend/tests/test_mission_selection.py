"""Testes da selecao persistente de missao."""
from __future__ import annotations

from app.services.mission_selection import MissionSelection


def test_build_consolida_poderes_e_personas_sem_duplicar_ids():
    selection = MissionSelection().build({
        "selected_power_ids": ["modo_rapido", {"id": "bundle_supremo"}, "modo_rapido"],
        "selected_power_persona_ids": ["inexistente"],
        "base_tokens": 1000,
        "base_value_brl": 100,
    })

    assert selection["selected_power_ids"] == ["modo_rapido", "bundle_supremo"]
    assert selection["selected_power_persona_ids"] == ["inexistente"]
    assert selection["poderes"]["tokens_estimados"] == 2500
    assert selection["poderes"]["valor_estimado_brl"] == 1450
    assert selection["personas"]["count"] == 0


def test_save_e_load_preservam_missao(tmp_path):
    store = MissionSelection(base_dir=str(tmp_path))

    saved = store.save("sim_123", {
        "selected_power_ids": ["forecast_ledger"],
        "modo_custo": "premium_rapido",
    })
    loaded = store.load("sim_123")

    assert saved["simulation_id"] == "sim_123"
    assert loaded["simulation_id"] == "sim_123"
    assert loaded["selected_power_ids"] == ["forecast_ledger"]
    assert loaded["modo_custo"] == "premium_rapido"
    assert loaded["updated_at"]


def test_load_sem_arquivo_retorna_estado_vazio(tmp_path):
    loaded = MissionSelection(base_dir=str(tmp_path)).load("sim_vazio")

    assert loaded["simulation_id"] == "sim_vazio"
    assert loaded["selected_power_ids"] == []
    assert loaded["personas"]["count"] == 0
