"""Qualidade do relatorio: medidor de overlap (anti-parafrase) + gate editorial.

Phase 3 do roadmap v1.2 — "Relatorio nao deve repetir o upload".

- jaccard_similarity: medida n-gram entre dois textos.
- measure_overlap: aplica em relatorio vs upload, retorna alerta se > threshold.
- evaluate_section_grounding: checa se uma secao tem dado factual (numero) e citacao.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:%|R\$|reais|mil|milh[oõ]es|bilh[oõ]es|pp|p\.p\.|nós|n[oó]s|fatos|agentes|rodadas|dias|horas|minutos)?\b", re.IGNORECASE)
_QUOTE_RE = re.compile(r'"[^"]{8,}"|"[^"]{8,}"|"[^"]{8,}"')


def _normalize(text: str) -> list[str]:
    """Tokeniza, normaliza unicode (NFKD), lowercase, remove pontuacao."""
    if not text:
        return []
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    return [tok.lower() for tok in _WORD_RE.findall(cleaned) if len(tok) > 2]


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if n <= 0 or len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard_similarity(a: str, b: str, ngram: int = 5) -> float:
    """Jaccard sobre n-gramas de palavras. 0.0 = disjunto, 1.0 = identicos.

    n=5 captura paragrafos copiados literalmente sem alarmar coincidencias curtas.
    """
    ga = _ngrams(_normalize(a), ngram)
    gb = _ngrams(_normalize(b), ngram)
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    union = len(ga | gb)
    return inter / union if union else 0.0


def measure_overlap(report_md: str, upload_text: str, threshold: float = 0.30) -> dict:
    """Mede overlap relatorio<->upload e retorna metricas + alerta.

    Args:
        report_md: relatorio final em Markdown
        upload_text: material-base original
        threshold: fracao de overlap acima da qual disparamos alerta (default 30%)

    Returns:
        {
            "jaccard_5gram": 0.XX,
            "jaccard_3gram": 0.XX,
            "alert": bool,
            "threshold": float,
            "tokens_report": int,
            "tokens_upload": int,
        }
    """
    j5 = jaccard_similarity(report_md, upload_text, ngram=5)
    j3 = jaccard_similarity(report_md, upload_text, ngram=3)
    return {
        "jaccard_5gram": round(j5, 4),
        "jaccard_3gram": round(j3, 4),
        "alert": j5 > threshold,
        "threshold": threshold,
        "tokens_report": len(_normalize(report_md)),
        "tokens_upload": len(_normalize(upload_text)),
    }


def evaluate_section_grounding(content: str, known_entities: Iterable[str] | None = None) -> dict:
    """Avalia uma secao do relatorio: tem numero? tem citacao? tem entidade do grafo?

    Args:
        content: texto da secao
        known_entities: nomes de nos/entidades extraidas do grafo (opcional)

    Returns:
        {
            "has_number": bool,
            "has_quote": bool,
            "entity_hits": int,
            "entity_matches": [str],
            "score": float (0..1),
            "passes_gate": bool,  # True se score >= 0.5
        }
    """
    has_number = bool(_NUMBER_RE.search(content or ""))
    has_quote = bool(_QUOTE_RE.search(content or ""))

    entity_matches: list[str] = []
    if known_entities and content:
        norm_content = content.lower()
        for ent in known_entities:
            if not ent or len(ent) < 3:
                continue
            if ent.lower() in norm_content:
                entity_matches.append(ent)

    # Score: 0.4 numero + 0.2 quote + 0.4 entidade (cap em 1.0)
    score = 0.0
    if has_number:
        score += 0.4
    if has_quote:
        score += 0.2
    if entity_matches:
        score += min(0.4, 0.1 * len(entity_matches))

    return {
        "has_number": has_number,
        "has_quote": has_quote,
        "entity_hits": len(entity_matches),
        "entity_matches": entity_matches[:10],
        "score": round(score, 3),
        "passes_gate": score >= 0.5,
    }


def render_qc_block(overlap: dict, sections_eval: list[dict] | None = None) -> str:
    """Gera bloco Markdown 'QC: Cobertura e Grounding' para anexar ao relatorio."""
    j5 = overlap.get("jaccard_5gram", 0)
    j3 = overlap.get("jaccard_3gram", 0)
    alert = overlap.get("alert", False)
    flag = "⚠️ ALTO" if alert else "OK"

    lines = [
        "",
        "---",
        "",
        "## QC — Cobertura e Grounding",
        "",
        f"- **Overlap relatorio×upload (5-gram):** {j5:.1%} ({flag}, limite {overlap.get('threshold', 0.3):.0%})",
        f"- **Overlap relatorio×upload (3-gram):** {j3:.1%}",
        f"- **Tamanho relatorio:** {overlap.get('tokens_report', 0)} tokens · upload: {overlap.get('tokens_upload', 0)} tokens",
    ]

    if sections_eval:
        passed = sum(1 for s in sections_eval if s.get("passes_gate"))
        total = len(sections_eval)
        lines.append(f"- **Gate editorial:** {passed}/{total} secoes com grounding suficiente")
        for i, ev in enumerate(sections_eval, 1):
            mark = "✅" if ev.get("passes_gate") else "⚠️"
            lines.append(
                f"  - {mark} Secao {i}: score={ev.get('score', 0):.2f} "
                f"(num={ev.get('has_number')}, quote={ev.get('has_quote')}, ents={ev.get('entity_hits')})"
            )

    lines.append("")
    return "\n".join(lines)
