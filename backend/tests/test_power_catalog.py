"""Testes do catalogo formal de poderes comerciais."""
from __future__ import annotations

from app.services.power_catalog import PowerCatalog


EXPECTED_POWER_IDS = [
    "oraculo_premium",
    "modo_rapido",
    "corte_helena",
    "consultores_lendarios",
    "vox_personas",
    "eleitores_sinteticos",
    "painel_judicial",
    "painel_parlamentar",
    "contrarians",
    "leitura_profunda",
    "forecast_ledger",
    "bundle_supremo",
]


def test_catalogo_completo_com_campos_obrigatorios():
    powers = PowerCatalog().list_powers()

    assert [power["id"] for power in powers] == EXPECTED_POWER_IDS
    for power in powers:
        assert set(power) == {
            "id",
            "nome",
            "descricao",
            "categoria",
            "custo_tipo",
            "multiplicador_tokens",
            "custo_fixo_brl",
            "impacto",
            "recomendado_para",
            "ativo_por_padrao",
        }
        assert power["nome"]
        assert power["descricao"]
        assert power["categoria"]
        assert power["custo_tipo"] in {"multiplicador_tokens", "custo_fixo_brl", "incluido"}
        assert isinstance(power["recomendado_para"], list)
        assert isinstance(power["ativo_por_padrao"], bool)


def test_list_powers_filtra_por_custo_tipo_e_categoria_mantendo_ordem():
    catalog = PowerCatalog()

    fixed = catalog.list_powers(tipo="custo_fixo_brl")
    report = catalog.list_powers(categoria="relatorio")

    assert [power["id"] for power in fixed] == ["corte_helena", "bundle_supremo"]
    assert [power["id"] for power in report] == ["oraculo_premium", "corte_helena", "leitura_profunda"]


def test_get_power_retorna_item_por_id_e_none_para_desconhecido():
    catalog = PowerCatalog()

    power = catalog.get_power("modo_rapido")

    assert power is not None
    assert power["id"] == "modo_rapido"
    assert catalog.get_power("nao_existe") is None


def test_estimate_selection_ignora_desconhecido_com_nota_e_preserva_ordem():
    estimate = PowerCatalog().estimate_selection(
        ["bundle_supremo", "nao_existe", "modo_rapido"],
        base_tokens=1000,
        base_value_brl=200,
    )

    assert [power["id"] for power in estimate["poderes_selecionados"]] == [
        "modo_rapido",
        "bundle_supremo",
    ]
    assert any("nao_existe" in nota for nota in estimate["notas_operacionais"])


def test_modo_rapido_multiplica_tokens_e_valor_base():
    estimate = PowerCatalog().estimate_selection(
        ["modo_rapido"],
        base_tokens=1000,
        base_value_brl=100,
    )

    assert estimate["multiplicador_total"] == 2.5
    assert estimate["tokens_estimados"] == 2500
    assert estimate["custo_fixo_brl"] == 0
    assert estimate["valor_estimado_brl"] == 250
    assert any("Modo Rápido" in nota for nota in estimate["notas_operacionais"])


def test_bundle_supremo_soma_custo_fixo_sem_mudar_tokens():
    estimate = PowerCatalog().estimate_selection(
        ["bundle_supremo"],
        base_tokens=1200,
        base_value_brl=300,
    )

    assert estimate["multiplicador_total"] == 1
    assert estimate["tokens_estimados"] == 1200
    assert estimate["custo_fixo_brl"] == 1200
    assert estimate["valor_estimado_brl"] == 1500
    assert any("Pacote Supremo" in nota for nota in estimate["notas_operacionais"])


def test_multiplos_multiplicadores_sao_acumulados_em_ordem_estavel():
    estimate = PowerCatalog().estimate_selection(
        ["leitura_profunda", "modo_rapido", "oraculo_premium"],
        base_tokens=1000,
        base_value_brl=100,
    )

    assert [power["id"] for power in estimate["poderes_selecionados"]] == [
        "oraculo_premium",
        "modo_rapido",
        "leitura_profunda",
    ]
    assert estimate["multiplicador_total"] == 9
    assert estimate["tokens_estimados"] == 9000
    assert estimate["valor_estimado_brl"] == 900
