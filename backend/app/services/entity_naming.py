"""
Politica de nomeacao de agentes sinteticos.

Por que existe: no caso Vale Trading, os perfis da simulacao se chamavam
"Uniao", "Contadoria Judicial" e "13a Vara Federal de Porto Alegre/RS", e
publicavam falas geradas por modelo. Fala sintetica atribuida a orgao real,
persistida em banco, vira passivo no momento em que qualquer artefato migra
para fora — e a neutralizacao tem que ser na origem, nao no relatorio final.

O papel processual e o que interessa para a deliberacao e permanece. O que sai
e a identificacao nominal do orgao. O nome original continua registrado no
perfil para auditoria interna, apenas nao e o que o agente ostenta.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# Cada padrao mapeia para o papel que o agente exerce no debate. A ordem
# importa: o primeiro que casar decide, entao o mais especifico vem antes.
PADROES_INSTITUCIONAIS: Tuple[Tuple[str, str], ...] = (
    (r"\b(vara|ju[ií]zo|juizado)\b", "Juízo de primeiro grau"),
    # `trf\d*` porque a sigla vem colada ao numero da regiao: TRF4, TRF-4, TRF 4.
    (r"\b(trf[\s\-]?\d*|tribunal regional federal)\b", "Tribunal de segundo grau"),
    (r"\b(stj|superior tribunal de justi[çc]a)\b", "Corte superior"),
    (r"\b(stf|supremo tribunal federal)\b", "Corte constitucional"),
    (r"\b(tribunal|c[âa]mara|turma|se[çc][ãa]o|desembargador)\b", "Órgão colegiado"),
    (r"\b(pgfn|procuradoria|advocacia-geral|agu)\b", "Representação judicial da parte pública"),
    (r"\b(minist[ée]rio p[úu]blico|mpf|procurador da rep[úu]blica)\b", "Ministério Público"),
    (r"\b(receita federal|fazenda nacional|fisco)\b", "Autoridade fiscal"),
    (r"\b(contadoria|perito|per[íi]cia|assistente t[ée]cnico)\b", "Auxiliar técnico do juízo"),
    (r"\b(uni[ãa]o|fazenda p[úu]blica|estado|munic[íi]pio)\b", "Parte pública"),
    (r"\b(secretaria|minist[ée]rio|autarquia|ag[êe]ncia reguladora)\b", "Órgão da administração"),
    (r"\b(cartório|serventia|of[íi]cio de registro)\b", "Serventia extrajudicial"),
)


def papel_institucional(nome: str) -> Optional[str]:
    """
    Devolve o papel funcional quando o nome designa instituicao, senao None.

    Pessoas fisicas e empresas privadas passam direto: o problema e atribuir
    fala a orgao publico, nao a qualquer entidade nomeada.
    """
    if not nome or not nome.strip():
        return None
    alvo = nome.strip().lower()
    for padrao, papel in PADROES_INSTITUCIONAIS:
        if re.search(padrao, alvo):
            return papel
    return None


def is_institucional(nome: str) -> bool:
    return papel_institucional(nome) is not None


def nome_publico(nome: str, ordinal: Optional[int] = None) -> str:
    """
    Nome que o agente ostenta.

    Instituicao vira o papel; quando ha mais de um agente no mesmo papel, o
    ordinal os distingue sem reintroduzir a identificacao.
    """
    papel = papel_institucional(nome)
    if papel is None:
        return nome
    return f"{papel} {ordinal}" if ordinal and ordinal > 1 else papel


def username_publico(nome_exibido: str, sufixo: int) -> str:
    """Handle derivado do nome ja neutralizado, nunca do original."""
    base = re.sub(r"[^a-z0-9]+", "_", nome_exibido.lower()).strip("_") or "agente"
    return f"{base}_{sufixo}"
