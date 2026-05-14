"""
Leitor de dados de simulacao direto dos arquivos actions.jsonl.
Substitui buscas no Graphiti quando este esta indisponivel.
"""

import os
import json
import math
import re
import sqlite3
import unicodedata
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from ..config import Config
from ..utils.logger import get_logger
from .social_bootstrap import get_social_bootstrap_target, is_social_bootstrap_enabled

logger = get_logger('mirofish.sim_data_reader')

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)


def _normalize_words(text: str) -> list[str]:
    if not text:
        return []
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    return [tok.lower() for tok in _WORD_RE.findall(cleaned) if len(tok) > 1]


def _normalized_entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total <= 0 or len(counts) <= 1:
        return 0.0
    entropy = 0.0
    for value in counts.values():
        if value <= 0:
            continue
        p = value / total
        entropy -= p * math.log(p)
    return entropy / math.log(len(counts))


def _distinct_n(texts: list[str], n: int) -> float:
    ngrams: list[tuple[str, ...]] = []
    for text in texts:
        words = _normalize_words(text)
        if len(words) < n:
            continue
        ngrams.extend(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    if not ngrams:
        return 0.0
    return len(set(ngrams)) / len(ngrams)


class SimulationDataReader:
    """Le e analisa dados da simulacao direto dos arquivos JSONL."""

    TRACE_FILTERED_ACTIONS = {"sign_up", "refresh", "interview"}
    TRACE_INTERACTIVE_ACTIONS = {
        "like_post",
        "dislike_post",
        "repost",
        "quote_post",
        "follow",
        "mute",
        "create_comment",
        "like_comment",
        "dislike_comment",
    }

    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        self.sim_dir = os.path.join(Config.UPLOAD_FOLDER, 'simulations', simulation_id)
        self._actions_cache = None

    def _load_actions(self) -> List[Dict[str, Any]]:
        """Carrega todas as acoes de Twitter e Reddit."""
        if self._actions_cache is not None:
            return self._actions_cache

        actions = []
        for platform in ['twitter', 'reddit']:
            path = os.path.join(self.sim_dir, platform, 'actions.jsonl')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            action = json.loads(line)
                            action['platform'] = platform
                            actions.append(action)
                        except json.JSONDecodeError:
                            continue

        self._actions_cache = actions
        logger.info(f"Carregadas {len(actions)} acoes da simulacao {self.simulation_id}")
        return actions

    def get_agent_actions(self) -> List[Dict[str, Any]]:
        """Retorna apenas acoes de agentes (com agent_name)."""
        return [a for a in self._load_actions() if a.get('agent_name')]

    def get_context_summary(self) -> str:
        """Gera um resumo textual dos dados da simulacao para contexto LLM."""
        actions = self.get_agent_actions()
        if not actions:
            return "Nenhuma acao de agente encontrada na simulacao."

        # Estatisticas basicas
        agents = set(a.get('agent_name', '') for a in actions)
        action_types = Counter(a.get('action_type', '') for a in actions)
        platforms = Counter(a.get('platform', '') for a in actions)

        # Posts/conteudo por agente
        agent_posts = defaultdict(list)
        for a in actions:
            name = a.get('agent_name', '')
            content = a.get('action_args', {}).get('content', '')
            if content and name:
                agent_posts[name].append(content[:200])

        # Montar resumo
        parts = [
            f"## Dados da Simulacao {self.simulation_id}",
            f"- **Agentes ativos**: {len(agents)} ({', '.join(sorted(agents)[:15])}{'...' if len(agents) > 15 else ''})",
            f"- **Total de acoes**: {len(actions)}",
            f"- **Plataformas**: {dict(platforms)}",
            f"- **Tipos de acao**: {dict(action_types)}",
            "",
            "## Amostra de Conteudo por Agente (primeiras acoes)",
        ]

        for agent, posts in sorted(agent_posts.items())[:15]:
            parts.append(f"\n### {agent}")
            for post in posts[:3]:
                parts.append(f"> {post}")

        return "\n".join(parts)

    def search_actions(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca simples por keyword nas acoes."""
        query_lower = query.lower()
        results = []
        for a in self.get_agent_actions():
            content = a.get('action_args', {}).get('content', '')
            agent = a.get('agent_name', '')
            if query_lower in content.lower() or query_lower in agent.lower():
                results.append({
                    'agent': agent,
                    'action': a.get('action_type', ''),
                    'content': content[:300],
                    'round': a.get('round', 0),
                    'platform': a.get('platform', ''),
                })
                if len(results) >= limit:
                    break
        return results

    def get_facts_for_report(self, query: str = "", limit: int = 30) -> List[str]:
        """Retorna fatos formatados para uso no prompt do ReportAgent."""
        actions = self.get_agent_actions()
        facts = []

        if query:
            # Busca por palavras-chave individuais (mais flexivel)
            words = [w.lower() for w in query.split() if len(w) > 3]
            for a in actions:
                content = a.get('action_args', {}).get('content', '')
                agent = a.get('agent_name', '')
                text = f"{agent} {content}".lower()
                if any(w in text for w in words):
                    facts.append(
                        f"{agent} ({a.get('platform','')}, round {a.get('round',0)}): "
                        f"[{a.get('action_type','')}] {content[:200]}"
                    )
                    if len(facts) >= limit:
                        break

        # Se busca nao retornou resultados, retornar amostra geral
        if not facts:
            for a in actions[:limit]:
                content = a.get('action_args', {}).get('content', '')
                if content:
                    facts.append(
                        f"{a.get('agent_name','')} ({a.get('platform','')}, "
                        f"round {a.get('round',0)}): [{a.get('action_type','')}] {content[:200]}"
                    )

        return facts

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatisticas da simulacao."""
        actions = self.get_agent_actions()
        agents = set(a.get('agent_name', '') for a in actions)

        return {
            'total_nodes': len(agents),
            'total_edges': len(actions),
            'entity_types': {
                'Agent': len(agents),
                'Action': len(actions),
            },
        }

    def get_diversity_metrics(self) -> Dict[str, Any]:
        """Mede diversidade comportamental e semantica da simulacao.

        Inspirado no estudo de Lan et al. (Scientific Reports, 2026): usa
        entropia normalizada para distribuicao de comportamento/agentes e
        Distinct-1/2 para repeticao lexical dos textos gerados.
        """
        actions = self.get_agent_actions()
        action_types = Counter(a.get('action_type', '') for a in actions if a.get('action_type'))
        agents = Counter(a.get('agent_name', '') for a in actions if a.get('agent_name'))
        platforms = Counter(a.get('platform', '') for a in actions if a.get('platform'))

        texts: list[str] = []
        for action in actions:
            content = action.get('action_args', {}).get('content', '')
            if content:
                texts.append(content)

        words_per_text = [len(_normalize_words(text)) for text in texts]
        avg_text_length = sum(words_per_text) / len(words_per_text) if words_per_text else 0.0

        role_counts = self._get_entity_type_action_counts(actions)
        oasis_trace = self.get_oasis_trace_metrics()

        return {
            "total_actions": len(actions),
            "generated_texts_count": len(texts),
            "active_agents_count": len(agents),
            "action_type_counts": dict(action_types),
            "action_type_entropy_norm": round(_normalized_entropy(action_types), 4),
            "agent_activity_entropy_norm": round(_normalized_entropy(agents), 4),
            "platform_counts": dict(platforms),
            "distinct_1": round(_distinct_n(texts, 1), 4),
            "distinct_2": round(_distinct_n(texts, 2), 4),
            "avg_text_length_words": round(avg_text_length, 2),
            "entity_type_action_counts": dict(role_counts),
            "entity_type_coverage": len(role_counts),
            "oasis_trace": oasis_trace,
        }

    def get_oasis_trace_metrics(self) -> Dict[str, Any]:
        """Resume a tabela trace dos bancos OASIS por plataforma.

        O actions.jsonl e o contrato de auditoria do sistema; a tabela trace e
        usada como contraprova para detectar duplicidade ou ausencia de
        comportamento social real.
        """
        platform_counts: dict[str, dict[str, int]] = {}
        total_counts: Counter = Counter()
        db_files_found = 0

        for platform in ["twitter", "reddit"]:
            db_path = os.path.join(self.sim_dir, f"{platform}_simulation.db")
            counts = Counter()
            if os.path.exists(db_path):
                db_files_found += 1
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT action, COUNT(*) FROM trace GROUP BY action")
                    counts.update({str(action): int(count) for action, count in cursor.fetchall() if action})
                    conn.close()
                except Exception as exc:
                    logger.warning(f"Falha ao ler trace OASIS {db_path}: {exc}")
            platform_counts[platform] = dict(counts)
            total_counts.update(counts)

        behavioral_counts = Counter({
            action: count
            for action, count in total_counts.items()
            if action not in self.TRACE_FILTERED_ACTIONS
        })
        interactive_total = sum(
            count for action, count in total_counts.items()
            if action in self.TRACE_INTERACTIVE_ACTIONS
        )
        simulation_config = self._load_simulation_config()
        configured_initial_posts = self._get_initial_posts_count(simulation_config)
        expected_initial_posts = configured_initial_posts * db_files_found
        dynamic_create_posts = max(0, total_counts.get("create_post", 0) - expected_initial_posts)
        bootstrap_interactive = self._estimate_bootstrap_interactive_actions(
            simulation_config,
            platform_counts,
        )
        emergent_interactive = max(0, interactive_total - bootstrap_interactive)

        return {
            "db_files_found": db_files_found,
            "platform_action_counts": platform_counts,
            "total_action_counts": dict(total_counts),
            "behavioral_action_counts": dict(behavioral_counts),
            "behavioral_entropy_norm": round(_normalized_entropy(behavioral_counts), 4),
            "configured_initial_posts": configured_initial_posts,
            "expected_initial_posts_total": expected_initial_posts,
            "dynamic_create_posts_estimate": dynamic_create_posts,
            "interactive_actions_total": interactive_total,
            "bootstrap_interactive_actions_estimate": bootstrap_interactive,
            "emergent_interactive_actions_estimate": emergent_interactive,
        }

    def _load_simulation_config(self) -> Dict[str, Any]:
        config_path = os.path.join(self.sim_dir, "simulation_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config if isinstance(config, dict) else {}
        except Exception:
            return {}

    def _get_initial_posts_count(self, config: Optional[Dict[str, Any]] = None) -> int:
        config = config if isinstance(config, dict) else self._load_simulation_config()
        try:
            return len((config.get("event_config") or {}).get("initial_posts", []) or [])
        except Exception:
            return 0

    def _estimate_bootstrap_interactive_actions(
        self,
        config: Dict[str, Any],
        platform_counts: Dict[str, Dict[str, int]],
    ) -> int:
        """Estima o pulso induzido para separar lastro emergente de bootstrap."""
        if not config or not is_social_bootstrap_enabled(config):
            return 0

        seed_post_count = self._get_initial_posts_count(config)
        candidate_count = len((config.get("agent_configs") or []) or [])
        if seed_post_count <= 0 or candidate_count <= 0:
            return 0

        total = 0
        for platform, counts in platform_counts.items():
            if not counts:
                continue
            target = get_social_bootstrap_target(
                config,
                platform,
                seed_post_count=seed_post_count,
                candidate_count=candidate_count,
            )
            observed_interactive = sum(
                int(count)
                for action, count in (counts or {}).items()
                if action in self.TRACE_INTERACTIVE_ACTIONS
            )
            total += min(target, observed_interactive)
        return total

    def _get_entity_type_action_counts(self, actions: List[Dict[str, Any]]) -> Counter:
        """Conta acoes por entity_type usando simulation_config.json quando existir."""
        config_path = os.path.join(self.sim_dir, "simulation_config.json")
        id_to_type: dict[int, str] = {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            for item in config.get("agent_configs", []) or []:
                agent_id = item.get("agent_id")
                entity_type = item.get("entity_type") or "unknown"
                if agent_id is not None:
                    id_to_type[int(agent_id)] = str(entity_type)
        except Exception:
            return Counter()

        counts = Counter()
        for action in actions:
            agent_id = action.get("agent_id")
            if agent_id is None:
                continue
            entity_type = id_to_type.get(int(agent_id), "unknown")
            counts[entity_type] += 1
        return counts
