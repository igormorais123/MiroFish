"""
A citacao precisa apontar para a folha onde o trecho realmente esta.

No ciclo original do caso Vale o unico achado aproveitavel veio com a citacao
apontando para o documento errado. Rodando os autos de novo o erro reapareceu
em 1 de 17 fatos — o trecho estava no OUT2, p. 5 e saiu citado como OUT3, p. 3.
Fato verdadeiro com referencia errada nao entra em peca.
"""

from app.services.citation_gate import (
    Veredito, filter_verified_facts, normalizar, verify_citation,
)
from app.utils.file_parser import PageSpan


CORPUS = (
    "a fixacao de limite temporal e coisa distinta da especificacao do que esta contido nesse periodo"  # 0-97
    "os relatorios sao emitidos pela Secretaria de Comercio Exterior e acompanhados de certificacao"   # 97-192
)

SPANS = [
    PageSpan(doc_id="p8.pdf", doc_index=8, page=1, start=0, end=97,
             evento="239", tipo_documento="ANEXO3", pagina_do_evento="3"),
    PageSpan(doc_id="p9.pdf", doc_index=9, page=2, start=97, end=192,
             evento="252", tipo_documento="OUT2", pagina_do_evento="5"),
]


def test_trecho_esta_na_folha_citada():
    c = verify_citation(
        "limite temporal e coisa distinta da especificacao",
        "Evento 239, ANEXO3, p. 3", CORPUS, SPANS,
    )

    assert c.veredito is Veredito.CONFIRMADO
    assert c.utilizavel is True
    assert c.exato is True


def test_citacao_errada_e_corrigida_em_vez_de_so_reprovada():
    """O fato costuma estar certo; quem erra e a referencia."""
    c = verify_citation(
        "relatorios sao emitidos pela Secretaria de Comercio Exterior",
        "Evento 239, ANEXO3, p. 3", CORPUS, SPANS,
    )

    assert c.veredito is Veredito.CONFIRMADO_EM_OUTRA_FOLHA
    assert c.citacao_correta == "Evento 252, OUT2, p. 5"
    assert c.utilizavel is True


def test_trecho_que_nao_existe_no_acervo_nao_passa():
    c = verify_citation(
        "o juizo determinou a imediata liberacao integral do deposito recursal",
        "Evento 239, ANEXO3, p. 3", CORPUS, SPANS,
    )

    assert c.veredito is Veredito.NAO_ENCONTRADO
    assert c.utilizavel is False
    assert c.citacao_correta is None


def test_acento_e_quebra_de_linha_nao_derrubam_o_confronto():
    """O OCR alterna acentuacao e quebra na mesma palavra entre folhas."""
    c = verify_citation(
        "limite\ntemporal é   coisa DISTINTA da especificação",
        "Evento 239, ANEXO3, p. 3", CORPUS, SPANS,
    )
    assert c.utilizavel is True


def test_borda_corrompida_ainda_confirma_pelo_nucleo_sem_alegar_exatidao():
    c = verify_citation(
        "XXXX a fixacao de limite temporal e coisa distinta da especificacao "
        "do que esta contido nesse periodo YYYY",
        "Evento 239, ANEXO3, p. 3", CORPUS, SPANS,
    )

    assert c.utilizavel is True
    assert c.exato is False


def test_folha_citada_que_nao_existe_nos_autos():
    c = verify_citation(
        "limite temporal e coisa distinta da especificacao",
        "Evento 999, INEXISTE1, p. 1", CORPUS, SPANS,
    )
    assert c.veredito is Veredito.FOLHA_INEXISTENTE


def test_citacao_sem_formato_processual():
    c = verify_citation(
        "limite temporal e coisa distinta da especificacao", "fl. 12", CORPUS, SPANS
    )
    assert c.veredito is Veredito.CITACAO_ILEGIVEL


def test_trecho_curto_nao_e_conferivel():
    """Poucos caracteres casam por acaso e nao provam nada."""
    c = verify_citation("periodo", "Evento 239, ANEXO3, p. 3", CORPUS, SPANS)

    assert c.veredito is Veredito.TRECHO_CURTO
    assert c.utilizavel is False


def test_citacao_sem_pagina_confere_no_documento_inteiro():
    c = verify_citation(
        "limite temporal e coisa distinta", "Evento 239, ANEXO3", CORPUS, SPANS
    )
    assert c.utilizavel is True


def test_filtro_devolve_so_o_conferido_e_corrige_a_referencia():
    fatos = [
        {"fato": "a", "trecho_literal": "limite temporal e coisa distinta",
         "citacao": "Evento 239, ANEXO3, p. 3"},
        {"fato": "b", "trecho_literal": "relatorios sao emitidos pela Secretaria de Comercio",
         "citacao": "Evento 239, ANEXO3, p. 3"},
        {"fato": "c", "trecho_literal": "o perito concluiu pela inexistencia de qualquer credito",
         "citacao": "Evento 239, ANEXO3, p. 3"},
    ]

    verificados = filter_verified_facts(fatos, CORPUS, SPANS)

    assert [f["fato"] for f in verificados] == ["a", "b"]
    assert verificados[1]["citacao"] == "Evento 252, OUT2, p. 5"
    assert verificados[0]["conferencia"]["utilizavel"] is True


def test_lista_vazia_nao_quebra():
    assert filter_verified_facts([], CORPUS, SPANS) == []
    assert filter_verified_facts(None, CORPUS, SPANS) == []


def test_normalizar_remove_acento_caixa_e_espaco():
    assert normalizar("  Órgão   Público\n") == "orgao publico"
