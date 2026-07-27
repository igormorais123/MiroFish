"""
Quando a simulacao de agentes vale como evidencia, e quando nao vale.

Por que existe: um modelo baseado em agentes so informa quando o fenomeno
modelado tem difusao — muitos atores, influencia mutua, resultado emergente.
Num processo judicial nao ha nada disso: ha um decisor unico e um conjunto
fechado de documentos. Rodar o ABM ali produz confianca falsa com aparencia
sofisticada, que foi exatamente o que aconteceu no caso Vale Trading: 36 tweets
sinteticos viraram base para percentuais de conviccao.

O ABM continua no produto para os dominios em que nasceu — eleitoral,
reputacional, difusao de narrativa. Para litigio, so com validacao declarada.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Dominios em que difusao existe e o ABM tem o que modelar.
DOMINIOS_COM_DIFUSAO = frozenset({
    "eleitoral_territorial",
    "reputacional",
    "general_public",
    "servidores_federais",
})

# Dominios em que o resultado depende de um decisor, nao de agregacao social.
DOMINIOS_COM_DECISOR_UNICO = frozenset({
    "materia_judicial",
})


@dataclass(frozen=True)
class VeredictoDoAbm:
    aplicavel: bool
    motivo: str
    exige_validacao_declarada: bool = False

    def to_dict(self) -> dict:
        return {
            "abm_applicable": self.aplicavel,
            "reason": self.motivo,
            "requires_declared_validation": self.exige_validacao_declarada,
        }


def evaluate_abm_applicability(
    domain_id: Optional[str],
    *,
    validacao_declarada: bool = False,
) -> VeredictoDoAbm:
    """
    Diz se a simulacao de agentes deve rodar para este dominio.

    `validacao_declarada` e a saida consciente: quem afirmar que validou o
    modelo contra dado real assume o resultado. Nao e um interruptor de
    conveniencia — e um registro de quem respondeu pela afirmacao.
    """
    dominio = (domain_id or "").strip().lower()

    if dominio in DOMINIOS_COM_DECISOR_UNICO:
        if validacao_declarada:
            return VeredictoDoAbm(
                aplicavel=True,
                motivo=(
                    "Dominio de decisor unico, liberado por validacao declarada: o "
                    "resultado responde por quem a declarou."
                ),
                exige_validacao_declarada=True,
            )
        return VeredictoDoAbm(
            aplicavel=False,
            motivo=(
                "Dominio de decisor unico e conjunto fechado de documentos: nao ha "
                "difusao a modelar, e comportamento judicial nao tem amostra para "
                "backtest. Use recuperacao documental e contraditorio antecipado."
            ),
            exige_validacao_declarada=True,
        )

    if dominio in DOMINIOS_COM_DIFUSAO:
        return VeredictoDoAbm(
            aplicavel=True,
            motivo="Dominio com difusao entre muitos atores: e o que o ABM modela.",
        )

    return VeredictoDoAbm(
        aplicavel=False,
        motivo=(
            f"Dominio '{dominio or 'nao informado'}' sem difusao verificada; "
            "rodar o ABM aqui produziria confianca sem lastro."
        ),
        exige_validacao_declarada=True,
    )
