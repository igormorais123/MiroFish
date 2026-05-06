"""Renderizacao segura de Markdown simples para superficies HTML."""

from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


RENDERER_NAME = "mirofish_safe_markdown"
RENDERER_VERSION = "1.0"


@dataclass(frozen=True)
class SafeMarkdownRenderResult:
    html: str
    metadata: dict
    blocked_patterns: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


_DANGEROUS_PATTERNS = {
    "script_tag": re.compile(r"<\s*/?\s*script\b", re.IGNORECASE),
    "event_handler": re.compile(r"\son[a-z]+\s*=", re.IGNORECASE),
    "javascript_url": re.compile(r"javascript\s*:", re.IGNORECASE),
    "dangerous_data_url": re.compile(r"data\s*:\s*(?!image/(?:png|gif|jpeg|webp);base64,)", re.IGNORECASE),
    "iframe_tag": re.compile(r"<\s*/?\s*iframe\b", re.IGNORECASE),
}


def detect_unsafe_markdown_patterns(markdown: str) -> list[str]:
    """Lista padroes perigosos encontrados antes do escape."""
    text = markdown or ""
    return [
        name
        for name, pattern in _DANGEROUS_PATTERNS.items()
        if pattern.search(text)
    ]


def _is_safe_url(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme:
        return True
    return parsed.scheme.lower() in {"http", "https", "mailto"}


def _render_inline(text: str) -> str:
    text = html.escape(text or "", quote=True)

    def replace_link(match: re.Match) -> str:
        label = match.group(1)
        url = html.unescape(match.group(2)).strip()
        if not _is_safe_url(url):
            return label
        safe_url = html.escape(url, quote=True)
        return f'<a href="{safe_url}" rel="noopener noreferrer" target="_blank">{label}</a>'

    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, text)
    return text


def render_safe_markdown(markdown: str) -> SafeMarkdownRenderResult:
    """Converte Markdown limitado em HTML escapado e com metadata auditavel."""
    blocked_patterns = detect_unsafe_markdown_patterns(markdown)
    lines = (markdown or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    html_lines: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            html_lines.append(f"<p>{'<br>'.join(paragraph)}</p>")
            paragraph.clear()

    def flush_code() -> None:
        html_lines.append(f"<pre><code>{html.escape(chr(10).join(code_lines), quote=True)}</code></pre>")
        code_lines.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                in_code = True
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not line.strip():
            flush_paragraph()
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            html_lines.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            continue

        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            html_lines.append(f"<ul><li>{_render_inline(bullet.group(1))}</li></ul>")
            continue

        paragraph.append(_render_inline(line))

    if in_code:
        flush_code()
    flush_paragraph()

    return SafeMarkdownRenderResult(
        html="\n".join(html_lines),
        blocked_patterns=blocked_patterns,
        metadata={
            "renderer": RENDERER_NAME,
            "version": RENDERER_VERSION,
            "raw_html_escaped": True,
            "allowed_url_schemes": ["http", "https", "mailto", "relative"],
            "unsafe_patterns_detected": blocked_patterns,
        },
    )
