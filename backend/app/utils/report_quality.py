"""Qualidade do relatorio: medidor de overlap (anti-parafrase) + gate editorial.

Phase 3 do roadmap v1.2 — "Relatorio nao deve repetir o upload".

- jaccard_similarity: medida n-gram entre dois textos.
- measure_overlap: aplica em relatorio vs upload, retorna alerta se > threshold.
- evaluate_section_grounding: checa se uma secao tem dado factual (numero) e citacao.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable, Mapping

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)
_NUMBER_RE = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:%|R\$|reais|mil|milh[oõ]es|bilh[oõ]es|pp|p\.p\.|nós|n[oó]s|fatos|agentes|rodadas|dias|horas|minutos)?", re.IGNORECASE)
_QUOTE_RE = re.compile(r'"([^"\n]{8,})"|“([^”\n]{8,})”|‘([^’\n]{8,})’')
_MARKDOWN_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_AUDIT_BLOCK_RE = re.compile(r"\n---\n\n## QC[\s\S]*$", re.IGNORECASE)
_INFERENCE_MARKER_RE = re.compile(
    r"\[(?:inferencia|simulacao|estimativa|campo necessario|calibracao|sugest[aã]o operacional)[^\]]*\]"
    r"|inferencia|simulacao|estimad[ao]s?|calibrad[ao]s?|sugest[aã]o operacional|nao estimavel|sem dados suficientes",
    re.IGNORECASE,
)
_TABLE_SEPARATOR_RE = re.compile(r"^\|?[\s:\-]+\|[\s:\-\|]*$")
_TABLE_HEADER_RE = re.compile(
    r"\|.*\b(?:cen[aá]rio|probabilidade|narrativa|gatilho|risco|confian[cç]a)\b.*\|",
    re.IGNORECASE,
)


_METRIC_CATEGORY_TERMS = {
    "nodes": ("node", "nodes", "no", "nos", "entidade", "entidades", "entity", "entities"),
    "relationships": ("edge", "edges", "relation", "relations", "relacao", "relacoes", "relationship", "relationships", "aresta", "arestas"),
    "facts": ("fact", "facts", "fato", "fatos", "edge", "edges", "relation", "relations", "relationship", "relationships"),
    "rounds": ("round", "rounds", "rodada", "rodadas"),
    "hours": ("hour", "hours", "hora", "horas"),
    "minutes": ("minute", "minutes", "minuto", "minutos"),
    "actions": ("action", "actions", "acao", "acoes"),
    "agents": ("agent", "agents", "agente", "agentes", "profile", "profiles", "perfil", "perfis"),
    "probability": ("probability", "probabilidade", "chance", "percentual", "cenario", "cenarios", "base", "otimista", "contrario", "risco", "riscos", "confianca", "conviccao"),
}

_PREDICTIVE_NUMERIC_CONTEXT_RE = re.compile(
    r"\b(?:probabilidade|chance|cen[aá]rio|risco|confian[cç]a|convic[cç][aã]o|base|otimista|contr[aá]rio)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> list[str]:
    """Tokeniza, normaliza unicode (NFKD), lowercase, remove pontuacao."""
    if not text:
        return []
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    return [tok.lower() for tok in _WORD_RE.findall(cleaned) if len(tok) > 2]


def _normalize_ascii_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    return cleaned.lower()


def _normalize_text_for_match(text: str) -> str:
    """Normaliza texto para comparacao conservadora de citacoes."""
    return " ".join(_normalize(text))


def _strip_code_fences(text: str) -> str:
    """Remove blocos de codigo para nao auditar exemplos como se fossem claims."""
    return _MARKDOWN_FENCE_RE.sub(" ", text or "")


def _strip_generated_audit_blocks(text: str) -> str:
    """Remove blocos QC/auditoria acrescentados pelo proprio sistema."""
    return _AUDIT_BLOCK_RE.sub("", text or "")


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


def _coerce_positive_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else 0
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            parsed = int(match.group(0))
            return parsed if parsed > 0 else 0
    return 0


def _nested_mapping(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, Mapping) else {}


def _first_positive_metric(metrics: Mapping[str, Any], keys: Iterable[str]) -> int:
    for key in keys:
        value = _coerce_positive_int(metrics.get(key))
        if value > 0:
            return value
    return 0


def _known_platforms(metrics: Mapping[str, Any]) -> list[str]:
    direct = metrics.get("platforms")
    if isinstance(direct, list):
        names = [str(item).strip() for item in direct if str(item).strip()]
        if names:
            return names

    candidates = []
    diversity = _nested_mapping(metrics, "diversity")
    for platform_counts in (
        metrics.get("platform_counts"),
        diversity.get("platform_counts"),
    ):
        if isinstance(platform_counts, Mapping):
            for name, count in platform_counts.items():
                if _coerce_positive_int(count) > 0:
                    candidates.append(str(name))

    for key in ("twitter_actions_count", "reddit_actions_count"):
        if _coerce_positive_int(metrics.get(key)) > 0:
            candidates.append(key.replace("_actions_count", ""))

    seen: set[str] = set()
    result: list[str] = []
    for name in candidates:
        normalized = _normalize_ascii_text(name).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(name)
    return result


def _line_issue(issue_id: str, message: str, line_no: int, line: str) -> dict:
    return {
        "id": issue_id,
        "severity": "error",
        "line": line_no,
        "message": message,
        "context": line.strip()[:240],
    }


def audit_report_content_consistency(report_md: str, structured_metrics: Mapping[str, Any] | None = None) -> dict:
    """Audita problemas editoriais que deixam um relatorio final incoerente.

    Esta auditoria complementa a checagem de evidencias. Ela bloqueia textos
    que contradizem metricas estruturadas ja conhecidas pelo sistema e impede
    que blocos tecnicos internos sejam publicados como parte do relatorio final.
    """
    metrics = structured_metrics or {}
    issues: list[dict] = []

    known_agents = _first_positive_metric(
        metrics,
        (
            "profiles_count",
            "state_profiles_count",
            "active_agents_count",
            "total_agents",
            "agent_count",
            "reddit_profiles_count",
            "twitter_profiles_count",
        ),
    )
    known_rounds = _first_positive_metric(
        metrics,
        (
            "current_round",
            "rounds_count",
            "total_rounds",
            "max_rounds",
        ),
    )
    platforms = _known_platforms(metrics)

    seen_issue_ids: set[str] = set()

    def add_once(issue_id: str, message: str, line_no: int, line: str) -> None:
        if issue_id in seen_issue_ids:
            return
        seen_issue_ids.add(issue_id)
        issues.append(_line_issue(issue_id, message, line_no, line))

    lines = (report_md or "").splitlines()
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        normalized = _normalize_ascii_text(stripped)

        if re.match(r"^##\s+(qc\b|auditoria de evidencias\b)", normalized):
            add_once(
                "internal_audit_block_in_client_report",
                "Bloco interno de auditoria apareceu no relatorio final.",
                line_no,
                line,
            )

        if re.match(r"^\[[^\]]+\]\s*\|", stripped):
            add_once(
                "malformed_markdown_table",
                "Linha de tabela Markdown nao comeca com '|'.",
                line_no,
                line,
            )

        if known_agents and re.search(
            r"(nao\s+(ha|tem|haver|existem?)\s+agentes|sem\s+agentes\s+ativos|agentes?\s+desconhecid)",
            normalized,
        ):
            add_once(
                "contradicts_known_agents",
                f"O texto declara agentes ausentes/desconhecidos, mas o sistema conhece {known_agents} perfil(is).",
                line_no,
                line,
            )

        if known_rounds and re.search(
            r"(nao\s+tem.{0,80}rodadas|rodadas?.{0,80}(desconhecid|conhecid|confirmar)|"
            r"numero\s+de\s+rodadas.{0,80}(desconhecid|confirmar)|falta\s+confirmar.{0,80}rodadas)",
            normalized,
        ):
            add_once(
                "contradicts_known_rounds",
                f"O texto declara rodadas ausentes/desconhecidas, mas o sistema conhece {known_rounds} rodada(s).",
                line_no,
                line,
            )

        if platforms and re.search(
            r"(nao\s+tem.{0,80}plataformas|plataformas?.{0,80}(desconhecid|conhecid|confirmar)|"
            r"falta\s+confirmar.{0,80}plataformas)",
            normalized,
        ):
            add_once(
                "contradicts_known_platforms",
                "O texto declara plataformas ausentes/desconhecidas, mas o sistema tem plataformas simuladas.",
                line_no,
                line,
            )

    for idx, line in enumerate(lines):
        heading = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if not heading:
            continue
        title = re.sub(r"[*_`#]+", "", heading.group(1)).strip()
        next_line_no = None
        next_line = ""
        for cursor in range(idx + 1, len(lines)):
            if lines[cursor].strip():
                next_line_no = cursor + 1
                next_line = lines[cursor].strip()
                break
        if not next_line_no:
            continue
        bold = re.match(r"^\*\*(.+?)\*\*:?\s*$", next_line)
        if bold and _normalize_text_for_match(title) == _normalize_text_for_match(bold.group(1)):
            add_once(
                "duplicate_section_heading",
                "Titulo de secao repetido imediatamente dentro do corpo.",
                next_line_no,
                next_line,
            )

    blockquote_occurrences: dict[str, list[tuple[int, str]]] = {}
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped.startswith(">"):
            continue
        normalized_quote = _normalize_text_for_match(stripped.lstrip("> ").strip("\"'“”"))
        if len(normalized_quote.split()) < 6:
            continue
        blockquote_occurrences.setdefault(normalized_quote, []).append((line_no, line))

    for occurrences in blockquote_occurrences.values():
        if len(occurrences) >= 3:
            line_no, line = occurrences[2]
            add_once(
                "repeated_blockquote",
                "Bloco citado repetido varias vezes no relatorio final.",
                line_no,
                line,
            )
            break

    return {
        "passes_gate": not issues,
        "issues": issues,
        "issue_count": len(issues),
        "known_metrics": {
            "agents": known_agents,
            "rounds": known_rounds,
            "platforms": platforms,
        },
    }


def extract_direct_quotes(text: str, min_chars: int = 8) -> list[str]:
    """Extrai citacoes diretas entre aspas duplas/curvas.

    A Regra Zero INTEIA exige que uma aspa no relatorio exista no corpus de
    evidencia. Esta funcao ignora exemplos em blocos de codigo.
    """
    cleaned = _strip_code_fences(text)
    quotes: list[str] = []
    for match in _QUOTE_RE.finditer(cleaned):
        quote = next((group for group in match.groups() if group), "")
        quote = re.sub(r"\s+", " ", quote).strip()
        if len(quote) >= min_chars:
            quotes.append(quote)
    return quotes


def quote_supported_by_evidence(quote: str, evidence_texts: Iterable[str]) -> bool:
    """Retorna True somente se a citacao aparece no corpus de evidencia.

    O teste e deliberadamente conservador: citacao direta precisa existir como
    sequencia normalizada dentro do texto-base, logs de simulacao ou fatos
    extraidos. Parafrase deve ser marcada como inferencia/simulacao, sem aspas.
    """
    normalized_quote = _normalize_text_for_match(quote)
    if not normalized_quote:
        return False

    for evidence in evidence_texts or []:
        normalized_evidence = _normalize_text_for_match(evidence)
        if normalized_quote and normalized_quote in normalized_evidence:
            return True
    return False


def extract_numeric_claims(text: str) -> list[dict]:
    """Extrai numeros em linhas de conteudo para auditoria conservadora."""
    cleaned = _strip_generated_audit_blocks(_strip_code_fences(text))
    claims: list[dict] = []
    active_table_header = ""
    for line_no, line in enumerate(cleaned.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            active_table_header = ""
            continue
        if set(stripped.replace(" ", "")) <= {"|", "-", ":"} or _TABLE_SEPARATOR_RE.match(stripped):
            continue
        if stripped.startswith("#"):
            continue
        if (
            stripped.startswith("|")
            and _TABLE_HEADER_RE.search(stripped)
            and "**" not in stripped
            and not re.search(r"\d+(?:[.,]\d+)?\s*%", stripped)
        ):
            active_table_header = stripped
            continue
        if not stripped.startswith("|"):
            active_table_header = ""

        predictive_table_number = bool(
            active_table_header
            and stripped.startswith("|")
            and re.search(r"\b(?:probabilidade|cen[aá]rio|risco|confian[cç]a)\b", active_table_header, re.IGNORECASE)
        )
        requires_metric_support = bool(
            predictive_table_number
            or (
                "%" in stripped
                and _PREDICTIVE_NUMERIC_CONTEXT_RE.search(stripped)
            )
        )
        for match in _NUMBER_RE.finditer(stripped):
            raw = match.group(0).strip()
            if raw:
                claims.append({
                    "number": raw,
                    "line": line_no,
                    "context": stripped[:240],
                    "labeled_inference": bool(_INFERENCE_MARKER_RE.search(stripped)),
                    "requires_metric_support": requires_metric_support,
                })
    return claims


def number_supported_by_evidence(number: str, evidence_texts: Iterable[str]) -> bool:
    """Retorna True quando o numero literal aparece no corpus local."""
    normalized_number = re.sub(r"\s+", " ", (number or "").strip()).lower()
    if not normalized_number:
        return False

    compact_number = normalized_number.replace(" ", "")
    for evidence in evidence_texts or []:
        normalized_evidence = re.sub(r"\s+", " ", (evidence or "").lower())
        compact_evidence = normalized_evidence.replace(" ", "")
        if normalized_number in normalized_evidence or compact_number in compact_evidence:
            return True
    return False


def _flatten_numeric_metrics(metrics: Mapping[str, Any] | None, prefix: str = "") -> list[tuple[str, float]]:
    flattened: list[tuple[str, float]] = []
    if not isinstance(metrics, Mapping):
        return flattened

    for key, value in metrics.items():
        metric_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            flattened.extend(_flatten_numeric_metrics(value, metric_key))
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            flattened.append((metric_key, float(value)))
    return flattened


def _claim_number_value(number: str) -> float | None:
    match = re.match(r"\s*(\d+(?:[.,]\d+)?)", number or "")
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _metric_categories(metric_key: str) -> set[str]:
    normalized_key = _normalize_ascii_text(metric_key)
    categories: set[str] = set()
    for category, terms in _METRIC_CATEGORY_TERMS.items():
        if any(term in normalized_key for term in terms):
            categories.add(category)
    return categories


def _claim_categories(claim: Mapping[str, Any]) -> set[str]:
    normalized_context = _normalize_ascii_text(
        f"{claim.get('number', '')} {claim.get('context', '')}"
    )
    tokens = set(_WORD_RE.findall(normalized_context))
    categories: set[str] = set()
    for category, terms in _METRIC_CATEGORY_TERMS.items():
        if any(term in tokens for term in terms):
            categories.add(category)
    return categories


def number_supported_by_structured_metrics(
    claim: Mapping[str, Any],
    structured_metrics: Mapping[str, Any] | None,
) -> bool:
    """Valida numeros derivados de métricas estruturadas do próprio sistema."""
    claim_value = _claim_number_value(str(claim.get("number", "")))
    if claim_value is None:
        return False

    claim_categories = _claim_categories(claim)
    if not claim_categories:
        return False

    for metric_key, metric_value in _flatten_numeric_metrics(structured_metrics):
        if abs(metric_value - claim_value) > 1e-9:
            continue
        if claim_categories & _metric_categories(metric_key):
            return True
    return False


def audit_report_evidence(
    report_md: str,
    evidence_texts: Iterable[str],
    *,
    fail_on_unsupported_quotes: bool = True,
    fail_on_unsupported_numbers: bool = True,
    structured_metrics: Mapping[str, Any] | None = None,
) -> dict:
    """Audita se o relatorio usa citacoes sustentadas pelo sistema.

    Returns:
        {
            "passes_gate": bool,
            "quotes_total": int,
            "quotes_supported": int,
            "quotes_unsupported": int,
            "unsupported_quotes": [str],
            "fail_on_unsupported_quotes": bool,
        }
    """
    evidence_list = [text for text in (evidence_texts or []) if text]
    quotes = extract_direct_quotes(report_md)
    unsupported = [
        quote
        for quote in quotes
        if not quote_supported_by_evidence(quote, evidence_list)
    ]

    numeric_claims = extract_numeric_claims(report_md)
    structured_supported_numbers = [
        claim
        for claim in numeric_claims
        if number_supported_by_structured_metrics(claim, structured_metrics)
    ]
    unsupported_numbers = []
    for claim in numeric_claims:
        evidence_supported = number_supported_by_evidence(claim.get("number", ""), evidence_list)
        metric_supported = number_supported_by_structured_metrics(claim, structured_metrics)
        if claim.get("requires_metric_support"):
            if not evidence_supported and not metric_supported:
                unsupported_numbers.append(claim)
            continue
        if not claim.get("labeled_inference") and not evidence_supported and not metric_supported:
            unsupported_numbers.append(claim)
    supported_numbers = [
        claim
        for claim in numeric_claims
        if number_supported_by_evidence(claim.get("number", ""), evidence_list)
        or number_supported_by_structured_metrics(claim, structured_metrics)
    ]
    labeled_numbers = [claim for claim in numeric_claims if claim.get("labeled_inference")]

    passes_gate = not (
        (fail_on_unsupported_quotes and unsupported)
        or (fail_on_unsupported_numbers and unsupported_numbers)
    )

    return {
        "passes_gate": passes_gate,
        "quotes_total": len(quotes),
        "quotes_supported": len(quotes) - len(unsupported),
        "quotes_unsupported": len(unsupported),
        "unsupported_quotes": unsupported[:20],
        "fail_on_unsupported_quotes": fail_on_unsupported_quotes,
        "numbers_total": len(numeric_claims),
        "numbers_supported": len(supported_numbers),
        "numbers_supported_by_structured_metrics": len(structured_supported_numbers),
        "numbers_labeled_inference": len(labeled_numbers),
        "numbers_unsupported": len(unsupported_numbers),
        "unsupported_numbers": unsupported_numbers[:20],
        "fail_on_unsupported_numbers": fail_on_unsupported_numbers,
        "evidence_documents": len(evidence_list),
    }


def render_evidence_audit_block(audit: dict) -> str:
    """Gera bloco Markdown com o resultado da auditoria de evidencias."""
    status = "OK" if audit.get("passes_gate") else "BLOQUEADO"
    lines = [
        "",
        "## Auditoria de Evidencias",
        "",
        f"- **Gate de citacoes:** {status}",
        f"- **Citacoes diretas:** {audit.get('quotes_supported', 0)}/{audit.get('quotes_total', 0)} sustentadas pelo corpus",
        f"- **Numeros:** {audit.get('numbers_supported', 0)} sustentados, {audit.get('numbers_labeled_inference', 0)} rotulados como inferencia, {audit.get('numbers_unsupported', 0)} sem suporte",
        f"- **Documentos de evidencia auditados:** {audit.get('evidence_documents', 0)}",
    ]

    unsupported = audit.get("unsupported_quotes") or []
    if unsupported:
        lines.append("- **Citacoes sem suporte encontradas:**")
        for quote in unsupported[:5]:
            clipped = quote[:180] + ("..." if len(quote) > 180 else "")
            lines.append(f"  - {clipped}")

    unsupported_numbers = audit.get("unsupported_numbers") or []
    if unsupported_numbers:
        lines.append("- **Numeros sem suporte encontrados:**")
        for item in unsupported_numbers[:5]:
            lines.append(
                f"  - linha {item.get('line')}: {item.get('number')} em `{item.get('context')}`"
            )

    lines.append("")
    return "\n".join(lines)


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
