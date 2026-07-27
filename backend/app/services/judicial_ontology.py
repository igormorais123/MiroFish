"""
Ontologia de processo judicial.

Por que existe: a ontologia padrao descreve gente numa rede social — quem apoia
quem, quem influencia quem, quem repercute o que. Num processo isso nao existe.
O que existe e um conjunto fechado de documentos, um decisor unico e teses que
se sustentam ou caem conforme a prova esta ou nao nos autos.

O mecanismo de ontologia do sistema funciona; o que estava errado era o
vocabulario. Aqui ele fica trocado, sem reconstruir nada.

A pergunta que esta ontologia precisa saber responder — e a social nao sabe — e
"quais teses ficam orfas se o documento X nao vier".
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

# Vocabulario forense. Dois sinais bastam: um termo isolado aparece em texto
# comum ("autos" de um inqueritinho interno, "peticao" em sentido figurado), dois
# ja caracterizam material processual.
SINAIS_FORENSES = (
    r"\bvara\s+(federal|c[íi]vel|criminal|do trabalho)\b",
    r"\bjusti[çc]a\s+(federal|estadual|do trabalho)\b",
    r"\btrf[\s\-]?\d*\b",
    r"\b(stj|stf|tst|tse)\b",
    r"\bac[óo]rd[ãa]o\b",
    r"\bembargos\b",
    r"\bagravo\b",
    r"\bapela[çc][ãa]o\b",
    r"\brecurso\s+(especial|extraordin[áa]rio|inomindado)\b",
    r"\bliquida[çc][ãa]o\s+de\s+senten[çc]a\b",
    r"\bexecu[çc][ãa]o\s+fiscal\b",
    r"\bpeti[çc][ãa]o\s+inicial\b",
    r"\bcontesta[çc][ãa]o\b",
    r"\bautos\b",
    r"\bevento\s+\d+\b",
    r"\bintima[çc][ãa]o\b",
    r"\bsenten[çc]a\b",
    r"\bper[íi]cia\b",
    r"\blaudo\s+pericial\b",
    r"\bc[óo]digo\s+de\s+processo\s+civil\b|\bcpc\b",
)

MINIMO_DE_SINAIS = 2


def is_material_processual(texto: str) -> bool:
    """True quando o material tem densidade forense suficiente."""
    if not texto:
        return False
    alvo = texto.lower()
    encontrados = sum(1 for padrao in SINAIS_FORENSES if re.search(padrao, alvo))
    return encontrados >= MINIMO_DE_SINAIS


def _entidade(nome: str, descricao: str, atributos: List[str]) -> Dict[str, Any]:
    return {
        "name": nome,
        "description": descricao,
        "attributes": [
            {"name": a, "type": "text", "description": a.replace("_", " ")}
            for a in atributos
        ],
        "examples": [],
    }


def _aresta(nome: str, descricao: str, pares: List[tuple]) -> Dict[str, Any]:
    return {
        "name": nome,
        "description": descricao,
        "source_targets": [{"source": s, "target": t} for s, t in pares],
        "attributes": [],
    }


def build_judicial_ontology() -> Dict[str, Any]:
    """
    Ontologia fixa do dominio processual.

    Fixa de proposito: os elementos de um processo nao variam de caso para caso
    como variam os atores de um debate publico, e deixar o modelo reinventa-los
    a cada run so introduz ruido.
    """
    entity_types = [
        _entidade(
            "Evento",
            "Ato processual numerado nos autos",
            ["numero_evento", "data", "sujeito", "natureza"],
        ),
        _entidade(
            "Documento",
            "Peca, anexo ou laudo juntado ao processo",
            ["doc_id", "pagina", "evento_de_origem", "tipo"],
        ),
        _entidade(
            "Tese",
            "Proposicao juridica sustentada por uma das partes",
            ["parte_que_sustenta", "fundamento", "situacao"],
        ),
        _entidade(
            "Norma",
            "Dispositivo legal, sumula ou precedente invocado",
            ["referencia", "orgao_emissor", "vigencia"],
        ),
        _entidade(
            "Valor",
            "Quantia, indice ou criterio de calculo em disputa",
            ["montante", "indice", "marco_temporal", "origem_do_calculo"],
        ),
        _entidade(
            "Diligencia",
            "Providencia pendente que pode alterar o resultado",
            ["prazo", "custo_estimado", "impacto_decisorio", "responsavel"],
        ),
        _entidade(
            "Parte",
            "Quem figura no polo ativo ou passivo",
            ["polo", "representacao"],
        ),
        _entidade(
            "Orgao",
            "Juizo, tribunal ou auxiliar que atua no feito",
            ["instancia", "funcao_processual"],
        ),
    ]

    edge_types = [
        _aresta("SUSTENTA", "O documento ampara a tese", [
            ("Documento", "Tese"), ("Norma", "Tese"), ("Valor", "Tese"),
        ]),
        _aresta("CONTRADIZ", "Choca-se com a tese ou com outra peca", [
            ("Documento", "Tese"), ("Tese", "Tese"), ("Documento", "Documento"),
        ]),
        _aresta("DEPENDE_DE", "A tese fica orfa sem este elemento", [
            ("Tese", "Documento"), ("Tese", "Diligencia"), ("Valor", "Documento"),
        ]),
        _aresta("FOI_OMITIDO_EM", "Ponto nao enfrentado pela decisao", [
            ("Tese", "Evento"), ("Norma", "Evento"), ("Documento", "Evento"),
        ]),
        _aresta("JUNTADO_EM", "Documento ingressou nos autos neste ato", [
            ("Documento", "Evento"),
        ]),
        _aresta("PRATICADO_POR", "Autoria do ato processual", [
            ("Evento", "Parte"), ("Evento", "Orgao"),
        ]),
        _aresta("IMPUGNA", "Ato que ataca outro ato", [
            ("Evento", "Evento"),
        ]),
        _aresta("FUNDAMENTA_SE_EM", "Tese apoiada em dispositivo", [
            ("Tese", "Norma"),
        ]),
    ]

    return {
        "entity_types": entity_types,
        "edge_types": edge_types,
        "analysis_summary": (
            "Ontologia de materia processual: atos, documentos, teses, normas, "
            "valores e diligencias, com as relacoes que dizem o que sustenta e o "
            "que derruba cada tese."
        ),
        "domain": "materia_judicial",
    }
