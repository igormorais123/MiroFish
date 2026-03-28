"""
Leitor de dados de simulacao direto dos arquivos actions.jsonl.
Substitui buscas no Graphiti quando este esta indisponivel.
"""

import os
import json
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.sim_data_reader')


class SimulationDataReader:
    """Le e analisa dados da simulacao direto dos arquivos JSONL."""

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
