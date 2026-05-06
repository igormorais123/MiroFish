"""Gate de atribuicao para textos de relatorio."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from app.utils.report_quality import extract_direct_quotes, quote_supported_by_evidence


SIMULATION_INFERENCE_MARKER = "[Inferencia da simulacao]"
OPERATIONAL_SUGGESTION_MARKER = "[Sugestao operacional]"

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)
_QUOTE_SPAN_RE = re.compile(
    r'"(?P<double>[^"\n]{8,})"|“(?P<curly_double>[^”\n]{8,})”|‘(?P<curly_single>[^’\n]{8,})’'
)
_MARKDOWN_FENCE_RE = re.compile(r"(```.*?```)", re.DOTALL)
_DEADLINE_RE = re.compile(
    r"\b\d+\s*(?:(?:,|\be\b|\bou\b|-|a)\s*\d+\s*)*"
    r"(?:dias?|semanas?|mes(?:es)?)\b",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    cleaned = "".join(char for char in decomposed if not unicodedata.combining(char))
    tokens = [token.lower() for token in _WORD_RE.findall(cleaned) if len(token) > 2]
    return " ".join(tokens)


def _normalize_text_for_deadline(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def _find_origin(quote: str, evidence_texts: list[str]) -> dict | None:
    normalized_quote = _normalize_text(quote)
    if not normalized_quote:
        return None

    for index, evidence in enumerate(evidence_texts):
        if normalized_quote in _normalize_text(evidence):
            return {
                "origin_index": index,
                "origin_text": evidence,
            }
    return None


def classify_direct_quotes(content: str, evidence_texts: Iterable[str]) -> list[dict]:
    """Classifica citacoes literais conforme presenca no corpus de evidencia."""
    evidence_list = [text for text in (evidence_texts or []) if text]
    classifications: list[dict] = []

    for quote in extract_direct_quotes(content or ""):
        supported = quote_supported_by_evidence(quote, evidence_list)
        item = {
            "quote": quote,
            "supported": supported,
        }
        if supported:
            origin = _find_origin(quote, evidence_list)
            if origin:
                item.update(origin)
        classifications.append(item)

    return classifications


def label_operational_deadlines(content: str) -> str:
    """Marca linhas com prazos operacionais antes da auditoria numerica."""
    labeled_lines: list[str] = []
    for line in (content or "").splitlines():
        if (
            _DEADLINE_RE.search(_normalize_text_for_deadline(line))
            and OPERATIONAL_SUGGESTION_MARKER not in line
        ):
            labeled_lines.append(f"{OPERATIONAL_SUGGESTION_MARKER} {line}")
        else:
            labeled_lines.append(line)
    return "\n".join(labeled_lines)


def normalize_report_attribution(content: str, evidence_texts: Iterable[str]) -> dict:
    """Remove aspas de sinteses sem suporte e preserva citacoes comprovadas."""
    evidence_list = [text for text in (evidence_texts or []) if text]
    converted_quotes_count = 0

    def replace_quote(match: re.Match[str]) -> str:
        nonlocal converted_quotes_count
        quote = next(group for group in match.groups() if group)
        quote = re.sub(r"\s+", " ", quote).strip()
        if quote_supported_by_evidence(quote, evidence_list):
            return match.group(0)

        converted_quotes_count += 1
        return f"{SIMULATION_INFERENCE_MARKER} {quote}"

    parts = _MARKDOWN_FENCE_RE.split(content or "")
    normalized_parts: list[str] = []
    for part in parts:
        if part.startswith("```"):
            normalized_parts.append(part)
            continue

        labeled_part = label_operational_deadlines(part)
        normalized_parts.append(_QUOTE_SPAN_RE.sub(replace_quote, labeled_part))

    normalized_content = "".join(normalized_parts)

    return {
        "content": normalized_content,
        "converted_quotes_count": converted_quotes_count,
        "quotes": classify_direct_quotes(normalized_content, evidence_list),
    }
