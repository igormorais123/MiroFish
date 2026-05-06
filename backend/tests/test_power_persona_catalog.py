"""Testes do catalogo de poderes e personas externas."""
from __future__ import annotations

import json

from app.services.power_persona_catalog import PowerPersonaCatalog


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_catalogo_usa_fontes_configuradas_por_ambiente(tmp_path, monkeypatch):
    write_text(tmp_path / "vox_env.md", "# Vox Ambiente\npersona sintetica configurada")
    monkeypatch.setenv(PowerPersonaCatalog.ENV_ROOTS_KEY, str(tmp_path))

    catalog = PowerPersonaCatalog().build_catalog()

    assert [item["nome"] for item in catalog] == ["Vox Ambiente"]
    assert PowerPersonaCatalog().roots == (tmp_path,)


def test_catalogo_indexa_md_json_e_csv(tmp_path):
    write_text(
        tmp_path / "consultores" / "helena.md",
        "# Helena Oracle\nConsultora lendaria para leitura de cenarios.",
    )
    write_text(
        tmp_path / "vox" / "personas.json",
        json.dumps(
            [
                {
                    "name": "Vox Eleitor Jovem",
                    "description": "Persona sintetica de eleitor urbano.",
                }
            ]
        ),
    )
    write_text(
        tmp_path / "poderes.csv",
        "nome,description\nPoder Preditivo,previsao com teoria dos jogos\n",
    )

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert [item["nome"] for item in catalog] == [
        "Vox Eleitor Jovem",
        "Helena Oracle",
        "Poder Preditivo",
    ]
    assert [item["tipo"] for item in catalog] == [
        "persona_sintetica",
        "consultor_lendario",
        "poder_previsao",
    ]
    assert all(set(item) >= {"id", "nome", "tipo", "fonte", "origem", "resumo", "marcadores", "caminho"} for item in catalog)


def test_catalogo_deduplica_por_caminho_e_nome_normalizado(tmp_path):
    write_text(
        tmp_path / "vox_personas.json",
        json.dumps(
            [
                {"nome": "Vox Norte", "bio": "persona sintetica"},
                {"nome": "Vox Norte", "bio": "persona sintetica duplicada"},
                {"nome": "Vox Sul", "bio": "persona sintetica"},
            ]
        ),
    )

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert [item["nome"] for item in catalog] == ["Vox Norte", "Vox Sul"]


def test_catalogo_deduplica_por_tipo_e_nome_entre_caminhos(tmp_path):
    write_text(tmp_path / "origem_a" / "persona" / "helena.md", "# Helena\nconsultor lendario")
    write_text(tmp_path / "origem_b" / "persona" / "helena.md", "# Helena\nconsultor lendario duplicado")

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert [item["nome"] for item in catalog] == ["Helena"]


def test_catalogo_respeita_limites_e_ignora_pastas_pesadas(tmp_path):
    write_text(tmp_path / "node_modules" / "helena.md", "# Helena\nconsultor lendario")
    write_text(tmp_path / ".git" / "oracle.md", "# Oracle\nconsultor lendario")
    write_text(tmp_path / "dist" / "cicero.md", "# Cicero\nconsultor lendario")
    write_text(tmp_path / ".venv" / "midas.md", "# Midas\nconsultor lendario")
    write_text(tmp_path / "backups" / "iris.md", "# Iris\nconsultor lendario")
    write_text(tmp_path / "grande_poder.md", "# Poder Preditivo\n" + ("previsao " * 100))
    write_text(tmp_path / "vox_1.md", "# Vox Um\npersona sintetica")
    write_text(tmp_path / "vox_2.md", "# Vox Dois\npersona sintetica")

    catalog = PowerPersonaCatalog(roots=[tmp_path], max_files=1, max_file_size=80).build_catalog()

    assert len(catalog) == 1
    assert catalog[0]["nome"] in {"Vox Um", "Vox Dois"}
    assert "node_modules" not in catalog[0]["caminho"]
    assert ".git" not in catalog[0]["caminho"]
    assert "dist" not in catalog[0]["caminho"]
    assert ".venv" not in catalog[0]["caminho"]
    assert "backups" not in catalog[0]["caminho"]


def test_catalogo_nao_classifica_arquivo_neutro_pelo_nome_da_raiz(tmp_path):
    root = tmp_path / "voxsintetica-platform"
    write_text(root / "docs" / "readme.md", "# README\nTexto tecnico de configuracao interna.")

    catalog = PowerPersonaCatalog(roots=[root]).build_catalog()

    assert catalog == []


def test_catalogo_ignora_metadados_de_projeto_em_raiz_vox(tmp_path):
    root = tmp_path / "voxsintetica-platform"
    write_text(root / ".prettierrc.json", '{ "semi": true, "singleQuote": true }')
    write_text(
        root / ".turbo" / "cache" / "abc-meta.json",
        json.dumps({"hash": "abc", "duration": 10, "sha": "deadbeef"}),
    )
    write_text(root / "package.json", json.dumps({"name": "@voxsintetica/app", "version": "0.0.0"}))
    write_text(root / "docs" / "vox_real.md", "# Vox Real\nPersona sintetica de teste.")

    catalog = PowerPersonaCatalog(roots=[root]).build_catalog()

    assert [item["nome"] for item in catalog] == ["Vox Real"]


def test_catalogo_default_restringe_raiz_ampla_a_pastas_de_catalogo(tmp_path, monkeypatch):
    root = tmp_path / "voxsintetica-platform"
    write_text(root / "docs" / "helena.md", "# Helena Doc\nConsultor lendario em documento tecnico.")
    write_text(root / "skills" / "helena" / "persona" / "SKILL.md", "# Helena Persona\nConsultor lendario.")
    monkeypatch.setattr(PowerPersonaCatalog, "DEFAULT_ROOTS", (root,))

    catalog = PowerPersonaCatalog().build_catalog()

    assert [item["nome"] for item in catalog] == ["Helena Persona"]


def test_select_items_filtra_ids_e_tipo(tmp_path):
    write_text(tmp_path / "helena.md", "# Helena\nconsultor lendario")
    write_text(tmp_path / "poder.md", "# Poder Preditivo\nprevisao")
    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    selected = PowerPersonaCatalog().select_items(
        catalog,
        [item["id"] for item in catalog],
        tipo="poder_previsao",
    )

    assert len(selected) == 1
    assert selected[0]["tipo"] == "poder_previsao"


def test_context_pack_e_curto_e_limitado(tmp_path):
    write_text(tmp_path / "conselho.md", "# Conselho Iris\nconsultor lendario " + ("analise " * 80))
    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    pack = PowerPersonaCatalog().build_context_pack(catalog, max_chars=120)

    assert pack.startswith("Contexto selecionado de poderes e personas:")
    assert "Conselho Iris" in pack
    assert len(pack) <= 120
    assert pack.endswith("...")


def test_arquivo_malformado_nao_derruba_catalogo(tmp_path):
    write_text(tmp_path / "vox_ruim.json", '{"name": "Vox Quebrado", "bio": ')
    write_text(tmp_path / "helena.md", "# Helena\nconsultor lendario")

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert any(item["nome"] == "Helena" for item in catalog)


def test_json_neutro_com_bio_persona_sintetica_entra(tmp_path):
    write_text(
        tmp_path / "registro.json",
        json.dumps({"name": "Moradora Centro", "bio": "persona sintetica de servicos publicos"}),
    )

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert len(catalog) == 1
    assert catalog[0]["nome"] == "Moradora Centro"
    assert catalog[0]["tipo"] == "persona_sintetica"


def test_json_neutro_infere_persona_sintetica_por_prompt(tmp_path):
    write_text(
        tmp_path / "registro.json",
        json.dumps({"name": "Moradora Centro", "bio": "texto neutro", "prompt": "persona sintetica"}),
    )

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert len(catalog) == 1
    assert catalog[0]["nome"] == "Moradora Centro"
    assert catalog[0]["tipo"] == "persona_sintetica"


def test_json_neutro_infere_por_system_apos_bio_neutro(tmp_path):
    write_text(
        tmp_path / "registro.json",
        json.dumps(
            [
                {
                    "name": "Conselheiro",
                    "bio": "texto neutro",
                    "system": "atuar como consultor lendario",
                },
                {
                    "name": "Radar",
                    "bio": "texto neutro",
                    "system": "avaliar poder de previsao",
                },
            ]
        ),
    )

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert [item["nome"] for item in catalog] == ["Conselheiro", "Radar"]
    assert [item["tipo"] for item in catalog] == ["consultor_lendario", "poder_previsao"]


def test_context_pack_limites_muito_pequenos():
    catalog = [
        {
            "nome": "Helena",
            "tipo": "consultor_lendario",
            "resumo": "consultor lendario",
            "marcadores": [],
        }
    ]

    builder = PowerPersonaCatalog()

    assert builder.build_context_pack(catalog, max_chars=0) == ""
    assert len(builder.build_context_pack(catalog, max_chars=1)) <= 1
    assert len(builder.build_context_pack(catalog, max_chars=2)) <= 2


def test_context_pack_pequeno_nao_consumir_toda_selecao():
    def selected_items():
        yield {
            "nome": "Helena",
            "tipo": "consultor_lendario",
            "resumo": "consultor lendario " * 100,
            "marcadores": ["helena"],
        }
        raise AssertionError("build_context_pack consumiu itens alem do limite")

    pack = PowerPersonaCatalog().build_context_pack(selected_items(), max_chars=80)

    assert len(pack) <= 80
    assert pack.endswith("...")


def test_json_dict_com_lista_comum(tmp_path):
    write_text(
        tmp_path / "consultores.json",
        json.dumps(
            {
                "consultores": [
                    {"title": "Cicero", "role": "consultor lendario", "description": "retorica"},
                    {"title": "Midas", "role": "consultor lendario", "description": "decisao"},
                ]
            }
        ),
    )

    catalog = PowerPersonaCatalog(roots=[tmp_path]).build_catalog()

    assert [item["nome"] for item in catalog] == ["Cicero", "Midas"]


def test_api_helpers_filtram_catalogo_e_montam_contexto(monkeypatch):
    from app.api import report as report_api

    catalog = [
        {
            "id": "poder_previsao:radar:1",
            "nome": "Radar Preditivo",
            "tipo": "poder_previsao",
            "fonte": "testes",
            "origem": "radar.md",
            "resumo": "poder de previsao para cenarios eleitorais",
            "marcadores": ["previsao"],
            "caminho": "C:/fake/radar.md",
        },
        {
            "id": "persona_sintetica:moradora:1",
            "nome": "Moradora Centro",
            "tipo": "persona_sintetica",
            "fonte": "testes",
            "origem": "vox.json",
            "resumo": "persona sintetica de servicos publicos",
            "marcadores": ["persona sintetica"],
            "caminho": "C:/fake/vox.json",
        },
    ]
    monkeypatch.setattr(report_api, "_build_power_persona_catalog", lambda: catalog)
    monkeypatch.setattr(PowerPersonaCatalog, "build_catalog", lambda self: catalog)

    filtered = report_api._filter_power_persona_catalog(catalog, tipo="poder_previsao", q="radar")
    context, metadata = report_api._build_power_persona_context_from_payload(
        {"selected_ids": ["poder_previsao:radar:1"], "tipo": "poder_previsao"}
    )

    assert [item["nome"] for item in filtered] == ["Radar Preditivo"]
    assert context.startswith("Contexto selecionado de poderes e personas:")
    assert "Radar Preditivo" in context
    assert metadata["selected_ids"] == ["poder_previsao:radar:1"]
    assert metadata["items"][0]["resumo_preview"] == "poder de previsao para cenarios eleitorais"
