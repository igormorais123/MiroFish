"""
Proveniência com documento e folha — o que separa "a IA disse" de "está na fl. X".

O offset de caractere já ancorava a entidade no corpus, mas ninguém peticiona
citando offset. Aqui fica travado o índice de páginas e a citação que dele sai.
"""

from unittest.mock import patch

import pytest

from app.services.llm_entity_extractor import LLMEntityExtractor
from app.utils.file_parser import FileParser, PageSpan, locate_page


SPANS = [
    PageSpan(doc_id="parte1.pdf", doc_index=1, page=1, start=0, end=100),
    PageSpan(doc_id="parte1.pdf", doc_index=1, page=2, start=100, end=250),
    PageSpan(doc_id="parte2.pdf", doc_index=2, page=1, start=300, end=400),
]


# --- localizar a folha a partir do offset ---

@pytest.mark.parametrize("offset,pagina,doc", [
    (0, 1, "parte1.pdf"),
    (99, 1, "parte1.pdf"),
    (100, 2, "parte1.pdf"),
    (249, 2, "parte1.pdf"),
    (350, 1, "parte2.pdf"),
])
def test_offset_resolve_para_documento_e_folha(offset, pagina, doc):
    span = locate_page(offset, SPANS)
    assert (span.page, span.doc_id) == (pagina, doc)


def test_offset_entre_paginas_nao_e_atribuido_a_folha_anterior():
    """O cabeçalho de documento não pertence a nenhuma folha."""
    assert locate_page(275, SPANS) is None


def test_offset_negativo_ou_indice_vazio_nao_quebra():
    assert locate_page(-1, SPANS) is None
    assert locate_page(10, []) is None


def test_citacao_sai_no_formato_de_peca():
    assert SPANS[1].as_citation() == "parte1.pdf, p. 2"


# --- o índice sai alinhado com o texto que ele descreve ---

def test_offsets_do_indice_batem_com_o_corpus(tmp_path):
    """
    Se texto e offsets forem montados separadamente, divergem sem ninguém
    perceber — e a citação passa a apontar para a folha errada.
    """
    a = tmp_path / "doc_a.txt"
    a.write_text("primeira peca do processo", encoding="utf-8")
    b = tmp_path / "doc_b.txt"
    b.write_text("segunda peca juntada depois", encoding="utf-8")

    corpus, spans = FileParser.extract_with_page_index([str(a), str(b)])

    assert len(spans) == 2
    for span in spans:
        assert corpus[span.start:span.end].strip()
    assert corpus[spans[0].start:spans[0].end].strip() == "primeira peca do processo"
    assert corpus[spans[1].start:spans[1].end].strip() == "segunda peca juntada depois"


def test_documento_ilegivel_nao_desalinha_os_demais(tmp_path):
    """Uma falha de extração no meio não pode deslocar as folhas seguintes."""
    bom = tmp_path / "bom.txt"
    bom.write_text("conteudo legivel", encoding="utf-8")

    corpus, spans = FileParser.extract_with_page_index(
        [str(tmp_path / "inexistente.pdf"), str(bom)]
    )

    assert len(spans) == 1
    assert corpus[spans[0].start:spans[0].end].strip() == "conteudo legivel"


# --- a entidade carrega a citação ---

def _extrator():
    return LLMEntityExtractor.__new__(LLMEntityExtractor)


def test_entidade_ganha_documento_e_folha():
    bruta = {
        "name": "Contadoria Judicial", "type": "Organizacao", "summary": "", "relations": [],
        "_proveniencia": {"excerpt": "trecho", "char_offset": 120},
    }

    resultado = _extrator()._merge([[bruta]], 1, SPANS)

    atributos = resultado.entities[0].attributes
    assert atributos["doc_id"] == "parte1.pdf"
    assert atributos["page"] == 2
    assert atributos["citation"] == "parte1.pdf, p. 2"


def test_sem_indice_de_paginas_a_citacao_fica_vazia_e_nao_inventada():
    bruta = {
        "name": "CIEX", "type": "Conceito", "summary": "", "relations": [],
        "_proveniencia": {"excerpt": "t", "char_offset": 120},
    }

    atributos = _extrator()._merge([[bruta]], 1, None).entities[0].attributes

    assert atributos["citation"] is None
    # O offset continua registrado: é a âncora que existe sem paginação.
    assert atributos["char_offset"] == 120


def test_entidade_sem_ancora_nao_recebe_folha():
    bruta = {"name": "Inventada", "type": "X", "summary": "", "relations": [], "_proveniencia": None}

    atributos = _extrator()._merge([[bruta]], 1, SPANS).entities[0].attributes

    assert atributos["verbatim_found"] is False
    assert atributos["page"] is None


def test_reaparicao_em_outro_pedaco_traz_a_folha():
    """Primeira ocorrência sem âncora, segunda com: a folha precisa chegar."""
    sem = {"name": "SELIC", "type": "C", "summary": "", "relations": [], "_proveniencia": None}
    com = {
        "name": "SELIC", "type": "C", "summary": "", "relations": [],
        "_proveniencia": {"excerpt": "t", "char_offset": 350},
    }

    atributos = _extrator()._merge([[sem], [com]], 2, SPANS).entities[0].attributes

    assert atributos["occurrences"] == 2
    assert atributos["citation"] == "parte2.pdf, p. 1"


# --- normalização de tipos ---

def test_variante_acentuada_casa_com_o_tipo_da_ontologia():
    """O mesmo conceito aparecia partido em dois no grafo: Orgao e Órgão."""
    from app.services.llm_entity_extractor import normalize_type

    permitidos = ["Evento", "Documento", "Tese", "Norma", "Valor", "Diligencia", "Parte", "Orgao"]
    assert normalize_type("Órgão", permitidos) == "Orgao"
    assert normalize_type("Diligência", permitidos) == "Diligencia"
    assert normalize_type("ORGAO", permitidos) == "Orgao"


def test_tipo_fora_da_ontologia_e_preservado():
    """Não é filtro: tipo desconhecido continua visível para diagnóstico."""
    from app.services.llm_entity_extractor import normalize_type
    assert normalize_type("Pessoa", ["Evento", "Documento"]) == "Pessoa"


def test_sem_lista_de_permitidos_nada_muda():
    from app.services.llm_entity_extractor import normalize_type
    assert normalize_type("Órgão") == "Órgão"
    assert normalize_type("") == "Entity"


def test_merge_normaliza_o_tipo():
    from app.services.llm_entity_extractor import LLMEntityExtractor

    brutas = [
        {"name": "TRF4", "type": "Órgão", "summary": "", "relations": [], "_proveniencia": None},
        {"name": "STJ", "type": "Orgao", "summary": "", "relations": [], "_proveniencia": None},
    ]
    resultado = LLMEntityExtractor._merge(None, [brutas], 1, None, ["Orgao"])

    assert resultado.entity_types == {"Orgao"}


# --- arestas tipadas: a ponte entre o grafo e os produtos do escritorio ---

def test_relacao_vira_aresta_com_nome_da_ontologia():
    """
    Sem nome, a aresta nao e consultavel: `build_coverage_matrix` procura
    SUSTENTA e CONTRADIZ por nome e devolvia matriz vazia sobre grafo cheio.
    """
    from app.services.llm_entity_extractor import parse_relation

    aresta = parse_relation({"tipo": "sustenta", "alvo": "Tese do CIEX"}, ["SUSTENTA"])

    assert aresta["edge_name"] == "SUSTENTA"
    assert aresta["target"] == "Tese do CIEX"
    assert aresta["direction"] == "outgoing"


def test_relacao_acentuada_casa_com_a_aresta():
    from app.services.llm_entity_extractor import parse_relation
    assert parse_relation(
        {"tipo": "Diligência", "alvo": "X"}, ["Diligencia"]
    )["edge_name"] == "Diligencia"


def test_frase_solta_e_preservada_mas_nao_vira_aresta_consultavel():
    """Formato antigo continua entrando; so nao finge ser relacao tipada."""
    from app.services.llm_entity_extractor import parse_relation

    aresta = parse_relation("relaciona-se de algum modo com a outra peca")

    assert aresta["edge_name"] == ""
    assert aresta["fact"].startswith("relaciona-se")


def test_relacao_sem_alvo_e_descartada():
    from app.services.llm_entity_extractor import parse_relation
    assert parse_relation({"tipo": "SUSTENTA"}) is None
    assert parse_relation({"tipo": "SUSTENTA", "alvo": "  "}) is None
    assert parse_relation("") is None
    assert parse_relation(None) is None


def test_merge_entrega_grafo_que_a_matriz_de_cobertura_consegue_ler():
    """Teste de ponta: extracao -> grafo -> produto do escritorio."""
    from app.services.case_products import build_coverage_matrix
    from app.services.llm_entity_extractor import LLMEntityExtractor

    brutas = [
        {"name": "Tese do credito-premio", "type": "Tese", "summary": "",
         "relations": [{"tipo": "DEPENDE_DE", "alvo": "Guia de 1996"}],
         "_proveniencia": None},
        {"name": "Guia de 1996", "type": "Documento", "summary": "",
         "relations": [{"tipo": "SUSTENTA", "alvo": "Tese do credito-premio"}],
         "_proveniencia": None},
    ]

    resultado = LLMEntityExtractor._merge(
        None, [brutas], 1, None, ["Tese", "Documento"], ["SUSTENTA", "DEPENDE_DE"]
    )
    cobertura = build_coverage_matrix(resultado.entities)

    assert len(cobertura) == 1
    assert cobertura[0].sustentada_por == ["Guia de 1996"]
    assert cobertura[0].depende_de == ["Guia de 1996"]
    assert cobertura[0].orfa is False


def test_atributos_lidos_chegam_na_entidade_e_alimentam_a_cronologia():
    from app.services.case_products import build_timeline
    from app.services.llm_entity_extractor import LLMEntityExtractor

    brutas = [{
        "name": "Evento 239", "type": "Evento", "summary": "embargos de declaracao",
        "attributes": {"numero_evento": "239", "data": "12/03/2024", "sujeito": "Vale Trading"},
        "relations": [], "_proveniencia": None,
    }]

    resultado = LLMEntityExtractor._merge(None, [brutas], 1, None, ["Evento"], [])
    linha = build_timeline(resultado.entities)

    assert linha[0].data == "2024-03-12"
    assert linha[0].sujeito == "Vale Trading"
    assert linha[0].evento == "239"


def test_reaparicao_completa_atributo_que_faltava_sem_sobrescrever():
    from app.services.llm_entity_extractor import LLMEntityExtractor

    primeiro = {"name": "Evento 239", "type": "Evento", "summary": "",
                "attributes": {"data": "12/03/2024"}, "relations": [], "_proveniencia": None}
    segundo = {"name": "Evento 239", "type": "Evento", "summary": "",
               "attributes": {"data": "01/01/1900", "sujeito": "Vale Trading"},
               "relations": [], "_proveniencia": None}

    atributos = LLMEntityExtractor._merge(
        None, [[primeiro], [segundo]], 2, None, ["Evento"], []
    ).entities[0].attributes

    assert atributos["data"] == "12/03/2024"
    assert atributos["sujeito"] == "Vale Trading"


def test_aresta_repetida_entre_pedacos_nao_duplica():
    from app.services.llm_entity_extractor import LLMEntityExtractor

    rel = {"tipo": "SUSTENTA", "alvo": "Tese X"}
    bruta = {"name": "Doc", "type": "Documento", "summary": "",
             "relations": [rel], "_proveniencia": None}

    entidade = LLMEntityExtractor._merge(
        None, [[dict(bruta)], [dict(bruta)]], 2, None, ["Documento"], ["SUSTENTA"]
    ).entities[0]

    assert len(entidade.related_edges) == 1


# --- ancoragem pela evidencia literal ---

def test_entidade_nomeada_por_parafrase_ancora_pela_evidencia():
    """
    Uma tese e nomeada por parafrase e uma norma por forma extensa; nenhuma das
    duas aparece assim na folha. So pelo nome, 47% do acervo da Vale ficou sem
    ancora — a entidade existia, o nome e que nao era literal.
    """
    from app.services.llm_entity_extractor import find_excerpt

    folha = "Nesse sentido, o art. 604 do CPC ampara a liquidacao por calculo."
    p = find_excerpt(
        "Artigo 604 do Codigo de Processo Civil", folha, 1000,
        evidencia="art. 604 do CPC",
    )

    assert p is not None
    assert p["ancorado_por"] == "evidencia"
    assert p["char_offset"] == 1000 + folha.find("art. 604")


def test_nome_literal_tem_precedencia_sobre_a_evidencia():
    from app.services.llm_entity_extractor import find_excerpt

    folha = "a SECEX certificou; adiante, a SECEX reiterou"
    p = find_excerpt("SECEX", folha, 0, evidencia="reiterou")

    assert p["ancorado_por"] == "nome"
    assert p["char_offset"] == folha.find("SECEX")


def test_evidencia_que_nao_esta_na_folha_nao_ancora():
    """Evidencia parafraseada e alucinacao: nao pode virar pincite."""
    from app.services.llm_entity_extractor import find_excerpt
    assert find_excerpt("Tese X", "texto sem relacao alguma", 0,
                        evidencia="o juizo assim decidiu") is None


def test_evidencia_curta_demais_nao_ancora():
    """Agulha de 3 caracteres casa por acaso e ancoraria na folha errada."""
    from app.services.llm_entity_extractor import find_excerpt
    assert find_excerpt("Tese X", "de fato o pedido procede", 0, evidencia="de") is None


# --- resposta com texto sobrando ---

def test_json_com_comentario_depois_ainda_e_lido():
    """"Extra data" derrubou 3 dos 1.164 pedacos do acervo da Vale."""
    from app.services.llm_entity_extractor import loads_first_object

    d = loads_first_object('{"entities": [{"name": "SECEX"}]}\nSegue o resumo...')

    assert d["entities"][0]["name"] == "SECEX"


def test_json_com_cerca_e_preambulo():
    from app.services.llm_entity_extractor import loads_first_object
    assert loads_first_object('Claro! {"entities": []} espero ter ajudado')["entities"] == []


def test_resposta_sem_json_falha_de_forma_explicita():
    import pytest as _pytest
    from app.services.llm_entity_extractor import loads_first_object
    with _pytest.raises(ValueError):
        loads_first_object("nao consegui processar este trecho")


# --- erro de digitacao no nome da aresta ---

def test_variante_com_erro_de_digitacao_casa_com_a_aresta():
    """FUNDAMENTA_SEM e FUNDAMENTAMENTA_SE_EM viraram arestas proprias no acervo."""
    from app.services.llm_entity_extractor import normalize_type

    permitidos = ["FUNDAMENTA_SE_EM", "SUSTENTA", "CONTRADIZ"]
    assert normalize_type("FUNDAMENTA_SEM", permitidos) == "FUNDAMENTA_SE_EM"
    assert normalize_type("FUNDAMENTAMENTA_SE_EM", permitidos) == "FUNDAMENTA_SE_EM"


def test_tipo_realmente_diferente_nao_e_absorvido_por_semelhanca():
    """O corte precisa ser alto o bastante para nao fundir tipos distintos."""
    from app.services.llm_entity_extractor import normalize_type
    assert normalize_type("Pessoa", ["Parte", "Orgao"]) == "Pessoa"
    assert normalize_type("IMPUGNA", ["SUSTENTA", "CONTRADIZ"]) == "IMPUGNA"


def test_barra_solta_no_trecho_copiado_nao_derruba_a_resposta():
    """"R\$" e o que o OCR deixa para tras: barra que nao inicia escape valido."""
    from app.services.llm_entity_extractor import loads_first_object

    d = loads_first_object(r'{"entities": [{"name": "X", "evidencia": "valor de R\$ 382.632"}]}')

    assert d["entities"][0]["evidencia"] == "valor de R$ 382.632"


def test_aspa_nao_escapada_derruba_so_a_entidade_e_nao_o_pedaco():
    """
    Pedir copia literal trouxe aspa junto e partiu o objeto no meio. Perder a
    entidade avariada custa uma linha; perder o pedaco custa folhas dos autos.
    """
    from app.services.llm_entity_extractor import loads_first_object

    bruto = (
        '{"entities": ['
        '{"name": "A", "attributes": {"data": "12/03/2024"}}, '
        '{"name": "B", "evidencia": "disse "assim" ali"}, '
        '{"name": "C", "attributes": {"polo": "ativo"}}]}'
    )
    entidades = loads_first_object(bruto)["entities"]

    # A entidade com objeto aninhado precisa sobreviver: e a mais completa.
    assert [e["name"] for e in entidades] == ["A", "C"]
    assert entidades[0]["attributes"]["data"] == "12/03/2024"
