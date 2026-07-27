"""
Separa fato recuperado de eco do proprio prompt.

Por que existe: no caso Vale Trading o `quick_search` devolveu cerca de 11 mil
caracteres repetindo o texto do pedido, carimbados com "Origem: parametros
documentados no pedido", e isso foi contabilizado como conhecimento
recuperado. O relatorio saiu afirmando com a seguranca de quem leu os autos,
tendo lido apenas a si mesmo.

A regra e simples e verificavel: um fato que ja estava no prompt nao e
descoberta. Vale para trecho literal e para reformulacao proxima, medida por
sobreposicao de termos.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

# Acima disto, o fato e considerado reformulacao do prompt e nao recuperacao.
# 0.85 e deliberadamente alto: derrubar fato legitimo custa mais caro do que
# deixar passar um eco ocasional, porque o gate aborta o run.
SOBREPOSICAO_MAXIMA = 0.85
# Fatos muito curtos nao tem termos suficientes para a medida significar algo.
MINIMO_DE_TERMOS = 4


def _normaliza(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def _termos(texto: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", _normaliza(texto)) if len(t) > 2}


@dataclass
class ResultadoDoGate:
    recuperados: List[str] = field(default_factory=list)
    ecos: List[str] = field(default_factory=list)

    @property
    def total_recuperado(self) -> int:
        return len(self.recuperados)

    @property
    def seco(self) -> bool:
        """Nenhum fato sobreviveu: nao ha o que sustentar um relatorio."""
        return not self.recuperados

    def to_dict(self) -> dict:
        return {
            "facts_recovered": self.total_recuperado,
            "facts_echoed": len(self.ecos),
            "dry": self.seco,
        }


def is_eco(fato: str, prompt: str) -> bool:
    """
    True quando o fato apenas devolve o que o prompt ja dizia.

    Trecho literal do prompt e eco direto. Reformulacao e detectada pela fracao
    de termos do fato que ja aparecem no prompt.
    """
    fato_normalizado = _normaliza(fato)
    if not fato_normalizado:
        return True

    prompt_normalizado = _normaliza(prompt)
    if fato_normalizado in prompt_normalizado:
        return True

    termos_do_fato = _termos(fato)
    if len(termos_do_fato) < MINIMO_DE_TERMOS:
        # Curto demais para medir; so o teste literal acima vale.
        return False

    comuns = termos_do_fato & _termos(prompt)
    return (len(comuns) / len(termos_do_fato)) >= SOBREPOSICAO_MAXIMA


def filter_recovered_facts(fatos: Sequence[str], prompt: str) -> ResultadoDoGate:
    """Separa o que foi recuperado do que so devolveu o pedido."""
    resultado = ResultadoDoGate()
    for fato in fatos or []:
        if not (fato or "").strip():
            continue
        (resultado.ecos if is_eco(fato, prompt) else resultado.recuperados).append(fato)
    return resultado
