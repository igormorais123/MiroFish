"""
Confere a citacao contra a folha que ela aponta.

Por que existe: no ciclo original do caso Vale, o unico achado aproveitavel veio
com a citacao apontando para o documento errado — um fato verdadeiro fica
inutilizavel numa peca se a referencia nao confere. Rodando os autos de novo o
erro reapareceu em 1 de 17 fatos: o trecho estava em "Evento 252, OUT2, p. 5" e
saiu citado como "OUT3, p. 3".

O modelo escreve a citacao copiando o que viu; as vezes copia da folha vizinha.
Aqui isso e verificado, nao confiado: o trecho literal e procurado na folha
citada. Nao estando la, o gate procura em que folha ele realmente esta — o fato
costuma ser bom, quem erra e a referencia.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Sequence

# "Evento 239, EMBDECL1, p. 4" — a forma que sai de PageSpan.as_citation().
CITACAO = re.compile(r"Evento\s+(\d+)\s*,\s*([A-Z0-9_]+)(?:\s*,\s*p\.\s*(\d+))?", re.IGNORECASE)

# Trecho curto casa por acaso e nao prova nada.
MINIMO_DE_CARACTERES = 25
# Fatia central usada quando o OCR corrompeu as bordas do trecho.
MINIMO_DO_NUCLEO = 40


class Veredito(str, Enum):
    CONFIRMADO = "confirmado"
    CONFIRMADO_EM_OUTRA_FOLHA = "confirmado em outra folha"
    NAO_ENCONTRADO = "nao encontrado"
    CITACAO_ILEGIVEL = "citacao ilegivel"
    FOLHA_INEXISTENTE = "folha citada nao existe"
    TRECHO_CURTO = "trecho curto demais para conferir"


@dataclass(frozen=True)
class Conferencia:
    veredito: Veredito
    citacao_correta: Optional[str] = None
    exato: bool = False

    @property
    def utilizavel(self) -> bool:
        """So entra em peca o que foi achado na fonte."""
        return self.veredito in (Veredito.CONFIRMADO, Veredito.CONFIRMADO_EM_OUTRA_FOLHA)

    def to_dict(self) -> dict:
        return {
            "veredito": self.veredito.value,
            "citacao_correta": self.citacao_correta,
            "exato": self.exato,
            "utilizavel": self.utilizavel,
        }


def normalizar(texto: str) -> str:
    """
    Compara ignorando acento, caixa e quebra de linha.

    O OCR dos autos varia nos tres: a mesma palavra sai acentuada numa folha e
    sem acento na seguinte, e a quebra de linha cai em posicao diferente.
    """
    sem = unicodedata.normalize("NFKD", texto or "")
    sem = "".join(c for c in sem if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem).casefold().strip()


def _folhas_citadas(citacao: str, spans: Sequence[Any]) -> Optional[List[Any]]:
    m = CITACAO.search(citacao or "")
    if not m:
        return None
    evento, tipo, folha = m.group(1), m.group(2).upper(), m.group(3)
    return [
        s for s in spans
        if s.evento == evento
        and (s.tipo_documento or "").upper() == tipo
        and (folha is None or s.pagina_do_evento == folha)
    ]


def _contem(trecho_normalizado: str, texto: str) -> tuple:
    """(achou, exato). O nucleo cobre o caso de borda corrompida pelo OCR."""
    alvo = normalizar(texto)
    if trecho_normalizado in alvo:
        return True, True
    nucleo = trecho_normalizado[len(trecho_normalizado) // 4: 3 * len(trecho_normalizado) // 4]
    return (len(nucleo) >= MINIMO_DO_NUCLEO and nucleo in alvo), False


def verify_citation(
    trecho: str, citacao: str, corpus: str, spans: Sequence[Any]
) -> Conferencia:
    """
    Procura o trecho literal na folha citada; nao achando, varre o acervo.

    Devolver a folha certa vale mais do que so reprovar: o fato costuma estar
    correto e quem errou foi a referencia, e sem a referencia certa ele nao
    serve para nada.
    """
    alvo = normalizar(trecho)
    if len(alvo) < MINIMO_DE_CARACTERES:
        return Conferencia(Veredito.TRECHO_CURTO)

    candidatas = _folhas_citadas(citacao, spans)
    if candidatas is None:
        return Conferencia(Veredito.CITACAO_ILEGIVEL)
    if not candidatas:
        return Conferencia(Veredito.FOLHA_INEXISTENTE)

    achou, exato = _contem(alvo, " ".join(corpus[s.start:s.end] for s in candidatas))
    if achou:
        return Conferencia(Veredito.CONFIRMADO, candidatas[0].as_citation(), exato)

    for span in spans:
        achou, exato = _contem(alvo, corpus[span.start:span.end])
        if achou:
            return Conferencia(
                Veredito.CONFIRMADO_EM_OUTRA_FOLHA, span.as_citation(), exato
            )

    return Conferencia(Veredito.NAO_ENCONTRADO)


def filter_verified_facts(
    fatos: Sequence[dict], corpus: str, spans: Sequence[Any]
) -> List[dict]:
    """
    Devolve so os fatos achados na fonte, com a citacao corrigida quando preciso.

    Fato reprovado nao e silenciado: sai com `conferencia` para quem revisa
    entender por que caiu.
    """
    saida = []
    for fato in fatos or []:
        conferencia = verify_citation(
            fato.get("trecho_literal", ""), fato.get("citacao", ""), corpus, spans
        )
        item = dict(fato, conferencia=conferencia.to_dict())
        if conferencia.citacao_correta:
            item["citacao"] = conferencia.citacao_correta
        if conferencia.utilizavel:
            saida.append(item)
    return saida
