"""
Postura da análise — o erro de mandato do caso Vale Trading.

A consulta encerrava com ordem expressa: "a IA deve atuar como perito
assistente da parte e não como perito do juízo". O sistema entregou perito do
juízo, com veredito de não-promoção — correto sobre o quantum e adverso a quem
pagou pelo trabalho.
"""

import pytest

from app.services import analysis_posture as ap


def test_padrao_e_assistente_da_parte():
    """Perito do juízo é quem o juízo nomeia, não quem o escritório contrata."""
    assert ap.POSTURA_PADRAO.id == "assistente_da_parte"
    assert ap.get_postura(None).id == "assistente_da_parte"
    assert ap.get_postura("").id == "assistente_da_parte"


@pytest.mark.parametrize("identificador", ["red_team", "RED_TEAM", " Red_Team "])
def test_identificador_e_tolerante_a_caixa_e_espaco(identificador):
    assert ap.get_postura(identificador).id == "red_team"


def test_postura_desconhecida_cai_no_padrao_em_vez_de_quebrar():
    assert ap.get_postura("perito_do_marte").id == "assistente_da_parte"


def test_as_tres_posturas_estao_disponiveis():
    ids = [p.id for p in ap.todas()]
    assert ids == ["assistente_da_parte", "perito_do_juizo", "red_team"]


def test_assistente_nao_simula_imparcialidade():
    """Era a confusão exata: entregar isenção quando se pediu assistência."""
    mandato = ap.ASSISTENTE_DA_PARTE.mandato.lower()
    assert "nao e imparcial" in mandato


def test_assistente_trata_fragilidade_como_risco_e_nao_como_desistencia():
    entrega = ap.ASSISTENTE_DA_PARTE.entrega.lower()
    assert "risco a administrar" in entrega
    assert "desistir" in entrega  # explicitamente afastado


def test_perito_do_juizo_permanece_imparcial():
    assert "imparcial" in ap.PERITO_DO_JUIZO.mandato.lower()
    assert "nenhuma das partes" in ap.PERITO_DO_JUIZO.mandato.lower()


def test_red_team_ataca_a_tese_do_proprio_cliente():
    assert "ataca a tese do cliente" in ap.RED_TEAM.mandato.lower()


def test_bloco_de_prompt_traz_mandato_e_entrega():
    bloco = ap.ASSISTENTE_DA_PARTE.prompt_block()

    assert "POSTURA:" in bloco
    assert "Mandato:" in bloco
    assert "O que entregar:" in bloco


def test_posturas_sao_imutaveis():
    """Nenhuma etapa do pipeline pode reescrever o mandato em runtime."""
    with pytest.raises(Exception):
        ap.ASSISTENTE_DA_PARTE.mandato = "outro mandato"
