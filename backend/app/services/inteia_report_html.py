"""HTML wrapper for INTEIA-standard report deliverables."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any


INTEIA_HTML_RENDERER = "mirofish_inteia_report_html"
INTEIA_HTML_RENDERER_VERSION = "1.0"


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _meta_rows(metadata: dict[str, Any] | None) -> str:
    rows = []
    for key, value in (metadata or {}).items():
        rows.append(
            "<div class=\"meta-row\">"
            f"<span>{_escape(key)}</span>"
            f"<strong>{_escape(value)}</strong>"
            "</div>"
        )
    return "\n".join(rows)


def render_inteia_report_html(
    *,
    title: str,
    body_html: str,
    subtitle: str = "",
    metadata: dict[str, Any] | None = None,
    classification: str = "Interno",
    generated_at: str | None = None,
) -> str:
    """Wrap already-sanitized body HTML in the standard INTEIA report shell."""

    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    escaped_title = _escape(title)
    escaped_subtitle = _escape(subtitle)
    escaped_classification = _escape(classification)
    metadata = {
        "Classificacao": classification,
        "Gerado em": generated_at,
        **(metadata or {}),
    }

    return "\n".join([
        "<!doctype html>",
        '<html lang="pt-BR">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{escaped_title} | INTEIA</title>",
        "  <style>",
        "    :root { color-scheme: light; --ink:#111827; --muted:#4b5563; --line:#d9dee8; --panel:#f8fafc; --gold:#b7791f; --deep:#0f172a; --paper:#ffffff; }",
        "    * { box-sizing: border-box; }",
        "    body { margin:0; background:#eef2f7; color:var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; line-height:1.55; }",
        "    .page { max-width:1120px; margin:0 auto; background:var(--paper); min-height:100vh; box-shadow:0 24px 80px rgba(15,23,42,.16); }",
        "    header { padding:42px 48px 28px; background:linear-gradient(135deg,#111827,#1f2937); color:white; border-bottom:5px solid var(--gold); }",
        "    .kicker { display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:20px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:#fde68a; }",
        "    .badge { border:1px solid rgba(253,230,138,.55); padding:4px 8px; border-radius:4px; }",
        "    h1 { margin:0; font-size:clamp(30px,4vw,54px); line-height:1.04; letter-spacing:0; max-width:980px; }",
        "    .subtitle { margin:18px 0 0; max-width:880px; color:#d1d5db; font-size:18px; }",
        "    .meta-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; padding:22px 48px; background:#f8fafc; border-bottom:1px solid var(--line); }",
        "    .meta-row { padding:12px 14px; background:white; border:1px solid var(--line); border-radius:6px; }",
        "    .meta-row span { display:block; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }",
        "    .meta-row strong { display:block; margin-top:4px; font-size:15px; }",
        "    main { padding:36px 48px 54px; }",
        "    h1 + p, h2 + p, h3 + p { margin-top:8px; }",
        "    main h1 { color:var(--deep); font-size:32px; border-bottom:2px solid var(--gold); padding-bottom:10px; margin-top:32px; }",
        "    main h2 { color:var(--deep); font-size:24px; margin:34px 0 10px; border-left:5px solid var(--gold); padding-left:12px; }",
        "    main h3 { color:#1f2937; font-size:19px; margin:24px 0 8px; }",
        "    p { margin:0 0 14px; }",
        "    ul { margin:10px 0 18px; padding-left:22px; }",
        "    li { margin:7px 0; }",
        "    table { width:100%; border-collapse:collapse; margin:18px 0 26px; display:block; overflow-x:auto; }",
        "    th, td { border:1px solid var(--line); padding:10px 12px; text-align:left; vertical-align:top; }",
        "    th { background:#f3f4f6; color:#111827; }",
        "    pre { overflow:auto; padding:16px; background:#0f172a; color:#e5e7eb; border-radius:6px; }",
        "    code { background:#f3f4f6; padding:2px 4px; border-radius:4px; }",
        "    pre code { background:transparent; padding:0; }",
        "    a { color:#8a5a00; font-weight:700; }",
        "    .footer { padding:24px 48px 38px; border-top:1px solid var(--line); color:var(--muted); background:#f8fafc; }",
        "    .footer strong { color:var(--deep); }",
        "    @media (max-width:720px) { header, main, .meta-grid, .footer { padding-left:20px; padding-right:20px; } .subtitle { font-size:16px; } main h1 { font-size:26px; } }",
        "    @media print { body { background:white; } .page { box-shadow:none; } a { color:inherit; } }",
        "  </style>",
        "</head>",
        "<body>",
        "  <article class=\"page\">",
        "    <header>",
        "      <div class=\"kicker\"><span>RELATÓRIO DE INTELIGÊNCIA | INTEIA</span>"
        f"<span class=\"badge\">{escaped_classification}</span></div>",
        f"      <h1>{escaped_title}</h1>",
        f"      <p class=\"subtitle\">{escaped_subtitle}</p>" if escaped_subtitle else "",
        "    </header>",
        f"    <section class=\"meta-grid\">{_meta_rows(metadata)}</section>",
        f"    <main>{body_html}</main>",
        "    <footer class=\"footer\">",
        f"      <strong>Render:</strong> {INTEIA_HTML_RENDERER} v{INTEIA_HTML_RENDERER_VERSION}. ",
        "HTML estático, auditável e sem JavaScript inline.",
        "    </footer>",
        "  </article>",
        "</body>",
        "</html>",
        "",
    ])


def inteia_renderer_metadata(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return renderer metadata for manifests and validation reports."""

    return {
        "html_shell": INTEIA_HTML_RENDERER,
        "html_shell_version": INTEIA_HTML_RENDERER_VERSION,
        "inline_script": False,
        "standard": "inteia.report.html.v1",
        **(extra or {}),
    }
