"""
Simulação de agentes só vale onde há difusão.

No caso Vale Trading, 36 tweets sintéticos viraram base para percentuais de
convicção sobre uma liquidação de sentença. Um ABM só informa quando há muitos
atores se influenciando; num processo há um decisor único e documentos fechados.
"""

import pytest

from app.services.abm_validation_gate import evaluate_abm_applicability


def test_materia_judicial_nao_roda_abm_por_padrao():
    veredicto = evaluate_abm_applicability("materia_judicial")

    assert veredicto.aplicavel is False
    assert "decisor unico" in veredicto.motivo
    assert veredicto.exige_validacao_declarada is True


def test_motivo_aponta_o_caminho_que_funciona():
    """Bloquear sem dizer o que fazer no lugar não ajuda ninguém."""
    motivo = evaluate_abm_applicability("materia_judicial").motivo
    assert "recuperacao documental" in motivo
    assert "contraditorio" in motivo


def test_validacao_declarada_libera_e_registra_a_responsabilidade():
    veredicto = evaluate_abm_applicability("materia_judicial", validacao_declarada=True)

    assert veredicto.aplicavel is True
    assert "responde por quem a declarou" in veredicto.motivo


@pytest.mark.parametrize("dominio", [
    "eleitoral_territorial",
    "reputacional",
    "general_public",
    "servidores_federais",
])
def test_dominios_com_difusao_continuam_rodando(dominio):
    """O ABM não é descartado: segue no produto onde nasceu."""
    assert evaluate_abm_applicability(dominio).aplicavel is True


def test_dominio_desconhecido_nao_roda_por_omissao():
    veredicto = evaluate_abm_applicability("dominio_que_ninguem_mapeou")

    assert veredicto.aplicavel is False
    assert "sem difusao verificada" in veredicto.motivo


def test_dominio_ausente_nao_quebra():
    assert evaluate_abm_applicability(None).aplicavel is False
    assert evaluate_abm_applicability("").aplicavel is False


def test_identificador_tolera_caixa_e_espaco():
    assert evaluate_abm_applicability("  Materia_Judicial ").aplicavel is False


def test_veredicto_serializa_para_o_gate():
    d = evaluate_abm_applicability("materia_judicial").to_dict()

    assert d["abm_applicable"] is False
    assert d["requires_declared_validation"] is True


def test_veredicto_e_imutavel():
    """Nenhuma etapa pode reescrever a aplicabilidade em runtime."""
    veredicto = evaluate_abm_applicability("materia_judicial")
    with pytest.raises(Exception):
        veredicto.aplicavel = True
