"""
Enriquecimento de materiais-base via Apify.

Fontes: Google SERP, Instagram (perfis, posts, tagged), YouTube comments.
Modos: lean (economia), full (completo), batch (escala municipal).

Cache em disco evita reprocessamento. Budget guard impede estouro.
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

import os as _os

# 2026-04-18, Phase 7 Task: path Windows hardcoded vira env var
# Fallback para o path historico em dev Windows, mas VPS Linux usa COLMEIA_SCRIPTS_PATH
_COLMEIA_SCRIPTS = Path(_os.environ.get("COLMEIA_SCRIPTS_PATH", "C:/Users/IgorPC/Colmeia/scripts"))
if _COLMEIA_SCRIPTS.exists() and str(_COLMEIA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_COLMEIA_SCRIPTS))

try:
    from apify_client import ApifyClient  # type: ignore
except ImportError as exc:
    raise ImportError(
        f"apify_client.py nao encontrado em {_COLMEIA_SCRIPTS}. "
        "Defina COLMEIA_SCRIPTS_PATH ou instale apify_client como dependencia."
    ) from exc


PROFILES = {
    "lean": {
        "results_per_query": 5,
        "posts_per_handle": 3,
        "max_ig_profiles": 3,
        "max_ig_posts_handles": 2,
        "enable_tagged": False,
        "enable_youtube": False,
        "yt_max_comments": 10,
        "budget_limit_pct": 90,
    },
    "full": {
        "results_per_query": 8,
        "posts_per_handle": 5,
        "max_ig_profiles": 10,
        "max_ig_posts_handles": 10,
        "enable_tagged": True,
        "enable_youtube": True,
        "yt_max_comments": 20,
        "budget_limit_pct": 90,
    },
    "batch": {
        "results_per_query": 3,
        "posts_per_handle": 2,
        "max_ig_profiles": 2,
        "max_ig_posts_handles": 1,
        "enable_tagged": False,
        "enable_youtube": False,
        "yt_max_comments": 0,
        "budget_limit_pct": 95,
    },
}


def _cache_path(project_id: str) -> Path:
    base = Path(os.environ.get("MIROFISH_DATA_DIR", "data"))
    return base / "projects" / project_id / "apify_cache.json"


def _cache_key(*lists: list[str]) -> str:
    raw = json.dumps([sorted(l) for l in lists], ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()


class ApifyEnricher:

    def __init__(self, client: ApifyClient | None = None, profile: str = "full"):
        self.client = client or ApifyClient()
        self.cfg = PROFILES.get(profile, PROFILES["full"]).copy()
        self.profile_name = profile
        self._calls_made = 0
        self._budget_blocked = False

    # ==================== BUDGET GUARD ====================

    def check_budget(self) -> bool:
        """Retorna True se ainda pode gastar. Seta _budget_blocked se nao."""
        if self._budget_blocked:
            return False
        try:
            u = self.client.usage()
            pct = u.get("pct", 0)
            if pct >= self.cfg["budget_limit_pct"]:
                logger.warning(
                    f"Budget Apify bloqueado: {pct}% >= {self.cfg['budget_limit_pct']}% "
                    f"(US$ {u['usd_used']:.2f} / US$ {u['usd_limit']})"
                )
                self._budget_blocked = True
                return False
            return True
        except Exception as e:
            logger.warning(f"Falha ao checar budget: {e}")
            return True

    # ==================== GOOGLE SERP ====================

    def fetch_case_facts(
        self,
        queries: list[str],
        results_per_query: int | None = None,
    ) -> list[dict[str, Any]]:
        if not queries or not self.check_budget():
            return []
        rpq = results_per_query or self.cfg["results_per_query"]
        logger.info(f"Apify SERP [{self.profile_name}]: {len(queries)} queries x {rpq}")
        self._calls_made += 1
        items = self.client.google_search(queries, results_per_query=rpq)
        organic: list[dict[str, Any]] = []
        for page in items:
            for r in page.get("organicResults", []) or []:
                organic.append({
                    "query": page.get("searchQuery", {}).get("term", ""),
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                })
        return organic

    # ==================== INSTAGRAM PERFIS ====================

    def fetch_instagram_profiles(self, handles: list[str]) -> list[dict[str, Any]]:
        handles = handles[:self.cfg["max_ig_profiles"]]
        if not handles or not self.check_budget():
            return []
        logger.info(f"Apify IG perfis [{self.profile_name}]: {len(handles)}")
        self._calls_made += 1
        items = self.client.instagram_profiles(handles, limit=1)
        profiles: list[dict[str, Any]] = []
        for it in items:
            if it.get("error"):
                logger.warning(f"IG erro {it.get('username')}: {it.get('errorDescription','')[:80]}")
                continue
            profiles.append({
                "handle": it.get("username", ""),
                "full_name": it.get("fullName", ""),
                "biography": it.get("biography", ""),
                "followers": it.get("followersCount", 0),
                "following": it.get("followsCount", 0),
                "posts": it.get("postsCount", 0),
                "verified": it.get("verified", False),
                "category": it.get("businessCategoryName") or it.get("category", ""),
                "external_url": it.get("externalUrl", ""),
            })
        return profiles

    # ==================== INSTAGRAM POSTS + COMMENTS ====================

    def fetch_instagram_posts(
        self,
        handles: list[str],
        posts_per_handle: int | None = None,
    ) -> list[dict[str, Any]]:
        handles = handles[:self.cfg["max_ig_posts_handles"]]
        if not handles or not self.check_budget():
            return []
        pph = posts_per_handle or self.cfg["posts_per_handle"]
        logger.info(f"Apify IG posts [{self.profile_name}]: {len(handles)} x {pph}")
        self._calls_made += 1
        items = self.client.run_actor(
            "apify/instagram-post-scraper",
            {"username": handles, "resultsLimit": pph},
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
        if not handles or not self.cfg["enable_tagged"] or not self.check_budget():
            return []
        logger.info(f"Apify IG tagged [{self.profile_name}]: {len(handles)}")
        all_tagged: list[dict[str, Any]] = []
        for handle in handles[:2]:
            try:
                self._calls_made += 1
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
        max_comments: int | None = None,
    ) -> list[dict[str, Any]]:
        if not video_urls or not self.cfg["enable_youtube"] or not self.check_budget():
            return []
        mc = max_comments or self.cfg["yt_max_comments"]
        if mc <= 0:
            return []
        logger.info(f"Apify YT comments [{self.profile_name}]: {len(video_urls)} x {mc}")
        self._calls_made += 1
        start_urls = [{"url": u} for u in video_urls]
        items = self.client.run_actor(
            "streamers/youtube-comments-scraper",
            {"startUrls": start_urls, "maxComments": mc, "maxReplies": 0},
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

    # ==================== AUTO-EXTRACT FROM TEXT ====================

    def extract_targets_from_text(self, text: str) -> dict[str, list[str]]:
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
            "ig_handles": ig_handles[:self.cfg["max_ig_profiles"]],
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

    def save_cache(self, project_id: str, cache_key: str, block: str) -> None:
        path = _cache_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "key": cache_key,
            "enriched_at": datetime.utcnow().isoformat(),
            "block": block,
            "profile": self.profile_name,
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
        results_per_query: int | None = None,
        posts_per_handle: int | None = None,
        yt_max_comments: int | None = None,
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

        if not self.check_budget():
            logger.warning("Budget Apify esgotado, retornando vazio")
            return ""

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
                    cap_limit = 200 if self.profile_name == "batch" else 300
                    parts.append(f"Legenda: {p['caption'][:cap_limit]}")
                if p["hashtags"]:
                    parts.append(f"Hashtags: {' '.join('#' + h for h in p['hashtags'][:10])}")
                if p["mentions"]:
                    parts.append(f"Mencoes: {' '.join('@' + m for m in p['mentions'])}")
                if p["latest_comments"]:
                    max_cm = 3 if self.profile_name == "batch" else 5
                    parts.append("Comentarios:")
                    for cm in p["latest_comments"][:max_cm]:
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

    # ==================== BATCH MODE ====================

    def enrich_batch(
        self,
        municipalities: list[dict[str, Any]],
        project_id_prefix: str = "batch",
    ) -> list[dict[str, Any]]:
        """Enriquece multiplos municipios de forma otimizada.

        Cada municipio e um dict com:
            name: str, queries: list[str], ig_handles: list[str],
            yt_urls: list[str] (opcional)

        Agrupa handles de Instagram numa unica chamada ao actor.
        Retorna lista de {name, block, cached, cost_estimate}.
        """
        results: list[dict[str, Any]] = []
        if not municipalities:
            return results

        all_ig_handles: list[str] = []
        handle_to_muni: dict[str, list[str]] = {}
        for m in municipalities:
            for h in m.get("ig_handles", [])[:self.cfg["max_ig_profiles"]]:
                all_ig_handles.append(h)
                handle_to_muni.setdefault(h, []).append(m["name"])

        all_ig_handles = list(dict.fromkeys(all_ig_handles))

        logger.info(
            f"Batch [{self.profile_name}]: {len(municipalities)} municipios, "
            f"{len(all_ig_handles)} handles IG unicos"
        )

        # Coleta profiles em lote (1 chamada para todos)
        all_profiles_data: dict[str, dict] = {}
        if all_ig_handles and self.check_budget():
            profiles = self.fetch_instagram_profiles(all_ig_handles)
            for p in profiles:
                all_profiles_data[p["handle"]] = p

        # Coleta posts em lote (1 chamada para todos)
        all_posts_data: dict[str, list[dict]] = {}
        posts_handles = all_ig_handles[:self.cfg["max_ig_posts_handles"] * len(municipalities)]
        if posts_handles and self.check_budget():
            posts = self.fetch_instagram_posts(posts_handles)
            for p in posts:
                handle = p.get("handle", "")
                all_posts_data.setdefault(handle, []).append(p)

        # Coleta SERP em lote (queries agrupadas)
        all_queries: list[str] = []
        query_to_muni: dict[str, str] = {}
        for m in municipalities:
            for q in m.get("queries", []):
                all_queries.append(q)
                query_to_muni[q] = m["name"]

        all_facts: dict[str, list[dict]] = {}
        if all_queries and self.check_budget():
            batch_size = 20
            for i in range(0, len(all_queries), batch_size):
                batch = all_queries[i:i + batch_size]
                facts = self.fetch_case_facts(batch)
                for f in facts:
                    muni = query_to_muni.get(f["query"], "")
                    all_facts.setdefault(muni, []).append(f)

        # Monta blocos por municipio
        for m in municipalities:
            pid = f"{project_id_prefix}_{m['name'].lower().replace(' ', '_')}"

            cached = self.load_cache(pid)
            if cached:
                results.append({"name": m["name"], "block": cached["block"], "cached": True})
                continue

            parts: list[str] = [f"# Enriquecimento: {m['name']}", ""]

            muni_facts = all_facts.get(m["name"], [])
            if muni_facts:
                parts.append("## Fatos web")
                parts.append("")
                for f in muni_facts:
                    parts.append(f"- **{f['title']}** — {f['description']}")
                parts.append("")

            for h in m.get("ig_handles", [])[:self.cfg["max_ig_profiles"]]:
                p = all_profiles_data.get(h)
                if p:
                    verif = " (verificado)" if p["verified"] else ""
                    parts.append(f"## @{p['handle']} — {p['full_name']}{verif}")
                    parts.append(f"Seguidores: {p['followers']:,} | Bio: {p.get('biography','')[:150]}")
                    h_posts = all_posts_data.get(p["full_name"], [])
                    for post in h_posts[:self.cfg["posts_per_handle"]]:
                        if post["caption"]:
                            parts.append(f"- Post ({post['timestamp'][:10]}): {post['caption'][:200]}")
                            if post["latest_comments"]:
                                for cm in post["latest_comments"][:2]:
                                    parts.append(f"  > @{cm['author']}: {cm['text'][:100]}")
                    parts.append("")

            block = "\n".join(parts) if len(parts) > 2 else ""
            if block:
                self.save_cache(pid, "batch", block)
            results.append({"name": m["name"], "block": block, "cached": False})

        return results

    def estimate_batch_cost(self, n_municipalities: int, avg_handles: int = 2) -> dict[str, Any]:
        """Estima custo para N municipios no perfil atual."""
        c = self.cfg
        serp_calls = (n_municipalities + 19) // 20
        serp_cost = serp_calls * 0.01

        unique_handles = min(n_municipalities * avg_handles, n_municipalities * c["max_ig_profiles"])
        profile_calls = (unique_handles + 9) // 10
        profile_cost = profile_calls * 0.01

        posts_handles = min(unique_handles, n_municipalities * c["max_ig_posts_handles"])
        posts_calls = (posts_handles + 4) // 5
        posts_cost = posts_calls * 0.06

        tagged_cost = 0.0
        if c["enable_tagged"]:
            tagged_cost = min(unique_handles, n_municipalities * 2) * 0.06

        total = serp_cost + profile_cost + posts_cost + tagged_cost
        return {
            "n_municipalities": n_municipalities,
            "profile": self.profile_name,
            "serp_cost": serp_cost,
            "profile_cost": profile_cost,
            "posts_cost": posts_cost,
            "tagged_cost": tagged_cost,
            "total_usd": total,
            "serp_calls": serp_calls,
            "profile_calls": profile_calls,
            "posts_calls": posts_calls,
        }

    def usage(self) -> dict[str, Any]:
        return self.client.usage()
