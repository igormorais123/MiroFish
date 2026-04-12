"""
Enriquecimento de materiais-base via Apify.

Fontes suportadas:
  - Google SERP (fatos web)
  - Instagram: perfis, posts recentes (com comments e mentions), tagged posts
  - YouTube: comentarios de videos

Funcionalidades:
  - auto_enrich_from_briefing(): extrai queries e handles do texto-base via LLM
  - build_enrichment_block(): monta bloco markdown completo
  - Cache em disco: evita reprocessar no force_regenerate
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
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


def _cache_path(project_id: str) -> Path:
    base = Path(os.environ.get("MIROFISH_DATA_DIR", "data"))
    return base / "projects" / project_id / "apify_cache.json"


def _cache_key(
    queries: list[str],
    actors: list[str],
    ig_posts_handles: list[str],
    ig_tagged_handles: list[str],
    yt_urls: list[str],
) -> str:
    raw = json.dumps(
        sorted(queries) + sorted(actors) + sorted(ig_posts_handles)
        + sorted(ig_tagged_handles) + sorted(yt_urls),
        ensure_ascii=False,
    )
    return hashlib.md5(raw.encode()).hexdigest()


class ApifyEnricher:
    """Coleta fatos web e perfis sociais via Apify para enriquecer contexto."""

    def __init__(self, client: ApifyClient | None = None):
        self.client = client or ApifyClient()

    # ==================== GOOGLE SERP ====================

    def fetch_case_facts(
        self,
        queries: list[str],
        results_per_query: int = 8,
    ) -> list[dict[str, Any]]:
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

    # ==================== INSTAGRAM PERFIS ====================

    def fetch_instagram_profiles(self, handles: list[str]) -> list[dict[str, Any]]:
        if not handles:
            return []
        logger.info(f"Apify Instagram perfis: {len(handles)}")
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

    # ==================== INSTAGRAM POSTS + COMMENTS ====================

    def fetch_instagram_posts(
        self,
        handles: list[str],
        posts_per_handle: int = 5,
    ) -> list[dict[str, Any]]:
        if not handles:
            return []
        logger.info(f"Apify Instagram posts: {len(handles)} handles x {posts_per_handle}")
        items = self.client.run_actor(
            "apify/instagram-post-scraper",
            {"username": handles, "resultsLimit": posts_per_handle},
            timeout=180,
        )
        posts: list[dict[str, Any]] = []
        for it in items:
            if it.get("error"):
                continue
            comments = []
            for cm in it.get("latestComments", []) or []:
                comments.append({
                    "author": cm.get("ownerUsername", ""),
                    "text": cm.get("text", ""),
                })
            posts.append({
                "handle": it.get("ownerFullName", ""),
                "url": it.get("url", ""),
                "caption": it.get("caption", ""),
                "likes": it.get("likesCount", 0),
                "comments_count": it.get("commentsCount", 0),
                "mentions": it.get("mentions", []),
                "hashtags": it.get("hashtags", []),
                "timestamp": it.get("timestamp", ""),
                "type": it.get("type", ""),
                "latest_comments": comments,
            })
        return posts

    # ==================== INSTAGRAM TAGGED POSTS ====================

    def fetch_instagram_tagged(
        self,
        handles: list[str],
        limit_per_handle: int = 5,
    ) -> list[dict[str, Any]]:
        if not handles:
            return []
        logger.info(f"Apify Instagram tagged: {len(handles)} handles")
        all_tagged: list[dict[str, Any]] = []
        for handle in handles:
            try:
                items = self.client.run_actor(
                    "instagram-scraper/instagram-tagged-posts-scraper",
                    {"username": handle, "resultsLimit": limit_per_handle},
                    timeout=120,
                )
                for it in items:
                    if it.get("error"):
                        continue
                    all_tagged.append({
                        "tagged_handle": handle,
                        "author": it.get("ownerUsername", it.get("ownerFullName", "")),
                        "caption": it.get("caption", ""),
                        "url": it.get("url", ""),
                        "likes": it.get("likesCount", 0),
                        "timestamp": it.get("timestamp", ""),
                    })
            except Exception as e:
                logger.warning(f"Tagged posts falhou para @{handle}: {e}")
        return all_tagged

    # ==================== YOUTUBE COMMENTS ====================

    def fetch_youtube_comments(
        self,
        video_urls: list[str],
        max_comments: int = 20,
    ) -> list[dict[str, Any]]:
        if not video_urls:
            return []
        logger.info(f"Apify YouTube comments: {len(video_urls)} videos x {max_comments}")
        start_urls = [{"url": u} for u in video_urls]
        items = self.client.run_actor(
            "streamers/youtube-comments-scraper",
            {"startUrls": start_urls, "maxComments": max_comments, "maxReplies": 0},
            timeout=180,
        )
        comments: list[dict[str, Any]] = []
        for it in items:
            comments.append({
                "video_url": it.get("pageUrl", ""),
                "video_title": it.get("title", ""),
                "author": it.get("author", ""),
                "text": it.get("comment", ""),
                "votes": it.get("voteCount", 0),
                "published": it.get("publishedTimeText", ""),
            })
        return comments

    # ==================== AUTO-ENRICH FROM BRIEFING ====================

    def extract_targets_from_text(self, text: str) -> dict[str, list[str]]:
        """Extrai queries, handles e URLs de video do texto-base sem LLM."""
        ig_pattern = r'@([a-zA-Z0-9_.]+)'
        ig_handles = list(set(re.findall(ig_pattern, text)))

        yt_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)'
        yt_urls = [f"https://www.youtube.com/watch?v={m}" for m in set(re.findall(yt_pattern, text))]

        name_pattern = r'(?:^|\n)\s*[-*]\s*(?:Ator|Actor|Candidato|Politico|Figura).*?:\s*(.+)'
        names = re.findall(name_pattern, text, re.IGNORECASE)

        queries: list[str] = []
        for name in names:
            name = name.strip().rstrip('.')
            if len(name) > 3:
                queries.append(name)

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line.lower() for kw in ['objetivo', 'simular', 'cenario', 'cenário', 'tema']):
                clean = re.sub(r'^[-*#\d.)\s]+', '', line).strip()
                if 10 < len(clean) < 120:
                    queries.append(clean)

        return {
            "queries": queries[:10],
            "ig_handles": ig_handles[:10],
            "yt_urls": yt_urls[:5],
        }

    # ==================== CACHE ====================

    def load_cache(self, project_id: str) -> dict[str, Any] | None:
        path = _cache_path(project_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                logger.info(f"Cache Apify carregado: {path}")
                return data
            except Exception:
                return None
        return None

    def save_cache(
        self,
        project_id: str,
        cache_key: str,
        block: str,
    ) -> None:
        path = _cache_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "key": cache_key,
            "enriched_at": datetime.utcnow().isoformat(),
            "block": block,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Cache Apify salvo: {path}")

    # ==================== BUILD BLOCK ====================

    def build_enrichment_block(
        self,
        queries: list[str] | None = None,
        actors_instagram: list[str] | None = None,
        ig_posts_handles: list[str] | None = None,
        ig_tagged_handles: list[str] | None = None,
        youtube_urls: list[str] | None = None,
        results_per_query: int = 8,
        posts_per_handle: int = 5,
        yt_max_comments: int = 20,
        project_id: str | None = None,
    ) -> str:
        queries = queries or []
        actors_instagram = actors_instagram or []
        ig_posts_handles = ig_posts_handles or []
        ig_tagged_handles = ig_tagged_handles or []
        youtube_urls = youtube_urls or []

        if not any([queries, actors_instagram, ig_posts_handles, ig_tagged_handles, youtube_urls]):
            return ""

        key = _cache_key(queries, actors_instagram, ig_posts_handles, ig_tagged_handles, youtube_urls)
        if project_id:
            cached = self.load_cache(project_id)
            if cached and cached.get("key") == key:
                logger.info("Usando bloco Apify do cache")
                return cached["block"]

        parts: list[str] = ["# Enriquecimento Apify", ""]

        # Google SERP
        facts = self.fetch_case_facts(queries, results_per_query)
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

        # Instagram perfis
        profiles = self.fetch_instagram_profiles(actors_instagram)
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

        # Instagram posts recentes + comments
        all_posts_handles = list(set(ig_posts_handles + actors_instagram))
        ig_posts = self.fetch_instagram_posts(all_posts_handles, posts_per_handle)
        if ig_posts:
            parts.append("## Posts recentes do Instagram")
            parts.append("")
            for p in ig_posts:
                ts = p["timestamp"][:10] if p["timestamp"] else ""
                parts.append(f"### {p['handle']} ({ts}) — {p['likes']} curtidas, {p['comments_count']} comentarios")
                if p["caption"]:
                    parts.append(f"Legenda: {p['caption'][:300]}")
                if p["hashtags"]:
                    parts.append(f"Hashtags: {' '.join('#' + h for h in p['hashtags'][:10])}")
                if p["mentions"]:
                    parts.append(f"Mencoes: {' '.join('@' + m for m in p['mentions'])}")
                if p["latest_comments"]:
                    parts.append("Comentarios:")
                    for cm in p["latest_comments"][:5]:
                        parts.append(f"  - @{cm['author']}: {cm['text'][:120]}")
                parts.append(f"URL: {p['url']}")
                parts.append("")

        # Instagram tagged posts
        tagged = self.fetch_instagram_tagged(ig_tagged_handles)
        if tagged:
            parts.append("## Posts em que os atores foram marcados")
            parts.append("")
            for t in tagged:
                ts = t["timestamp"][:10] if t["timestamp"] else ""
                parts.append(f"- @{t['tagged_handle']} marcado por @{t['author']} ({ts}): {t['caption'][:150]}")
                parts.append(f"  {t['url']}")
            parts.append("")

        # YouTube comments
        yt_comments = self.fetch_youtube_comments(youtube_urls, yt_max_comments)
        if yt_comments:
            parts.append("## Comentarios do YouTube")
            parts.append("")
            current_video = None
            for c in yt_comments:
                if c["video_url"] != current_video:
                    current_video = c["video_url"]
                    parts.append(f"### {c['video_title']}")
                    parts.append(f"URL: {current_video}")
                    parts.append("")
                vote_str = f" (+{c['votes']})" if c["votes"] else ""
                parts.append(f"- **{c['author']}**{vote_str}: {c['text'][:200]}")
            parts.append("")

        if len(parts) <= 2:
            return ""

        block = "\n".join(parts)

        if project_id:
            self.save_cache(project_id, key, block)

        return block

    def usage(self) -> dict[str, Any]:
        return self.client.usage()
