"""
Enriquecimento de materiais-base via Apify.

Objetivo: aumentar fidelidade da simulacao trazendo fatos web (SERPs) e
perfis sociais reais dos atores antes da construcao do grafo. Nao acelera
nada — apenas torna o contexto mais rico.

Uso tipico (CLI): backend/scripts/enrich_project.py
Uso programatico:

    from app.services.apify_enricher import ApifyEnricher
    e = ApifyEnricher()
    bloco = e.build_enrichment_block(
        queries=["reforma tributaria PEC 45", "Neto 2026 Bahia"],
        actors_instagram=["acmneto", "brunoreisba"],
    )
    # bloco e um texto markdown pronto para anexar ao documento-base
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger

logger = get_logger("mirofish.apify_enricher")

_COLMEIA_SCRIPTS = Path(r"C:/Users/IgorPC/Colmeia/scripts")
if _COLMEIA_SCRIPTS.exists() and str(_COLMEIA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_COLMEIA_SCRIPTS))

try:
    from apify_client import ApifyClient  # type: ignore
except ImportError as exc:
    raise ImportError(
        "apify_client.py nao encontrado. Esperado em "
        "C:/Users/IgorPC/Colmeia/scripts/apify_client.py. "
        "Ajuste PYTHONPATH ou copie o helper para o backend."
    ) from exc


class ApifyEnricher:
    """Coleta fatos web e perfis sociais via Apify para enriquecer contexto."""

    def __init__(self, client: ApifyClient | None = None):
        self.client = client or ApifyClient()

    def fetch_case_facts(
        self,
        queries: list[str],
        results_per_query: int = 8,
    ) -> list[dict[str, Any]]:
        """Retorna itens de SERP (title, url, description) para cada query."""
        if not queries:
            return []
        logger.info(f"Apify SERP: {len(queries)} queries x {results_per_query}")
        items = self.client.google_search(queries, results_per_query=results_per_query)
        organic: list[dict[str, Any]] = []
        for page in items:
            for r in page.get("organicResults", []) or []:
                organic.append(
                    {
                        "query": page.get("searchQuery", {}).get("term", ""),
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "description": r.get("description", ""),
                    }
                )
        return organic

    def fetch_instagram_profiles(self, handles: list[str]) -> list[dict[str, Any]]:
        """Retorna dados de perfil Instagram (nome, bio, seguidores, categoria)."""
        if not handles:
            return []
        logger.info(f"Apify Instagram: {len(handles)} perfis")
        items = self.client.instagram_profiles(handles, limit=1)
        profiles: list[dict[str, Any]] = []
        for it in items:
            if it.get("error"):
                logger.warning(f"Apify erro {it.get('username')}: {it.get('errorDescription','')[:80]}")
                continue
            profiles.append(
                {
                    "handle": it.get("username", ""),
                    "full_name": it.get("fullName", ""),
                    "biography": it.get("biography", ""),
                    "followers": it.get("followersCount", 0),
                    "following": it.get("followsCount", 0),
                    "posts": it.get("postsCount", 0),
                    "verified": it.get("verified", False),
                    "category": it.get("businessCategoryName") or it.get("category", ""),
                    "external_url": it.get("externalUrl", ""),
                }
            )
        return profiles

    def build_enrichment_block(
        self,
        queries: list[str] | None = None,
        actors_instagram: list[str] | None = None,
        results_per_query: int = 8,
    ) -> str:
        """Monta um bloco markdown pronto para anexar ao documento-base."""
        parts: list[str] = ["# Enriquecimento Apify", ""]

        facts = self.fetch_case_facts(queries or [], results_per_query)
        if facts:
            parts.append("## Fatos web (Google SERP)")
            parts.append("")
            current_q = None
            for f in facts:
                if f["query"] != current_q:
                    current_q = f["query"]
                    parts.append(f"### Consulta: {current_q}")
                    parts.append("")
                parts.append(f"- **{f['title']}** — {f['description']}")
                parts.append(f"  Fonte: {f['url']}")
            parts.append("")

        profiles = self.fetch_instagram_profiles(actors_instagram or [])
        if profiles:
            parts.append("## Perfis Instagram dos atores")
            parts.append("")
            for p in profiles:
                verif = " (verificado)" if p["verified"] else ""
                parts.append(f"### @{p['handle']} — {p['full_name']}{verif}")
                if p["category"]:
                    parts.append(f"Categoria: {p['category']}")
                parts.append(
                    f"Seguidores: {p['followers']:,} | Seguindo: {p['following']:,} | Posts: {p['posts']:,}"
                )
                if p["biography"]:
                    parts.append(f"Bio: {p['biography']}")
                if p["external_url"]:
                    parts.append(f"Link: {p['external_url']}")
                parts.append("")

        if len(parts) <= 2:
            return ""
        return "\n".join(parts)

    def usage(self) -> dict[str, Any]:
        return self.client.usage()
