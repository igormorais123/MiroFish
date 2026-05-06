from __future__ import annotations

from app.services.mission_bundle import MissionBundle, gerar_mission_bundle, sha256_item


def _sample_payload():
    return {
        "report_id": "rep-4b",
        "simulation_id": "sim-4b",
        "custo": {"moeda": "BRL", "total": 128.5},
        "poderes": ["analise de sinais", "simulacao social"],
        "personas": [{"nome": "Coordenacao", "papel": "decisao"}],
        "previsoes": [
            {"id": "prev_1", "enunciado": "A fila cai.", "status": "congelada"},
            {"id": "prev_2", "enunciado": "O risco ja foi observado.", "status": "confirmada"},
        ],
        "arquivos": [
            {"nome": "relatorio.md", "conteudo": "Sintese final"},
            {"nome": "dados.json", "conteudo": {"linhas": 3}},
        ],
        "criado_em": "2026-05-05T12:00:00+00:00",
    }


def test_mission_bundle_generates_portuguese_manifest_without_real_files():
    manifest = MissionBundle().gerar_manifesto(**_sample_payload())

    assert manifest["titulo"] == "Manifesto final da missao"
    assert manifest["custo_total"] == {"moeda": "BRL", "total": 128.5}
    assert manifest["poderes_mobilizados"] == ["analise de sinais", "simulacao social"]
    assert manifest["participantes"] == [{"nome": "Coordenacao", "papel": "decisao"}]
    assert manifest["previsoes_congeladas"] == [
        {"id": "prev_1", "enunciado": "A fila cai.", "status": "congelada"}
    ]
    assert manifest["arquivos"][0]["nome"] == "relatorio.md"
    assert "LGPD" not in str(manifest)
    assert "disclaimer" not in str(manifest).lower()


def test_mission_bundle_hashes_items_and_manifest_deterministically():
    payload = _sample_payload()
    first = gerar_mission_bundle(**payload)
    second = gerar_mission_bundle(**payload)

    assert first["hashes"] == second["hashes"]
    assert first["hashes"]["itens"]["report_id"] == sha256_item("rep-4b")
    assert first["hashes"]["itens"]["arquivos"] == sha256_item(payload["arquivos"])
    assert len(first["hashes"]["manifesto"]) == 64


def test_mission_bundle_hash_nao_depende_do_horario_de_criacao():
    payload = _sample_payload()
    first = gerar_mission_bundle(**{**payload, "criado_em": "2026-05-05T12:00:00+00:00"})
    second = gerar_mission_bundle(**{**payload, "criado_em": "2026-05-05T12:30:00+00:00"})

    assert first["criado_em"] != second["criado_em"]
    assert first["hashes"] == second["hashes"]


def test_mission_bundle_manifest_hash_changes_when_content_changes():
    payload = _sample_payload()
    first = gerar_mission_bundle(**payload)
    payload["custo"] = {"moeda": "BRL", "total": 130.0}
    second = gerar_mission_bundle(**payload)

    assert first["hashes"]["itens"]["custo_total"] != second["hashes"]["itens"]["custo_total"]
    assert first["hashes"]["manifesto"] != second["hashes"]["manifesto"]
