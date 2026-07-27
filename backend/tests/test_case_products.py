"""
Os quatro produtos do escritório, derivados do grafo do caso.

A saída era um relatório sobre o próprio sistema. O que a consulta pediu era
cronologia auditada, matriz de omissões por fundamento autônomo, cobertura
documental e mapa de contradições.
"""

import pytest

from app.services.case_products import (
    build_case_products,
    build_contradiction_map,
    build_coverage_matrix,
    build_omissions,
    build_timeline,
)


class No:
    """Dublê de EntityNode, com o mínimo que os produtos consultam."""

    def __init__(self, name, tipo, summary="", attributes=None, edges=None):
        self.name = name
        self.labels = ["Entity", tipo]
        self.summary = summary
        self.attributes = attributes or {}
        self.related_edges = edges or []


def aresta(nome, alvo):
    return {"direction": "related", "edge_name": nome, "target": alvo, "fact": alvo}


# --- cronologia ---

def test_atos_saem_ordenados_por_data():
    entidades = [
        No("Ato C", "Evento", attributes={"data": "12/03/2020", "numero_evento": "239"}),
        No("Ato A", "Evento", attributes={"data": "2018-01-05", "numero_evento": "1"}),
        No("Ato B", "Evento", attributes={"data": "07-06-2019", "numero_evento": "112"}),
    ]

    datas = [a.data for a in build_timeline(entidades)]
    assert datas == ["2018-01-05", "2019-06-07", "2020-03-12"]


def test_ato_sem_data_vai_para_o_fim_sem_ser_descartado():
    """A ausência da data é informação: o ato existe e não foi possível situá-lo."""
    entidades = [
        No("Sem data", "Evento", attributes={"numero_evento": "500"}),
        No("Com data", "Evento", attributes={"data": "2021-02-02"}),
    ]

    atos = build_timeline(entidades)
    assert len(atos) == 2
    assert atos[-1].evento == "500"
    assert atos[-1].data is None


def test_cronologia_carrega_a_ponte_para_os_autos():
    entidades = [No("Ato", "Evento", attributes={"data": "2020-01-01", "citation": "parte3.pdf, p. 12"})]
    assert build_timeline(entidades)[0].citacao == "parte3.pdf, p. 12"


def test_entidade_que_nao_e_evento_fica_fora_da_cronologia():
    assert build_timeline([No("Uma tese", "Tese")]) == []


# --- omissões ---

def test_omissao_registra_onde_o_ponto_nao_foi_enfrentado():
    """Eixo dos embargos do evento 239."""
    entidades = [
        No("Prescricao quinquenal", "Tese",
           attributes={"citation": "embargos.pdf, p. 4"},
           edges=[aresta("FOI_OMITIDO_EM", "Evento 228 - acordao")]),
    ]

    omissoes = build_omissions(entidades)
    assert len(omissoes) == 1
    assert omissoes[0].nao_enfrentado_em == ["Evento 228 - acordao"]
    # Embargo por omissão sem indicar onde o ponto foi suscitado não se sustenta.
    assert omissoes[0].citacao == "embargos.pdf, p. 4"


def test_ponto_enfrentado_nao_entra_na_matriz():
    entidades = [No("Tese tratada", "Tese", edges=[aresta("SUSTENTA", "Doc X")])]
    assert build_omissions(entidades) == []


def test_norma_omitida_tambem_e_capturada():
    """A omissão pode ser de dispositivo, não só de tese."""
    entidades = [No("EREsp 800.578", "Norma", edges=[aresta("FOI_OMITIDO_EM", "Evento 228")])]

    omissoes = build_omissions(entidades)
    assert omissoes[0].tipo_do_ponto == "Norma"


# --- cobertura ---

def test_tese_sem_nada_que_a_sustente_e_orfa():
    """Substitui 'convicção 72%' por algo verificável e acionável."""
    entidades = [No("Tese solta", "Tese")]

    cobertura = build_coverage_matrix(entidades)[0]
    assert cobertura.orfa is True
    assert cobertura.sustentada_por == []


def test_documento_que_sustenta_aparece_na_tese():
    entidades = [
        No("CIEX 12%", "Tese"),
        No("Laudo pericial", "Documento", edges=[aresta("SUSTENTA", "CIEX 12%")]),
        No("Guia de exportacao", "Documento", edges=[aresta("SUSTENTA", "CIEX 12%")]),
    ]

    cobertura = build_coverage_matrix(entidades)[0]
    assert sorted(cobertura.sustentada_por) == ["Guia de exportacao", "Laudo pericial"]
    assert cobertura.orfa is False


def test_tese_mais_contradita_do_que_sustentada_fica_exposta():
    entidades = [
        No("Tese fragil", "Tese"),
        No("Doc A", "Documento", edges=[aresta("SUSTENTA", "Tese fragil")]),
        No("Doc B", "Documento", edges=[aresta("CONTRADIZ", "Tese fragil")]),
        No("Doc C", "Documento", edges=[aresta("CONTRADIZ", "Tese fragil")]),
    ]

    cobertura = build_coverage_matrix(entidades)[0]
    assert cobertura.exposta is True


def test_dependencia_da_tese_e_registrada():
    """Responde 'o que fica órfão se o documento X não vier'."""
    entidades = [
        No("Tese", "Tese", edges=[aresta("DEPENDE_DE", "Guia de exportacao 1996")]),
    ]

    assert build_coverage_matrix(entidades)[0].depende_de == ["Guia de exportacao 1996"]


def test_aresta_para_tese_inexistente_e_ignorada():
    """Grafo incompleto não pode quebrar o produto."""
    entidades = [No("Doc", "Documento", edges=[aresta("SUSTENTA", "Tese que nao existe")])]
    assert build_coverage_matrix(entidades) == []


# --- contradições ---

def test_mapa_registra_de_onde_para_onde():
    entidades = [
        No("Peticao inicial", "Documento", edges=[aresta("CONTRADIZ", "Memorial")]),
    ]

    mapa = build_contradiction_map(entidades)
    assert (mapa[0].de, mapa[0].para) == ("Peticao inicial", "Memorial")
    assert "Documento" in mapa[0].natureza


def test_sem_contradicao_o_mapa_e_vazio():
    assert build_contradiction_map([No("Doc", "Documento")]) == []


# --- pacote ---

def test_pacote_conta_o_que_esta_ancorado_nos_autos():
    """Pacote construído sobre entidades sem ponte não é utilizável numa peça."""
    entidades = [
        No("Ato", "Evento", attributes={"data": "2020-01-01", "citation": "a.pdf, p. 1"}),
        No("Tese orfa", "Tese"),
    ]

    pacote = build_case_products(entidades)

    assert pacote["summary"] == {
        "total_entities": 2,
        "anchored_entities": 1,
        "orphan_theses": 1,
        "exposed_theses": 0,
        "dated_acts": 1,
        # A entidade se chama "Ato" e nao tem resumo: a descricao nao diz o que
        # aconteceu, so que aconteceu.
        "substantive_acts": 0,
    }


def test_grafo_vazio_produz_pacote_vazio_e_nao_inventado():
    pacote = build_case_products([])

    assert pacote["timeline"] == []
    assert pacote["coverage"] == []
    assert pacote["summary"]["total_entities"] == 0


def test_pacote_traz_os_quatro_produtos():
    pacote = build_case_products([No("Ato", "Evento")])
    assert {"timeline", "omissions", "coverage", "contradictions"} <= set(pacote)


# --- valor da informação ---

def test_lacuna_vira_item_com_prazo_custo_e_impacto():
    """Substitui a probabilidade fabricada por algo decidível."""
    from app.services.case_products import build_information_value

    entidades = [
        No("CIEX 12%", "Tese", edges=[aresta("DEPENDE_DE", "Guia de exportacao 1996")]),
        No("Guia de exportacao 1996", "Diligencia", attributes={
            "prazo": "30 dias",
            "custo_estimado": "R$ 4.000",
            "impacto_decisorio": "converte a tese de plausivel em comprovada",
        }),
    ]

    itens = build_information_value(entidades)
    assert len(itens) == 1
    assert itens[0].tese == "CIEX 12%"
    assert itens[0].prazo == "30 dias"
    assert itens[0].impacto_decisorio.startswith("converte")


def test_dependencia_ja_satisfeita_nao_vira_lacuna():
    """O documento já sustenta a tese: não há o que diligenciar."""
    from app.services.case_products import build_information_value

    entidades = [
        No("Tese", "Tese", edges=[aresta("DEPENDE_DE", "Laudo")]),
        No("Laudo", "Documento", edges=[aresta("SUSTENTA", "Tese")]),
    ]

    assert build_information_value(entidades) == []


def test_lacuna_sem_diligencia_cadastrada_ainda_e_reportada():
    """Não saber o custo não é motivo para esconder a lacuna."""
    from app.services.case_products import build_information_value

    entidades = [No("Tese", "Tese", edges=[aresta("DEPENDE_DE", "Documento que ninguem mapeou")])]

    item = build_information_value(entidades)[0]
    assert item.falta == "Documento que ninguem mapeou"
    assert item.custo_estimado is None


def test_pacote_inclui_valor_da_informacao():
    entidades = [No("Tese", "Tese", edges=[aresta("DEPENDE_DE", "Doc faltante")])]
    assert len(build_case_products(entidades)["information_value"]) == 1


# --- data como a peca escreve ---

def test_data_por_extenso_entra_na_cronologia():
    """
    Das 752 datas extraidas do acervo da Vale, so 83 vinham em dd/mm/aaaa.
    Ler so esse formato descartava atos com data perfeitamente legivel.
    """
    from app.services.case_products import _data_ordenavel

    assert _data_ordenavel("28 de marco de 2003") == "2003-03-28"
    assert _data_ordenavel("31 de Dezembro de 1995") == "1995-12-31"
    assert _data_ordenavel("29 (vinte e nove) de abril de 1994") == "1994-04-29"


def test_dia_e_mes_sem_zero_a_esquerda():
    from app.services.case_products import _data_ordenavel
    assert _data_ordenavel("9/5/1996") == "1996-05-09"


def test_ano_isolado_situa_o_ato_sem_inventar_o_dia():
    from app.services.case_products import _data_ordenavel

    assert _data_ordenavel("2018") == "2018"
    # Ordena junto com as datas completas, que e o ponto.
    assert "2018" < "2018-03-01"


def test_mes_por_extenso_desconhecido_nao_vira_data_torta():
    from app.services.case_products import _data_ordenavel
    assert _data_ordenavel("12 de brumario de 1799") is None


def test_texto_sem_data_continua_sem_data():
    from app.services.case_products import _data_ordenavel
    assert _data_ordenavel("nao informada") is None
    assert _data_ordenavel("") is None
    assert _data_ordenavel(None) is None


def test_cronologia_ordena_extenso_e_numerico_juntos():
    from app.services.case_products import build_timeline

    class E:
        def __init__(self, data):
            self.labels = ["Entity", "Evento"]
            self.attributes = {"data": data, "numero_evento": data}
            self.summary = data
            self.related_edges = []

    linha = build_timeline([E("17/07/2003"), E("28 de marco de 2003"), E("2018")])

    assert [a.data for a in linha] == ["2003-03-28", "2003-07-17", "2018"]


def test_ano_de_dois_digitos_e_lido_com_o_corte_do_seculo():
    """544 das 551 datas que sobravam no acervo vinham assim."""
    from app.services.case_products import _data_ordenavel

    assert _data_ordenavel("28/3/05") == "2005-03-28"
    assert _data_ordenavel("25.03.92") == "1992-03-25"
    assert _data_ordenavel("30/5/05") == "2005-05-30"


def test_ano_de_quatro_digitos_nao_e_afetado_pelo_corte():
    from app.services.case_products import _data_ordenavel
    assert _data_ordenavel("17/07/2003") == "2003-07-17"
    assert _data_ordenavel("09/05/1996") == "1996-05-09"


# --- cronologia x indice de andamentos ---

def _ato(descricao):
    from app.services.case_products import AtoProcessual
    return AtoProcessual(evento="1", data="1984-03-06", sujeito=None,
                         natureza=None, descricao=descricao, citacao=None)


def test_descricao_que_so_repete_a_chave_nao_e_substantiva():
    """Uma tabela de andamentos do Evento 96 virou 456 pseudo-atos assim."""
    for d in (
        "Ato processual identificado pelo número 25 e pela data 13/10/83.",
        "Registro processual numerado 34.",
        "Registro numerado associado aos valores de 1987.",
        "Ato processual datado de 09/04/84.",
    ):
        assert _ato(d).substantivo is False, d


def test_ato_que_diz_o_que_aconteceu_e_substantivo():
    for d in (
        "Juntada de embargos de declaração no processo.",
        "Despacho ou decisão que rejeitou os embargos de declaração.",
        "Data do trânsito em julgado do acórdão da Primeira Turma.",
        "Petição de Luiz Alberto Maffini requerendo juntada de título.",
        "Ato processual de oposição dos embargos de declaração.",
    ):
        assert _ato(d).substantivo is True, d


def test_ato_generico_continua_na_cronologia():
    """O ato existe e a data e boa; separar nao e descartar."""
    from app.services.case_products import build_case_products

    class E:
        labels = ["Entity", "Evento"]
        attributes = {"data": "06/03/1984", "numero_evento": "34"}
        summary = "Registro processual numerado 34."
        related_edges = []

    p = build_case_products([E()])

    assert len(p["timeline"]) == 1
    assert p["summary"]["dated_acts"] == 1
    assert p["summary"]["substantive_acts"] == 0
    assert p["timeline"][0]["substantivo"] is False


def test_descricao_vazia_nao_e_marcada_como_indice():
    """Sem descricao nao ha o que julgar; nao e o mesmo que tautologia."""
    assert _ato("").substantivo is True
