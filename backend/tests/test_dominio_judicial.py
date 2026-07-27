"""
Materia judicial nao recebe priors demograficos de populacao.

No caso Vale Trading, a deteccao de dominio classificou uma liquidacao
tributaria como pesquisa com servidores publicos federais — porque a palavra
"federal" aparecia em "13a Vara Federal". Os perfis dos agentes vieram
alimentados com sexo, idade, escolaridade, orgao e remuneracao de servidores.
"""

import pytest

from app.services.vox_science.artifacts import _baseline_sources, _detect_domain


CONSULTA_VALE = (
    "Consulta tecnico-pericial sobre liquidacao de sentenca em credito-premio de IPI, "
    "processo em tramite na 13a Vara Federal de Porto Alegre, com embargos de declaracao "
    "opostos ao acordao do TRF4."
)


def test_processo_judicial_nao_vira_pesquisa_com_servidores():
    assert _detect_domain(CONSULTA_VALE, "")["id"] == "materia_judicial"


@pytest.mark.parametrize("texto", [
    "acao na Justica Federal",
    "peticao nos autos do processo judicial",
    "execucao fiscal em tramite",
    "embargos ao acordao do TRF4",
])
def test_vocabulario_forense_cai_no_dominio_judicial(texto):
    assert _detect_domain(texto, "")["id"] == "materia_judicial"


def test_materia_judicial_nao_recebe_baseline_demografico():
    """Idade e renda nao explicam como a Uniao se manifesta numa liquidacao."""
    dominio = _detect_domain(CONSULTA_VALE, "")
    assert _baseline_sources(dominio) == []


def test_pesquisa_real_com_servidores_continua_detectada():
    """A correcao nao pode cegar o dominio para o qual o sistema foi feito."""
    dominio = _detect_domain(
        "Avaliar clima e engajamento entre servidores publicos federais apos o PGD", ""
    )

    assert dominio["id"] == "servidores_federais"
    fontes = _baseline_sources(dominio)
    assert any(f["name"] == "PEP/MGI" for f in fontes)


def test_dominio_eleitoral_continua_intacto():
    dominio = _detect_domain("intencao de voto para prefeito na eleicao municipal", "")

    assert dominio["id"] == "eleitoral_territorial"
    assert _baseline_sources(dominio)


def test_federal_sozinho_nao_classifica_servidor():
    """Era o gatilho exato do vazamento: 'federal' e palavra do foro."""
    assert _detect_domain("recurso federal sobre tributo", "")["id"] != "servidores_federais"
