"""
Material processual usa ontologia de processo, não de rede social.

A ontologia padrão descreve quem apoia quem e quem repercute o quê. Num
processo isso não existe: há um decisor único, um conjunto fechado de
documentos, e teses que caem conforme a prova está ou não nos autos.
"""

from unittest.mock import patch

import pytest

from app.services import judicial_ontology as jo
from app.services.ontology_generator import OntologyGenerator


CONSULTA_VALE = (
    "Liquidacao de sentenca do credito-premio de IPI. O acordao do TRF4 nao "
    "enfrentou a prescricao, e foram opostos embargos de declaracao no evento "
    "239 dos autos."
)


# --- detecção ---

def test_material_do_caso_vale_e_processual():
    assert jo.is_material_processual(CONSULTA_VALE) is True


@pytest.mark.parametrize("texto", [
    "peticao inicial e contestacao nos autos",
    "sentenca proferida apos pericia com laudo pericial",
    "agravo contra decisao da 3a Vara Federal",
])
def test_vocabulario_forense_e_reconhecido(texto):
    assert jo.is_material_processual(texto) is True


@pytest.mark.parametrize("texto", [
    "Avaliar aceitacao da proposta entre eleitores da capital",
    "Pesquisa de clima organizacional com servidores",
    "",
])
def test_material_nao_forense_nao_e_confundido(texto):
    assert jo.is_material_processual(texto) is False


def test_um_sinal_isolado_nao_basta():
    """'Autos' e 'petição' aparecem em texto comum; exigir dois evita falso positivo."""
    assert jo.is_material_processual("consultei os autos do inquerito interno") is False


# --- a ontologia em si ---

def test_entidades_sao_do_processo_e_nao_da_rede_social():
    nomes = {e["name"] for e in jo.build_judicial_ontology()["entity_types"]}

    assert {"Evento", "Documento", "Tese", "Norma", "Valor", "Diligencia"} <= nomes


def test_arestas_dizem_o_que_sustenta_e_o_que_derruba():
    nomes = {a["name"] for a in jo.build_judicial_ontology()["edge_types"]}

    assert {"SUSTENTA", "CONTRADIZ", "DEPENDE_DE", "FOI_OMITIDO_EM"} <= nomes


def test_tese_pode_ficar_orfa_de_documento():
    """É a pergunta que a ontologia social não sabe responder."""
    depende = next(
        a for a in jo.build_judicial_ontology()["edge_types"] if a["name"] == "DEPENDE_DE"
    )
    pares = {(p["source"], p["target"]) for p in depende["source_targets"]}

    assert ("Tese", "Documento") in pares
    assert ("Tese", "Diligencia") in pares


def test_documento_carrega_pagina_para_o_pincite():
    documento = next(
        e for e in jo.build_judicial_ontology()["entity_types"] if e["name"] == "Documento"
    )
    atributos = {a["name"] for a in documento["attributes"]}

    assert {"doc_id", "pagina"} <= atributos


def test_diligencia_tem_prazo_custo_e_impacto():
    """Substitui a probabilidade fabricada por valor da informação."""
    diligencia = next(
        e for e in jo.build_judicial_ontology()["entity_types"] if e["name"] == "Diligencia"
    )
    atributos = {a["name"] for a in diligencia["attributes"]}

    assert {"prazo", "custo_estimado", "impacto_decisorio"} <= atributos


# --- integração com o gerador ---

def test_gerador_usa_a_ontologia_judicial_sem_chamar_o_modelo():
    gerador = OntologyGenerator.__new__(OntologyGenerator)

    with patch.object(OntologyGenerator, "_build_user_message") as construiu:
        resultado = gerador.generate([CONSULTA_VALE], "avaliar a liquidacao")

    assert resultado["domain"] == "materia_judicial"
    # Nem monta o prompt social: o preset é fixo e não depende de LLM.
    construiu.assert_not_called()
