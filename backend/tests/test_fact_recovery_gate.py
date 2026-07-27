"""
Fato repetido do prompt não é fato recuperado.

No caso Vale Trading o quick_search devolveu ~11 mil caracteres ecoando o
próprio pedido, carimbados com "Origem: parâmetros documentados no pedido", e
isso foi contabilizado como conhecimento recuperado. O relatório afirmou com a
segurança de quem leu os autos, tendo lido apenas a si mesmo.
"""

import pytest

from app.services.fact_recovery_gate import (
    filter_recovered_facts,
    is_eco,
)
from app.services.zep_tools import SearchResult


PROMPT = (
    "Analise a liquidacao de sentenca do credito-premio de IPI da Vale Trading, "
    "com CIEX de 12% ou 24%, correcao pela SELIC desde janeiro de 1996 e "
    "conversao cambial unica, no processo da 13a Vara Federal de Porto Alegre."
)


# --- eco direto ---

def test_trecho_literal_do_prompt_e_eco():
    assert is_eco("correcao pela SELIC desde janeiro de 1996", PROMPT) is True


def test_reformulacao_proxima_tambem_e_eco():
    """Trocar a ordem das palavras não transforma o pedido em descoberta."""
    assert is_eco("A SELIC corrige desde janeiro de 1996 o credito-premio", PROMPT) is True


def test_eco_ignora_acento_e_caixa():
    assert is_eco("CONVERSÃO CAMBIAL ÚNICA", PROMPT) is True


def test_fato_vazio_nao_conta_como_recuperado():
    assert is_eco("", PROMPT) is True
    assert is_eco("   ", PROMPT) is True


# --- recuperação real ---

def test_fato_externo_ao_prompt_e_recuperado():
    """O achado da LDO não estava no pedido: é o que o ciclo produziu de novo."""
    fato = (
        "A Uniao listou o processo por R$ 1,0 bilhao no Anexo V de Riscos Fiscais "
        "do PLDO 2024, pagina 56, entre riscos provaveis."
    )
    assert is_eco(fato, PROMPT) is False


def test_fato_com_alguns_termos_em_comum_ainda_e_recuperado():
    """Compartilhar vocabulário do caso é esperado; não é eco por isso."""
    fato = (
        "O acordao do TRF4 omitiu o AI 5039469 e o EREsp 800.578 ao tratar da "
        "prescricao, o que autoriza embargos por omissao"
    )
    assert is_eco(fato, PROMPT) is False


def test_fato_curto_nao_e_derrubado_por_sobreposicao():
    """Poucos termos não dão base estatística; só o teste literal vale."""
    assert is_eco("CIEX 12%", "documento sobre CIEX e aliquotas") is False


# --- separação em lote ---

def test_separa_recuperados_de_ecos():
    resultado = filter_recovered_facts(
        [
            "conversao cambial unica",                       # eco
            "Anexo V de Riscos Fiscais do PLDO 2024, p. 56",  # recuperado
            "CIEX de 12% ou 24%",                             # eco
        ],
        PROMPT,
    )

    assert resultado.total_recuperado == 1
    assert len(resultado.ecos) == 2
    assert resultado.seco is False


def test_run_so_com_eco_e_declarado_seco():
    """É a condição que precisa abortar o run em vez de gerar relatório."""
    resultado = filter_recovered_facts(
        ["correcao pela SELIC desde janeiro de 1996", "conversao cambial unica"],
        PROMPT,
    )

    assert resultado.seco is True
    assert resultado.to_dict() == {"facts_recovered": 0, "facts_echoed": 2, "dry": True}


def test_lista_vazia_e_seca():
    assert filter_recovered_facts([], PROMPT).seco is True
    assert filter_recovered_facts(None, PROMPT).seco is True


def test_fatos_em_branco_sao_descartados_sem_contar():
    resultado = filter_recovered_facts(["", "   ", "Anexo V do PLDO 2024, p. 56"], PROMPT)

    assert resultado.total_recuperado == 1
    assert resultado.ecos == []


# --- integração com o resultado de busca ---

def test_search_result_expoe_o_gate():
    r = SearchResult(
        facts=["conversao cambial unica", "Anexo V de Riscos Fiscais do PLDO 2024, p. 56"],
        edges=[], nodes=[], query="q", total_count=2,
    )

    resultado = r.recovered_facts(PROMPT)

    assert resultado.total_recuperado == 1
    assert resultado.seco is False


def test_busca_que_so_devolve_o_pedido_fica_seca():
    r = SearchResult(
        facts=["CIEX de 12% ou 24%", "conversao cambial unica"],
        edges=[], nodes=[], query="q", total_count=2,
    )

    assert r.recovered_facts(PROMPT).seco is True


# --- gate de ancoragem do grafo ---

class _No:
    def __init__(self, **atributos):
        self.attributes = atributos


def test_conta_apenas_nos_ancorados(monkeypatch):
    """Nós existirem não basta: sem trecho de origem não há como citar fonte."""
    from app.services import report_system_gate as gate

    class _Servico:
        def get_all_nodes(self, graph_id):
            return [
                _No(verbatim_found=True, source_excerpt="trecho"),
                _No(verbatim_found=False, source_excerpt=None),
                _No(verbatim_found=False, source_excerpt=None),
            ]

    monkeypatch.setattr("app.services.zep_tools.ZepToolsService", _Servico)
    assert gate._count_anchored_nodes("g1") == 1


def test_grafo_indisponivel_nao_vira_acusacao(monkeypatch):
    """Ausência de medida não pode ser lida como ausência de ancoragem."""
    from app.services import report_system_gate as gate

    class _Servico:
        def get_all_nodes(self, graph_id):
            raise RuntimeError("graphiti fora")

    monkeypatch.setattr("app.services.zep_tools.ZepToolsService", _Servico)
    assert gate._count_anchored_nodes("g1") is None


def test_grafo_sem_nenhum_no_ancorado(monkeypatch):
    from app.services import report_system_gate as gate

    class _Servico:
        def get_all_nodes(self, graph_id):
            return [_No(verbatim_found=False), _No()]

    monkeypatch.setattr("app.services.zep_tools.ZepToolsService", _Servico)
    assert gate._count_anchored_nodes("g1") == 0
