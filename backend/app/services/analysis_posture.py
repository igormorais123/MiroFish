"""
Postura da analise: de que lugar o sistema fala.

Por que existe: a consulta do caso Vale encerrava com ordem expressa — "a IA
deve atuar como perito assistente da parte e nao como perito do juizo". O
sistema entregou perito do juizo, com veredito de nao-promocao. Estava
tecnicamente correto sobre o quantum e era inutil, quando nao adverso, para
quem precisava sustentar a tese do cliente.

Postura nao muda o que e verdade. Muda o que a analise procura, o que ela
destaca e para quem ela serve. Rodar as tres sobre o mesmo material e o que
transforma um veredito solitario em avaliacao utilizavel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Postura:
    id: str
    rotulo: str
    mandato: str
    procura: str
    entrega: str

    def prompt_block(self) -> str:
        return (
            f"POSTURA: {self.rotulo}\n"
            f"Mandato: {self.mandato}\n"
            f"O que procurar: {self.procura}\n"
            f"O que entregar: {self.entrega}"
        )


ASSISTENTE_DA_PARTE = Postura(
    id="assistente_da_parte",
    rotulo="Assistente tecnico da parte",
    mandato=(
        "Voce assiste tecnicamente a parte que contratou o trabalho. Nao e "
        "imparcial e nao deve simular imparcialidade: seu dever e a melhor "
        "sustentacao tecnica possivel da posicao do cliente, dentro do que os "
        "autos permitem afirmar."
    ),
    procura=(
        "O que sustenta a tese do cliente; onde a prova ja existe e nao foi "
        "aproveitada; quais fragilidades da parte contraria podem ser exploradas; "
        "que diligencia converteria duvida em prova."
    ),
    entrega=(
        "Linha de sustentacao com a prova que a ampara, ponto a ponto, e a lista "
        "do que falta obter. Fragilidade da propria tese entra como risco a "
        "administrar, nao como recomendacao de desistir."
    ),
)

PERITO_DO_JUIZO = Postura(
    id="perito_do_juizo",
    rotulo="Perito do juizo",
    mandato=(
        "Voce e auxiliar imparcial. Nao serve a nenhuma das partes e responde "
        "apenas ao que os autos comprovam."
    ),
    procura=(
        "O que esta efetivamente comprovado; onde cada lado extrapola o que a "
        "prova permite; qual metodologia resiste a contestacao."
    ),
    entrega=(
        "Conclusao tecnica com o grau de comprovacao de cada ponto e a "
        "metodologia que a sustenta."
    ),
)

RED_TEAM = Postura(
    id="red_team",
    rotulo="Red team",
    mandato=(
        "Voce ataca a tese do cliente com a maior forca disponivel, como faria a "
        "parte contraria bem preparada."
    ),
    procura=(
        "O ataque mais forte que a tese sofre; a prova ausente que sera cobrada; "
        "a contradicao entre as proprias pecas do cliente."
    ),
    entrega=(
        "Os ataques em ordem de gravidade, cada um com o que precisaria existir "
        "nos autos para neutraliza-lo."
    ),
)

POSTURAS: Dict[str, Postura] = {
    p.id: p for p in (ASSISTENTE_DA_PARTE, PERITO_DO_JUIZO, RED_TEAM)
}

# Em materia judicial o pedido e quase sempre de assistencia tecnica a uma
# parte; o perito do juizo e quem o juizo nomeia, nao quem o escritorio contrata.
POSTURA_PADRAO = ASSISTENTE_DA_PARTE


def get_postura(identificador: str | None) -> Postura:
    """Postura pelo id, caindo no padrao quando nao reconhecida."""
    return POSTURAS.get((identificador or "").strip().lower(), POSTURA_PADRAO)


def todas() -> Tuple[Postura, ...]:
    """As tres, na ordem em que se leem: sustentacao, isencao, ataque."""
    return (ASSISTENTE_DA_PARTE, PERITO_DO_JUIZO, RED_TEAM)
