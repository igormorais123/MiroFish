"""
Servicos de busca e leitura do grafo usados pelo Report Agent.

Ferramentas centrais:
1. InsightForge: busca profunda com decomposicao em subperguntas
2. PanoramaSearch: visao ampla, incluindo historico e itens expirados
3. QuickSearch: busca leve e direta

Agora usa a API REST do Graphiti Server em vez do SDK Zep Cloud.
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from ..utils.graphiti_client import GraphitiClient

logger = get_logger('mirofish.zep_tools')


@dataclass
class SearchResult:
    """Resultado de busca."""
    facts: List[str]
    edges: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]
    query: str
    total_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts": self.facts,
            "edges": self.edges,
            "nodes": self.nodes,
            "query": self.query,
            "total_count": self.total_count
        }

    def to_text(self) -> str:
        """Converte para texto estruturado para consumo do LLM."""
        text_parts = [f"Busca: {self.query}", f"Foram encontradas {self.total_count} informacoes relevantes"]

        if self.facts:
            text_parts.append("\n### Fatos relacionados:")
            for i, fact in enumerate(self.facts, 1):
                text_parts.append(f"{i}. {fact}")

        return "\n".join(text_parts)


@dataclass
class NodeInfo:
    """Informacoes de um no."""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes
        }

    def to_text(self) -> str:
        """Converte para texto."""
        entity_type = next((l for l in self.labels if l not in ["Entity", "Node"]), "Tipo nao informado")
        return f"Entidade: {self.name} (tipo: {entity_type})\nResumo: {self.summary}"


@dataclass
class EdgeInfo:
    """Informacoes de uma relacao."""
    uuid: str
    name: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    # Metadados temporais
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "fact": self.fact,
            "source_node_uuid": self.source_node_uuid,
            "target_node_uuid": self.target_node_uuid,
            "source_node_name": self.source_node_name,
            "target_node_name": self.target_node_name,
            "created_at": self.created_at,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "expired_at": self.expired_at
        }

    def to_text(self, include_temporal: bool = False) -> str:
        """Converte para texto."""
        source = self.source_node_name or self.source_node_uuid[:8]
        target = self.target_node_name or self.target_node_uuid[:8]
        base_text = f"Relacao: {source} --[{self.name}]--> {target}\nFato: {self.fact}"

        if include_temporal:
            valid_at = self.valid_at or "desconhecido"
            invalid_at = self.invalid_at or "atual"
            base_text += f"\nVigencia: {valid_at} - {invalid_at}"
            if self.expired_at:
                base_text += f" (expirado em: {self.expired_at})"

        return base_text

    @property
    def is_expired(self) -> bool:
        """Indica se a relacao expirou."""
        return self.expired_at is not None

    @property
    def is_invalid(self) -> bool:
        """Indica se a relacao foi invalidada."""
        return self.invalid_at is not None


@dataclass
class InsightForgeResult:
    """Resultado do InsightForge, com subperguntas e sintese analitica."""
    query: str
    simulation_requirement: str
    sub_queries: List[str]

    # Resultados por dimensao
    semantic_facts: List[str] = field(default_factory=list)
    entity_insights: List[Dict[str, Any]] = field(default_factory=list)
    relationship_chains: List[str] = field(default_factory=list)

    # Estatisticas
    total_facts: int = 0
    total_entities: int = 0
    total_relationships: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "simulation_requirement": self.simulation_requirement,
            "sub_queries": self.sub_queries,
            "semantic_facts": self.semantic_facts,
            "entity_insights": self.entity_insights,
            "relationship_chains": self.relationship_chains,
            "total_facts": self.total_facts,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships
        }

    def to_text(self) -> str:
        """Converte para texto estruturado e detalhado."""
        text_parts = [
            f"## Analise profunda de previsao",
            f"Pergunta de analise: {self.query}",
            f"Cenario de previsao: {self.simulation_requirement}",
            f"\n### Estatisticas da previsao",
            f"- Fatos relevantes: {self.total_facts}",
            f"- Entidades envolvidas: {self.total_entities}",
            f"- Cadeias relacionais: {self.total_relationships}"
        ]

        if self.sub_queries:
            text_parts.append(f"\n### Subperguntas analisadas")
            for i, sq in enumerate(self.sub_queries, 1):
                text_parts.append(f"{i}. {sq}")

        if self.semantic_facts:
            text_parts.append(f"\n### Fatos-chave")
            for i, fact in enumerate(self.semantic_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")

        if self.entity_insights:
            text_parts.append(f"\n### Entidades centrais")
            for entity in self.entity_insights:
                text_parts.append(f"- **{entity.get('name', 'Nao informado')}** ({entity.get('type', 'Entidade')})")
                if entity.get('summary'):
                    text_parts.append(f"  Resumo: \"{entity.get('summary')}\"")
                if entity.get('related_facts'):
                    text_parts.append(f"  Fatos relacionados: {len(entity.get('related_facts', []))}")

        if self.relationship_chains:
            text_parts.append(f"\n### Cadeias relacionais")
            for chain in self.relationship_chains:
                text_parts.append(f"- {chain}")

        return "\n".join(text_parts)


@dataclass
class PanoramaResult:
    """Resultado de busca panoramica, incluindo historico e itens expirados."""
    query: str

    # Todos os nos
    all_nodes: List[NodeInfo] = field(default_factory=list)
    # Todas as relacoes, inclusive expiradas
    all_edges: List[EdgeInfo] = field(default_factory=list)
    # Fatos atualmente validos
    active_facts: List[str] = field(default_factory=list)
    # Fatos expirados ou invalidados
    historical_facts: List[str] = field(default_factory=list)

    # Estatisticas
    total_nodes: int = 0
    total_edges: int = 0
    active_count: int = 0
    historical_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "all_nodes": [n.to_dict() for n in self.all_nodes],
            "all_edges": [e.to_dict() for e in self.all_edges],
            "active_facts": self.active_facts,
            "historical_facts": self.historical_facts,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "active_count": self.active_count,
            "historical_count": self.historical_count
        }

    def to_text(self) -> str:
        """Converte para texto sem truncamento."""
        text_parts = [
            f"## Resultado panoramico",
            f"Consulta: {self.query}",
            f"\n### Estatisticas",
            f"- Total de nos: {self.total_nodes}",
            f"- Total de relacoes: {self.total_edges}",
            f"- Fatos atuais: {self.active_count}",
            f"- Fatos historicos/expirados: {self.historical_count}"
        ]

        if self.active_facts:
            text_parts.append(f"\n### Fatos atuais")
            for i, fact in enumerate(self.active_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")

        if self.historical_facts:
            text_parts.append(f"\n### Fatos historicos ou expirados")
            for i, fact in enumerate(self.historical_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")

        if self.all_nodes:
            text_parts.append(f"\n### Entidades envolvidas")
            for node in self.all_nodes:
                entity_type = next((l for l in node.labels if l not in ["Entity", "Node"]), "Entidade")
                text_parts.append(f"- **{node.name}** ({entity_type})")

        return "\n".join(text_parts)


@dataclass
class AgentInterview:
    """Resultado de entrevista de um agente."""
    agent_name: str
    agent_role: str
    agent_bio: str
    question: str
    response: str
    key_quotes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "agent_bio": self.agent_bio,
            "question": self.question,
            "response": self.response,
            "key_quotes": self.key_quotes
        }

    def to_text(self) -> str:
        text = f"**{self.agent_name}** ({self.agent_role})\n"
        text += f"_Bio: {self.agent_bio}_\n\n"
        text += f"**Q:** {self.question}\n\n"
        text += f"**A:** {self.response}\n"
        if self.key_quotes:
            text += "\n**Citacoes-chave:**\n"
            for quote in self.key_quotes:
                clean_quote = quote.replace('\u201c', '').replace('\u201d', '').replace('"', '')
                clean_quote = clean_quote.replace('\u300c', '').replace('\u300d', '')
                clean_quote = clean_quote.strip()
                while clean_quote and clean_quote[0] in '，,；;：:、。！？\n\r\t ':
                    clean_quote = clean_quote[1:]
                skip = False
                for d in '123456789':
                    if f'\u95ee\u9898{d}' in clean_quote:
                        skip = True
                        break
                if skip:
                    continue
                if len(clean_quote) > 150:
                    dot_pos = clean_quote.find('\u3002', 80)
                    if dot_pos > 0:
                        clean_quote = clean_quote[:dot_pos + 1]
                    else:
                        clean_quote = clean_quote[:147] + "..."
                if clean_quote and len(clean_quote) >= 10:
                    text += f'> "{clean_quote}"\n'
        return text


@dataclass
class InterviewResult:
    """Resultado consolidado das entrevistas."""
    interview_topic: str
    interview_questions: List[str]

    selected_agents: List[Dict[str, Any]] = field(default_factory=list)
    interviews: List[AgentInterview] = field(default_factory=list)

    selection_reasoning: str = ""
    summary: str = ""

    total_agents: int = 0
    interviewed_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interview_topic": self.interview_topic,
            "interview_questions": self.interview_questions,
            "selected_agents": self.selected_agents,
            "interviews": [i.to_dict() for i in self.interviews],
            "selection_reasoning": self.selection_reasoning,
            "summary": self.summary,
            "total_agents": self.total_agents,
            "interviewed_count": self.interviewed_count
        }

    def to_text(self) -> str:
        """Converte o resultado em texto detalhado para o LLM e o relatorio."""
        text_parts = [
            "## Relatorio de entrevistas aprofundadas",
            f"**Tema da entrevista:** {self.interview_topic}",
            f"**Pessoas entrevistadas:** {self.interviewed_count} / {self.total_agents} agentes simulados",
            "\n### Motivo da selecao dos entrevistados",
            self.selection_reasoning or "(selecao automatica)",
            "\n---",
            "\n### Registro das entrevistas",
        ]

        if self.interviews:
            for i, interview in enumerate(self.interviews, 1):
                text_parts.append(f"\n#### Entrevista #{i}: {interview.agent_name}")
                text_parts.append(interview.to_text())
                text_parts.append("\n---")
        else:
            text_parts.append("(sem entrevistas registradas)\n\n---")

        text_parts.append("\n### Resumo e pontos centrais")
        text_parts.append(self.summary or "(sem resumo)")

        return "\n".join(text_parts)


class ZepToolsService:
    """
    Servico de leitura, consulta e analise sobre o grafo via Graphiti Server.

    Ferramentas principais:
    - `insight_forge`: busca profunda com subperguntas
    - `panorama_search`: visao ampla com historico
    - `quick_search`: busca leve e direta
    - `interview_agents`: entrevistas com agentes simulados
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    def __init__(self, api_key: Optional[str] = None, llm_client: Optional[LLMClient] = None):
        """Inicializa o servico.

        Args:
            api_key: Mantido na assinatura para compatibilidade.
            llm_client: Cliente LLM opcional.
        """
        self.client = GraphitiClient()
        self._llm_client = llm_client
        logger.info("ZepToolsService inicializado (backend: Graphiti Server)")

    @property
    def llm(self) -> LLMClient:
        """Inicializa o cliente LLM apenas quando necessario."""
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    def _call_with_retry(self, func, operation_name: str, max_retries: int = None):
        """Executa uma chamada com retry exponencial simples."""
        max_retries = max_retries or self.MAX_RETRIES
        last_exception = None
        delay = self.RETRY_DELAY

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Graphiti {operation_name} falhou na tentativa {attempt + 1}: {str(e)[:100]}. "
                        f"Novo retry em {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Graphiti {operation_name} falhou apos {max_retries} tentativas: {str(e)}")

        raise last_exception

    def _parse_facts(self, raw_facts: list) -> tuple:
        """Extrai fatos, arestas e nos a partir da resposta do Graphiti.

        Returns:
            (facts_text, edges_list, nodes_list)
        """
        facts = []
        edges = []
        seen_entities = set()
        nodes = []

        for fact in raw_facts:
            if isinstance(fact, dict):
                fact_text = fact.get("fact", "")
                fact_name = fact.get("name", "")
                if fact_text:
                    facts.append(fact_text)
                edges.append({
                    "uuid": fact.get("uuid", ""),
                    "name": fact_name,
                    "fact": fact_text,
                    "source_node_uuid": "",
                    "target_node_uuid": "",
                    "valid_at": fact.get("valid_at"),
                    "invalid_at": fact.get("invalid_at"),
                    "created_at": fact.get("created_at"),
                    "expired_at": fact.get("expired_at"),
                })
                if fact_name and fact_name not in seen_entities:
                    seen_entities.add(fact_name)
                    nodes.append({
                        "uuid": fact.get("uuid", ""),
                        "name": fact_name,
                        "labels": ["Entity"],
                        "summary": fact_text,
                    })
            elif isinstance(fact, str):
                facts.append(fact)

        return facts, edges, nodes

    def search_graph(
        self,
        graph_id: str,
        query: str,
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        Faz busca semantica no grafo via Graphiti POST /search.
        """
        logger.info(f"Busca no grafo: graph_id={graph_id}, query={query[:50]}...")

        try:
            search_result = self._call_with_retry(
                func=lambda: self.client.search(
                    group_ids=[graph_id],
                    query=query,
                    max_facts=limit,
                ),
                operation_name=f"busca no grafo {graph_id}"
            )

            raw_facts = search_result.get("facts", [])
            facts, edges, nodes = self._parse_facts(raw_facts)

            logger.info(f"Busca concluida: {len(facts)} fatos relacionados encontrados")

            return SearchResult(
                facts=facts,
                edges=edges,
                nodes=nodes,
                query=query,
                total_count=len(facts)
            )

        except Exception as e:
            logger.warning(f"Falha na busca Graphiti; tentando dados locais: {str(e)}")

            # Fallback: buscar nos dados locais da simulacao
            try:
                from .simulation_data_reader import SimulationDataReader
                sim_id = self._find_simulation_for_graph(graph_id)
                logger.info(f"Fallback: graph_id={graph_id} -> sim_id={sim_id}")
                if sim_id:
                    reader = SimulationDataReader(sim_id)
                    local_facts = reader.get_facts_for_report(query=query, limit=limit)
                    if local_facts:
                        logger.info(f"Fallback local: {len(local_facts)} fatos encontrados")
                        return SearchResult(
                            facts=local_facts,
                            edges=[],
                            nodes=[],
                            query=query,
                            total_count=len(local_facts)
                        )
            except Exception as fallback_err:
                logger.warning(f"Fallback local tambem falhou: {fallback_err}")

            return SearchResult(
                facts=[],
                edges=[],
                nodes=[],
                query=query,
                total_count=0
            )

    def get_all_nodes(self, graph_id: str) -> List[NodeInfo]:
        """Retorna todos os nos do grafo via busca ampla."""
        logger.info(f"Carregando todos os nos do grafo {graph_id}...")

        search_result = self.client.search(
            group_ids=[graph_id],
            query="*",
            max_facts=500,
        )

        raw_facts = search_result.get("facts", [])
        result = []
        seen_names = set()

        for fact in raw_facts:
            if isinstance(fact, dict):
                name = fact.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    result.append(NodeInfo(
                        uuid=fact.get("uuid", ""),
                        name=name,
                        labels=["Entity"],
                        summary=fact.get("fact", ""),
                        attributes={}
                    ))

        logger.info(f"{len(result)} nos carregados")
        return result

    def get_all_edges(self, graph_id: str, include_temporal: bool = True) -> List[EdgeInfo]:
        """Retorna todas as relacoes do grafo via busca ampla."""
        logger.info(f"Carregando todas as relacoes do grafo {graph_id}...")

        search_result = self.client.search(
            group_ids=[graph_id],
            query="*",
            max_facts=500,
        )

        raw_facts = search_result.get("facts", [])
        result = []

        for fact in raw_facts:
            if isinstance(fact, dict):
                edge_info = EdgeInfo(
                    uuid=fact.get("uuid", ""),
                    name=fact.get("name", ""),
                    fact=fact.get("fact", ""),
                    source_node_uuid="",
                    target_node_uuid=""
                )
                if include_temporal:
                    edge_info.created_at = fact.get("created_at")
                    edge_info.valid_at = fact.get("valid_at")
                    edge_info.invalid_at = fact.get("invalid_at")
                    edge_info.expired_at = fact.get("expired_at")
                result.append(edge_info)
            elif isinstance(fact, str):
                result.append(EdgeInfo(
                    uuid="",
                    name="",
                    fact=fact,
                    source_node_uuid="",
                    target_node_uuid=""
                ))

        logger.info(f"{len(result)} relacoes carregadas")
        return result

    def get_node_detail(self, node_uuid: str) -> Optional[NodeInfo]:
        """Busca o detalhe de um no especifico via busca."""
        logger.info(f"Buscando detalhes do no {node_uuid[:8]}...")
        # Graphiti nao tem endpoint de busca por UUID de no.
        # Retorna None - os chamadores devem usar busca por nome.
        return None

    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[EdgeInfo]:
        """Retorna todas as relacoes ligadas a um no."""
        logger.info(f"Buscando relacoes ligadas ao no {node_uuid[:8]}...")
        # Sem endpoint direto no Graphiti. Retorna lista vazia.
        return []

    def get_entities_by_type(
        self,
        graph_id: str,
        entity_type: str
    ) -> List[NodeInfo]:
        """Retorna entidades filtradas por tipo via busca semantica."""
        logger.info(f"Buscando entidades do tipo {entity_type}...")

        search_result = self.client.search(
            group_ids=[graph_id],
            query=entity_type,
            max_facts=100,
        )

        raw_facts = search_result.get("facts", [])
        filtered = []
        seen_names = set()

        for fact in raw_facts:
            if isinstance(fact, dict):
                name = fact.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    filtered.append(NodeInfo(
                        uuid=fact.get("uuid", ""),
                        name=name,
                        labels=["Entity", entity_type],
                        summary=fact.get("fact", ""),
                        attributes={}
                    ))

        logger.info(f"{len(filtered)} entidades do tipo {entity_type} encontradas")
        return filtered

    def get_entity_summary(
        self,
        graph_id: str,
        entity_name: str
    ) -> Dict[str, Any]:
        """Gera um resumo relacional para a entidade informada."""
        logger.info(f"Montando resumo relacional da entidade {entity_name}...")

        search_result = self.search_graph(
            graph_id=graph_id,
            query=entity_name,
            limit=20
        )

        # Tenta localizar o no exato da entidade
        all_nodes = self.get_all_nodes(graph_id)
        entity_node = None
        for node in all_nodes:
            if node.name.lower() == entity_name.lower():
                entity_node = node
                break

        return {
            "entity_name": entity_name,
            "entity_info": entity_node.to_dict() if entity_node else None,
            "related_facts": search_result.facts,
            "related_edges": [e for e in search_result.edges],
            "total_relations": len(search_result.edges)
        }

    def get_graph_statistics(self, graph_id: str) -> Dict[str, Any]:
        """Retorna estatisticas gerais do grafo."""
        logger.info(f"Calculando estatisticas do grafo {graph_id}...")

        nodes = self.get_all_nodes(graph_id)
        edges = self.get_all_edges(graph_id)

        entity_types = {}
        for node in nodes:
            for label in node.labels:
                if label not in ["Entity", "Node"]:
                    entity_types[label] = entity_types.get(label, 0) + 1

        relation_types = {}
        for edge in edges:
            if edge.name:
                relation_types[edge.name] = relation_types.get(edge.name, 0) + 1

        return {
            "graph_id": graph_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entity_types": entity_types,
            "relation_types": relation_types
        }

    def get_simulation_context(
        self,
        graph_id: str,
        simulation_requirement: str,
        limit: int = 30
    ) -> Dict[str, Any]:
        """Monta um contexto consolidado a partir do objetivo da simulacao."""
        logger.info(f"Montando contexto da simulacao: {simulation_requirement[:50]}...")

        # Fallback seguro: se Graphiti falhar, retorna contexto vazio
        related_facts = []
        stats = {"total_nodes": 0, "total_edges": 0, "entity_types": {}}
        entities = []

        try:
            search_result = self.search_graph(
                graph_id=graph_id,
                query=simulation_requirement,
                limit=limit
            )
            related_facts = search_result.facts
        except Exception as e:
            logger.warning(f"Falha na busca Graphiti; retornando resultado vazio: {e}")

        try:
            stats = self.get_graph_statistics(graph_id)
        except Exception as e:
            logger.warning(f"Falha ao obter estatisticas do grafo: {e}")

        try:
            all_nodes = self.get_all_nodes(graph_id)
            for node in all_nodes:
                custom_labels = [l for l in node.labels if l not in ["Entity", "Node"]]
                if custom_labels:
                    entities.append({
                        "name": node.name,
                        "type": custom_labels[0],
                        "summary": node.summary
                    })
        except Exception as e:
            logger.warning(f"Falha ao obter nos do grafo: {e}")

        # Fallback: se Graphiti nao retornou dados, usar dados locais da simulacao
        if not related_facts and not entities:
            try:
                from .simulation_data_reader import SimulationDataReader
                # Tentar encontrar simulation_id associado ao graph_id
                sim_id = self._find_simulation_for_graph(graph_id)
                if sim_id:
                    reader = SimulationDataReader(sim_id)
                    local_facts = reader.get_facts_for_report(query=simulation_requirement, limit=limit)
                    local_stats = reader.get_statistics()
                    if local_facts:
                        related_facts = local_facts
                        stats = local_stats
                        logger.info(f"Fallback: {len(local_facts)} fatos carregados dos dados locais da simulacao {sim_id}")
            except Exception as e:
                logger.warning(f"Fallback de dados locais falhou: {e}")

        return {
            "simulation_requirement": simulation_requirement,
            "related_facts": related_facts,
            "graph_statistics": stats,
            "entities": entities[:limit],
            "total_entities": len(entities)
        }

    def _find_simulation_for_graph(self, graph_id: str) -> Optional[str]:
        """Encontra simulation_id associado a um graph_id."""
        import os, json
        sims_dir = os.path.join(Config.UPLOAD_FOLDER, 'simulations')
        if not os.path.exists(sims_dir):
            return None
        for sim_folder in os.listdir(sims_dir):
            state_path = os.path.join(sims_dir, sim_folder, 'state.json')
            if os.path.exists(state_path):
                try:
                    with open(state_path, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    if state.get('graph_id') == graph_id:
                        return sim_folder
                except Exception:
                    continue
        return None

    # Ferramentas analiticas principais.

    def insight_forge(
        self,
        graph_id: str,
        query: str,
        simulation_requirement: str,
        report_context: str = "",
        max_sub_queries: int = 5
    ) -> InsightForgeResult:
        """Executa busca profunda com decomposicao em subperguntas."""
        logger.info(f"InsightForge: busca profunda para '{query[:50]}'")

        result = InsightForgeResult(
            query=query,
            simulation_requirement=simulation_requirement,
            sub_queries=[]
        )

        # Etapa 1: gerar subperguntas com apoio do LLM
        sub_queries = self._generate_sub_queries(
            query=query,
            simulation_requirement=simulation_requirement,
            report_context=report_context,
            max_queries=max_sub_queries
        )
        result.sub_queries = sub_queries
        logger.info(f"{len(sub_queries)} subperguntas geradas")

        # Etapa 2: rodar busca semantica em cada subpergunta
        all_facts = []
        all_edges = []
        seen_facts = set()

        for sub_query in sub_queries:
            search_result = self.search_graph(
                graph_id=graph_id,
                query=sub_query,
                limit=15,
                scope="edges"
            )

            for fact in search_result.facts:
                if fact not in seen_facts:
                    all_facts.append(fact)
                    seen_facts.add(fact)

            all_edges.extend(search_result.edges)

        # Tambem consulta a pergunta original
        main_search = self.search_graph(
            graph_id=graph_id,
            query=query,
            limit=20,
            scope="edges"
        )
        for fact in main_search.facts:
            if fact not in seen_facts:
                all_facts.append(fact)
                seen_facts.add(fact)

        result.semantic_facts = all_facts
        result.total_facts = len(all_facts)

        # Etapa 3: extrair entidades dos fatos
        entity_insights = []
        seen_entity_names = set()

        for edge_data in all_edges:
            if isinstance(edge_data, dict):
                name = edge_data.get('name', '')
                if name and name not in seen_entity_names:
                    seen_entity_names.add(name)
                    related_facts = [
                        f for f in all_facts
                        if name.lower() in f.lower()
                    ]
                    entity_insights.append({
                        "uuid": edge_data.get("uuid", ""),
                        "name": name,
                        "type": "Entidade",
                        "summary": edge_data.get("fact", ""),
                        "related_facts": related_facts
                    })

        result.entity_insights = entity_insights
        result.total_entities = len(entity_insights)

        # Etapa 4: montar cadeias relacionais a partir dos fatos
        relationship_chains = []
        for edge_data in all_edges:
            if isinstance(edge_data, dict):
                fact = edge_data.get('fact', '')
                name = edge_data.get('name', '')
                if fact:
                    chain = f"[{name}]: {fact}" if name else fact
                    if chain not in relationship_chains:
                        relationship_chains.append(chain)

        result.relationship_chains = relationship_chains
        result.total_relationships = len(relationship_chains)

        logger.info(f"InsightForge concluido: {result.total_facts} fatos, {result.total_entities} entidades, {result.total_relationships} relacoes")
        return result

    def _generate_sub_queries(
        self,
        query: str,
        simulation_requirement: str,
        report_context: str = "",
        max_queries: int = 5
    ) -> List[str]:
        """Usa o LLM para quebrar uma pergunta complexa em subperguntas."""
        system_prompt = """Voce e um especialista em decomposicao de perguntas.
Transforme uma questao complexa em subperguntas observaveis dentro do mundo simulado.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

Regras:
1. Cada subpergunta deve ser especifica o bastante para gerar busca util
2. O conjunto deve cobrir perspectivas diferentes do problema
3. As subperguntas precisam ser coerentes com o cenario da simulacao
4. Retorne JSON no formato {"sub_queries": ["subpergunta 1", "subpergunta 2"]}"""

        user_prompt = f"""Contexto da simulacao:
{simulation_requirement}

{f"Contexto do relatorio: {report_context[:500]}" if report_context else ""}

Decomponha a pergunta abaixo em ate {max_queries} subperguntas:
{query}

Retorne somente o JSON."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )

            sub_queries = response.get("sub_queries", [])
            return [str(sq) for sq in sub_queries[:max_queries]]

        except Exception as e:
            logger.warning(f"Falha ao gerar subperguntas; usando fallback: {str(e)}")
            return [
                query,
                f"Principais atores envolvidos em {query}",
                f"Causas e impactos de {query}",
                f"Evolucao de {query}"
            ][:max_queries]

    def panorama_search(
        self,
        graph_id: str,
        query: str,
        include_expired: bool = True,
        limit: int = 50
    ) -> PanoramaResult:
        """Executa uma busca panoramica, incluindo historico quando pedido."""
        logger.info(f"PanoramaSearch: busca panoramica para '{query[:50]}'")

        result = PanoramaResult(query=query)

        # Carrega todos os nos
        all_nodes = self.get_all_nodes(graph_id)
        result.all_nodes = all_nodes
        result.total_nodes = len(all_nodes)

        # Carrega todas as relacoes com metadata temporal
        all_edges = self.get_all_edges(graph_id, include_temporal=True)
        result.all_edges = all_edges
        result.total_edges = len(all_edges)

        # Classifica fatos atuais e historicos
        active_facts = []
        historical_facts = []

        for edge in all_edges:
            if not edge.fact:
                continue

            is_historical = edge.is_expired or edge.is_invalid

            if is_historical:
                valid_at = edge.valid_at or "desconhecido"
                invalid_at = edge.invalid_at or edge.expired_at or "desconhecido"
                fact_with_time = f"[{valid_at} - {invalid_at}] {edge.fact}"
                historical_facts.append(fact_with_time)
            else:
                active_facts.append(edge.fact)

        # Ordena por aderencia a consulta
        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.replace(',', ' ').replace('\uff0c', ' ').split() if len(w.strip()) > 1]

        def relevance_score(fact: str) -> int:
            fact_lower = fact.lower()
            score = 0
            if query_lower in fact_lower:
                score += 100
            for kw in keywords:
                if kw in fact_lower:
                    score += 10
            return score

        active_facts.sort(key=relevance_score, reverse=True)
        historical_facts.sort(key=relevance_score, reverse=True)

        result.active_facts = active_facts[:limit]
        result.historical_facts = historical_facts[:limit] if include_expired else []
        result.active_count = len(active_facts)
        result.historical_count = len(historical_facts)

        logger.info(f"PanoramaSearch concluido: {result.active_count} fatos atuais, {result.historical_count} historicos")
        return result

    def quick_search(
        self,
        graph_id: str,
        query: str,
        limit: int = 10
    ) -> SearchResult:
        """Executa uma busca simples e leve."""
        logger.info(f"QuickSearch: busca simples para '{query[:50]}'")

        result = self.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit,
            scope="edges"
        )

        logger.info(f"QuickSearch concluido: {result.total_count} resultados")
        return result

    def interview_agents(
        self,
        simulation_id: str,
        interview_requirement: str,
        simulation_requirement: str = "",
        max_agents: int = 5,
        custom_questions: List[str] = None
    ) -> InterviewResult:
        """
        Entrevista agentes simulados via API real do OASIS.

        O fluxo:
        1. Carrega os perfis disponiveis
        2. Seleciona os perfis mais uteis para a pauta
        3. Gera perguntas, se necessario
        4. Chama a API de entrevista em lote
        5. Consolida as respostas em um resultado estruturado
        """
        from .simulation_runner import SimulationRunner

        logger.info(f"InterviewAgents: entrevista aprofundada via API real: {interview_requirement[:50]}...")

        result = InterviewResult(
            interview_topic=interview_requirement,
            interview_questions=custom_questions or []
        )

        # Etapa 1: carregar os perfis dos agentes
        profiles = self._load_agent_profiles(simulation_id)

        if not profiles:
            logger.warning(f"Nenhum perfil de agente foi encontrado para a simulacao {simulation_id}")
            result.summary = "Nenhum perfil de agente disponivel para entrevista"
            return result

        result.total_agents = len(profiles)
        logger.info(f"{len(profiles)} perfis de agente carregados")

        # Etapa 2: selecionar os agentes para entrevista
        selected_agents, selected_indices, selection_reasoning = self._select_agents_for_interview(
            profiles=profiles,
            interview_requirement=interview_requirement,
            simulation_requirement=simulation_requirement,
            max_agents=max_agents
        )

        result.selected_agents = selected_agents
        result.selection_reasoning = selection_reasoning
        logger.info(f"{len(selected_agents)} agentes selecionados para entrevista: {selected_indices}")

        # Etapa 3: gerar perguntas, se necessario
        if not result.interview_questions:
            result.interview_questions = self._generate_interview_questions(
                interview_requirement=interview_requirement,
                simulation_requirement=simulation_requirement,
                selected_agents=selected_agents
            )
            logger.info(f"{len(result.interview_questions)} perguntas de entrevista geradas")

        combined_prompt = "\n".join([f"{i+1}. {q}" for i, q in enumerate(result.interview_questions)])

        INTERVIEW_PROMPT_PREFIX = (
            "Voce esta sendo entrevistado. Com base na sua persona, memoria e acoes anteriores, "
            "responda diretamente, em texto puro, as perguntas abaixo.\n"
            "IMPORTANTE: Todas as respostas devem ser em português brasileiro.\n"
            "Regras de resposta:\n"
            "1. Responda em linguagem natural, sem chamar ferramentas\n"
            "2. Nao retorne JSON nem formato de tool call\n"
            "3. Nao use titulos Markdown como #, ## ou ###\n"
            "4. Responda em ordem numerada, com cada bloco iniciando em 'Pergunta X:'\n"
            "5. Separe as respostas por linha em branco\n"
            "6. Cada resposta deve ter conteudo real, com pelo menos 2 ou 3 frases\n\n"
        )
        optimized_prompt = f"{INTERVIEW_PROMPT_PREFIX}{combined_prompt}"

        # Etapa 4: chamar a API real de entrevista
        try:
            interviews_request = []
            for agent_idx in selected_indices:
                interviews_request.append({
                    "agent_id": agent_idx,
                    "prompt": optimized_prompt
                })

            logger.info(f"Chamando API de entrevista em lote: {len(interviews_request)} agentes")

            api_result = SimulationRunner.interview_agents_batch(
                simulation_id=simulation_id,
                interviews=interviews_request,
                platform=None,
                timeout=180.0
            )

            logger.info(f"API de entrevista retornou {api_result.get('interviews_count', 0)} resultados; success={api_result.get('success')}")

            if not api_result.get("success", False):
                error_msg = api_result.get("error", "Erro desconhecido")
                logger.warning(f"Falha retornada pela API de entrevista: {error_msg}")
                result.summary = f"Falha na API de entrevista: {error_msg}. Verifique o estado do ambiente OASIS."
                return result

            # Etapa 5: interpretar o retorno da API
            api_data = api_result.get("result", {})
            results_dict = api_data.get("results", {}) if isinstance(api_data, dict) else {}

            for i, agent_idx in enumerate(selected_indices):
                agent = selected_agents[i]
                agent_name = agent.get("realname", agent.get("username", f"Agent_{agent_idx}"))
                agent_role = agent.get("profession", "Nao informado")
                agent_bio = agent.get("bio", "")

                twitter_result = results_dict.get(f"twitter_{agent_idx}", {})
                reddit_result = results_dict.get(f"reddit_{agent_idx}", {})

                twitter_response = twitter_result.get("response", "")
                reddit_response = reddit_result.get("response", "")

                twitter_response = self._clean_tool_call_response(twitter_response)
                reddit_response = self._clean_tool_call_response(reddit_response)

                twitter_text = twitter_response if twitter_response else "[Sem resposta nesta plataforma]"
                reddit_text = reddit_response if reddit_response else "[Sem resposta nesta plataforma]"
                response_text = (
                    f"\u3010Resposta do Feed aberto\u3011\n{twitter_text}\n\n"
                    f"\u3010Resposta da Comunidade\u3011\n{reddit_text}"
                )

                import re
                combined_responses = f"{twitter_response} {reddit_response}"

                clean_text = re.sub(r'#{1,6}\s+', '', combined_responses)
                clean_text = re.sub(r'\{[^}]*tool_name[^}]*\}', '', clean_text)
                clean_text = re.sub(r'[*_`|>~\-]{2,}', '', clean_text)
                clean_text = re.sub(r'(?:Pergunta)\d+[\uff1a:]\s*', '', clean_text)
                clean_text = re.sub(r'\u3010[^\u3011]+\u3011', '', clean_text)

                sentences = re.split(r'[\u3002\uff01\uff1f.!?]', clean_text)
                meaningful = [
                    s.strip() for s in sentences
                    if 20 <= len(s.strip()) <= 150
                    and not re.match(r'^[\s\W\uff0c,\uff1b;\uff1a:\u3001]+', s.strip())
                    and not s.strip().startswith(('{', 'Pergunta'))
                ]
                meaningful.sort(key=len, reverse=True)
                key_quotes = [s + "." for s in meaningful[:3]]

                if not key_quotes:
                    paired = re.findall(r'\u201c([^\u201c\u201d]{15,100})\u201d', clean_text)
                    paired += re.findall(r'\u300c([^\u300c\u300d]{15,100})\u300d', clean_text)
                    paired += re.findall(r'"([^"\n]{15,100})"', clean_text)
                    key_quotes = [q for q in paired if not re.match(r'^[\uff0c,\uff1b;\uff1a:\u3001]', q)][:3]

                interview = AgentInterview(
                    agent_name=agent_name,
                    agent_role=agent_role,
                    agent_bio=agent_bio[:1000],
                    question=combined_prompt,
                    response=response_text,
                    key_quotes=key_quotes[:5]
                )
                result.interviews.append(interview)

            result.interviewed_count = len(result.interviews)

        except ValueError as e:
            logger.warning(f"Falha na API de entrevista; ambiente nao esta disponivel? {e}")
            result.summary = f"Falha na entrevista: {str(e)}. O ambiente de simulacao pode estar desligado; confirme que o OASIS esta ativo."
            return result
        except Exception as e:
            logger.error(f"Erro inesperado na API de entrevista: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result.summary = f"Ocorreu um erro durante a entrevista: {str(e)}"
            return result

        # Etapa 6: gerar o resumo final
        if result.interviews:
            result.summary = self._generate_interview_summary(
                interviews=result.interviews,
                interview_requirement=interview_requirement
            )

        logger.info(f"InterviewAgents concluido: {result.interviewed_count} agentes entrevistados no modo dual")
        return result

    @staticmethod
    def _clean_tool_call_response(response: str) -> str:
        """Limpa wrappers JSON de tool call e extrai o conteudo real."""
        if not response or not response.strip().startswith('{'):
            return response
        text = response.strip()
        if 'tool_name' not in text[:80]:
            return response
        import re as _re
        try:
            data = json.loads(text)
            if isinstance(data, dict) and 'arguments' in data:
                for key in ('content', 'text', 'body', 'message', 'reply'):
                    if key in data['arguments']:
                        return str(data['arguments'][key])
        except (json.JSONDecodeError, KeyError, TypeError):
            match = _re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            if match:
                return match.group(1).replace('\\n', '\n').replace('\\"', '"')
        return response

    def _load_agent_profiles(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Carrega os perfis de agente da simulacao."""
        import os
        import csv

        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )

        profiles = []

        reddit_profile_path = os.path.join(sim_dir, "reddit_profiles.json")
        if os.path.exists(reddit_profile_path):
            try:
                with open(reddit_profile_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                logger.info(f"{len(profiles)} perfis carregados de reddit_profiles.json")
                return profiles
            except Exception as e:
                logger.warning(f"Falha ao ler reddit_profiles.json: {e}")

        twitter_profile_path = os.path.join(sim_dir, "twitter_profiles.csv")
        if os.path.exists(twitter_profile_path):
            try:
                with open(twitter_profile_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        profiles.append({
                            "realname": row.get("name", ""),
                            "username": row.get("username", ""),
                            "bio": row.get("description", ""),
                            "persona": row.get("user_char", ""),
                            "profession": "Nao informado"
                        })
                logger.info(f"{len(profiles)} perfis carregados de twitter_profiles.csv")
                return profiles
            except Exception as e:
                logger.warning(f"Falha ao ler twitter_profiles.csv: {e}")

        return profiles

    def _select_agents_for_interview(
        self,
        profiles: List[Dict[str, Any]],
        interview_requirement: str,
        simulation_requirement: str,
        max_agents: int
    ) -> tuple:
        """Usa o LLM para selecionar os agentes mais adequados para entrevista."""
        agent_summaries = []
        for i, profile in enumerate(profiles):
            summary = {
                "index": i,
                "name": profile.get("realname", profile.get("username", f"Agent_{i}")),
                "profession": profile.get("profession", "Nao informado"),
                "bio": profile.get("bio", "")[:200],
                "interested_topics": profile.get("interested_topics", [])
            }
            agent_summaries.append(summary)

        system_prompt = """Voce e um especialista em planejamento de entrevistas.
Sua tarefa e selecionar, a partir da lista de agentes simulados, os perfis mais adequados para a pauta.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

Criterios:
1. Relacao entre identidade/profissao e o tema
2. Potencial de trazer perspectivas unicas ou valiosas
3. Diversidade de pontos de vista
4. Prioridade para personagens diretamente ligados ao evento

Retorne JSON no formato:
{
    "selected_indices": [lista de indices],
    "reasoning": "explicacao da selecao"
}"""

        user_prompt = f"""Necessidade da entrevista:
{interview_requirement}

Contexto da simulacao:
{simulation_requirement if simulation_requirement else "Nao informado"}

Lista de agentes disponiveis ({len(agent_summaries)}):
{json.dumps(agent_summaries, ensure_ascii=False, indent=2)}

Escolha no maximo {max_agents} agentes e explique a selecao."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )

            selected_indices = response.get("selected_indices", [])[:max_agents]
            reasoning = response.get("reasoning", "Selecao automatica por relevancia")

            selected_agents = []
            valid_indices = []
            for idx in selected_indices:
                if 0 <= idx < len(profiles):
                    selected_agents.append(profiles[idx])
                    valid_indices.append(idx)

            return selected_agents, valid_indices, reasoning

        except Exception as e:
            logger.warning(f"Falha ao selecionar agentes com LLM; usando fallback: {e}")
            selected = profiles[:max_agents]
            indices = list(range(min(max_agents, len(profiles))))
            return selected, indices, "Fallback padrao: primeiros perfis disponiveis"

    def _generate_interview_questions(
        self,
        interview_requirement: str,
        simulation_requirement: str,
        selected_agents: List[Dict[str, Any]]
    ) -> List[str]:
        """Usa o LLM para gerar perguntas de entrevista."""
        agent_roles = [a.get("profession", "Nao informado") for a in selected_agents]

        system_prompt = """Voce e um entrevistador profissional.
Gere de 3 a 5 perguntas aprofundadas com base na pauta.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

Requisitos:
1. Perguntas abertas
2. Capazes de revelar perspectivas diferentes
3. Devem cobrir fatos, opinioes e impactos
4. Linguagem natural
5. Perguntas curtas e claras
6. Sem prefacios longos

Retorne JSON: {"questions": ["Pergunta 1", "Pergunta 2"]}"""

        user_prompt = f"""Pauta da entrevista: {interview_requirement}

Contexto da simulacao: {simulation_requirement if simulation_requirement else "Nao informado"}

Perfis entrevistados: {', '.join(agent_roles)}

Gere de 3 a 5 perguntas."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )

            return response.get("questions", [f"Qual e a sua visao sobre {interview_requirement}?"])

        except Exception as e:
            logger.warning(f"Falha ao gerar perguntas de entrevista: {e}")
            return [
                f"Qual e a sua avaliacao sobre {interview_requirement}?",
                "Que impacto isso tem para voce ou para o grupo que voce representa?",
                "O que deveria ser feito para melhorar ou resolver a situacao?"
            ]

    def _generate_interview_summary(
        self,
        interviews: List[AgentInterview],
        interview_requirement: str
    ) -> str:
        """Gera um resumo consolidado das entrevistas."""
        if not interviews:
            return "Nenhuma entrevista foi concluida"

        interview_texts = []
        for interview in interviews:
            interview_texts.append(f"[{interview.agent_name} ({interview.agent_role})]\n{interview.response[:500]}")

        system_prompt = """Voce e um editor experiente.
Com base nas respostas dos entrevistados, gere um resumo jornalistico.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

Requisitos:
1. Sintetizar os principais pontos de vista
2. Indicar convergencias e divergencias
3. Destacar citacoes valiosas
4. Manter tom objetivo e neutro
5. Limitar o texto a cerca de 1000 palavras

Formato:
- Use paragrafos em texto simples
- Separe blocos com linha em branco
- Nao use titulos markdown nem divisorias
- Ao citar falas literais, use aspas normais"""

        user_prompt = f"""Tema da entrevista: {interview_requirement}

Conteudo das entrevistas:
{"".join(interview_texts)}

Gere o resumo final."""

        try:
            summary = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            return summary

        except Exception as e:
            logger.warning(f"Falha ao gerar resumo das entrevistas: {e}")
            return f"Foram entrevistados {len(interviews)} perfis: " + ", ".join([i.agent_name for i in interviews])
