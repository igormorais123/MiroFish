"""
As quatro correcoes que destravam o grafo, diagnosticadas no caso Vale Trading.

O grafo saia com 0 nos e as quatro ferramentas de consulta falhavam juntas por
lerem dele. Aqui ficam travadas: leitura do corpus inteiro, proveniencia por
entidade, degradacao visivel e gate que barra grafo vazio.
"""

import json
from unittest.mock import patch

from app.services import llm_entity_extractor as lee
from app.services.zep_tools import SearchResult


# --- 1. o corpus inteiro e lido, nao so os primeiros 8000 caracteres ---

def test_texto_longo_vira_varios_pedacos():
    """Nove PDFs concatenados construiam o grafo so a partir da capa do primeiro."""
    texto = "a" * (lee.CHUNK_SIZE * 3)
    pedacos = lee.split_into_chunks(texto)

    assert len(pedacos) >= 3
    # O ultimo pedaco alcanca o fim do corpus.
    inicio_final, trecho_final = pedacos[-1]
    assert inicio_final + len(trecho_final) == len(texto)


def test_pedacos_se_sobrepoem_para_nao_partir_entidade():
    texto = "b" * (lee.CHUNK_SIZE * 2)
    pedacos = lee.split_into_chunks(texto)

    primeiro_fim = pedacos[0][0] + len(pedacos[0][1])
    assert pedacos[1][0] < primeiro_fim


def test_texto_curto_continua_em_um_pedaco():
    assert lee.split_into_chunks("texto curto") == [(0, "texto curto")]


def test_texto_vazio_nao_gera_pedaco():
    assert lee.split_into_chunks("") == []


def test_corpus_absurdo_para_no_teto_de_pedacos(monkeypatch):
    """Guarda para um corpus gigante nao consumir a assinatura inteira."""
    monkeypatch.setattr(lee, "MAX_CHUNKS", 3)
    assert len(lee.split_into_chunks("c" * (lee.CHUNK_SIZE * 20))) == 3


# --- 2. proveniencia: cada entidade carrega o trecho que a sustenta ---

def test_entidade_presente_no_texto_recebe_trecho_e_offset():
    trecho = "O processo tramita na 13a Vara Federal de Porto Alegre desde 1996."
    prov = lee.find_excerpt("13a Vara Federal", trecho, offset=5000)

    assert prov is not None
    assert "13a Vara Federal" in prov["excerpt"]
    # Offset absoluto no corpus, nao relativo ao pedaco.
    assert prov["char_offset"] == 5000 + trecho.index("13a Vara Federal")


def test_entidade_ausente_do_texto_nao_ganha_ancora():
    """Nome que nao aparece no texto foi inventado, nao extraido."""
    assert lee.find_excerpt("Tribunal de Haia", "texto sobre credito-premio de IPI", 0) is None


def test_ancoragem_ignora_diferenca_de_caixa():
    assert lee.find_excerpt("vale trading", "A VALE TRADING S.A. recorreu.", 0) is not None


# --- 3. juncao dos pedacos ---

def _bruta(nome, prov=None, tipo="Organizacao"):
    return {"name": nome, "type": tipo, "summary": "s", "relations": [], "_proveniencia": prov}


def test_mesma_entidade_em_pedacos_diferentes_vira_um_no_so():
    prov = {"excerpt": "trecho", "char_offset": 10}
    resultado = lee.LLMEntityExtractor._merge(
        None, [[_bruta("Vale Trading", prov)], [_bruta("vale trading", prov)]], 2
    )

    assert resultado.total_count == 1
    assert resultado.entities[0].attributes["occurrences"] == 2


def test_entidade_sem_ancora_e_mantida_porem_marcada():
    """O gate precisa distinguir leitura ancorada de alucinacao."""
    resultado = lee.LLMEntityExtractor._merge(None, [[_bruta("Entidade Inventada", None)]], 1)

    entidade = resultado.entities[0]
    assert entidade.attributes["verbatim_found"] is False
    assert entidade.attributes["source_excerpt"] is None


def test_ancora_de_um_pedaco_posterior_preenche_entidade_ja_vista():
    prov = {"excerpt": "achado", "char_offset": 99}
    resultado = lee.LLMEntityExtractor._merge(
        None, [[_bruta("CIEX", None)], [_bruta("CIEX", prov)]], 2
    )

    entidade = resultado.entities[0]
    assert entidade.attributes["verbatim_found"] is True
    assert entidade.attributes["char_offset"] == 99


def test_entidade_sem_nome_e_descartada():
    resultado = lee.LLMEntityExtractor._merge(None, [[_bruta("   ")]], 1)
    assert resultado.total_count == 0


def test_falha_num_pedaco_nao_derruba_o_corpus():
    """Um pedaco que volta JSON quebrado nao pode zerar o grafo inteiro."""
    extrator = lee.LLMEntityExtractor.__new__(lee.LLMEntityExtractor)
    respostas = iter([
        "nao e json",
        json.dumps({"entities": [{"name": "SELIC", "type": "Conceito", "summary": "", "relations": []}]}),
    ])

    class _Cliente:
        def chat(self, **kwargs):
            return next(respostas)

    extrator.client = _Cliente()
    with patch.object(lee, "split_into_chunks", return_value=[(0, "x"), (1, "SELIC")]):
        resultado = extrator.extract_entities("texto")

    assert [e.name for e in resultado.entities] == ["SELIC"]


# --- 4. degradacao visivel ---

def test_busca_normal_nao_e_degradada():
    r = SearchResult(facts=["f"], edges=[], nodes=[], query="q", total_count=1)
    assert r.degraded is False
    assert "DEGRADADO" not in r.to_text()


def test_busca_degradada_avisa_o_modelo_no_texto():
    """Sem o aviso, o modelo trata dado local como fato recuperado do grafo."""
    r = SearchResult(
        facts=["f"], edges=[], nodes=[], query="q", total_count=1,
        degraded_reason="Graphiti indisponivel; busca atendida por dados locais",
    )

    texto = r.to_text()
    assert r.degraded is True
    assert "DEGRADADO" in texto
    assert "Graphiti indisponivel" in texto


def test_degradacao_viaja_no_dicionario_para_auditoria():
    r = SearchResult(facts=[], edges=[], nodes=[], query="q", total_count=0,
                     degraded_reason="motivo")
    assert r.to_dict()["degraded"] is True
    assert r.to_dict()["degraded_reason"] == "motivo"
