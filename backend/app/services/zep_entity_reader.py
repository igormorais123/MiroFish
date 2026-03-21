"""
Servico de leitura e filtragem de entidades do grafo.
Le fatos do Graphiti Server e filtra os que correspondem a tipos de entidade pre-definidos.
"""

import time
from typing import Dict, Any, List, Optional, Set, Callable, TypeVar
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger
from ..utils.graphiti_client import GraphitiClient

logger = get_logger('mirofish.zep_entity_reader')

T = TypeVar('T')


@dataclass
class EntityNode:
    """Estrutura de dados do no de entidade"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    # Informacoes de arestas relacionadas
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    # Informacoes de outros nos relacionados
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }

    def get_entity_type(self) -> Optional[str]:
        """Obter tipo da entidade (excluindo o label padrao Entity)"""
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None


@dataclass
class FilteredEntities:
    """Conjunto de entidades filtradas"""
    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    Servico de leitura e filtragem de entidades do grafo.

    Funcionalidades principais:
    1. Buscar fatos no Graphiti Server via POST /search
    2. Extrair entidades unicas a partir dos fatos retornados
    3. Filtrar entidades por tipo pre-definido
    """

    def __init__(self, api_key: Optional[str] = None):
        """Inicializa o leitor.

        Args:
            api_key: Mantido na assinatura para compatibilidade. Nao e
                     necessario para o Graphiti Server.
        """
        self.client = GraphitiClient()

    def _call_with_retry(
        self,
        func: Callable[[], T],
        operation_name: str,
        max_retries: int = 3,
        initial_delay: float = 2.0
    ) -> T:
        """Chamada com mecanismo de retentativa."""
        last_exception = None
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Graphiti {operation_name} tentativa {attempt + 1} falhou: {str(e)[:100]}, "
                        f"retentando em {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Graphiti {operation_name} falhou apos {max_retries} tentativas: {str(e)}")

        raise last_exception

    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        Obter todos os nos do grafo via busca ampla no Graphiti.

        No Graphiti, nao ha endpoint direto de listagem de nos.
        Fazemos uma busca ampla e extraimos entidades unicas dos fatos.
        """
        logger.info(f"Obtendo todos os nos do grafo {graph_id}...")

        search_result = self.client.search(
            group_ids=[graph_id],
            query="*",
            max_facts=500,
        )

        raw_facts = search_result.get("facts", [])
        nodes_data = []
        seen_names = set()

        for fact in raw_facts:
            if isinstance(fact, dict):
                name = fact.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    nodes_data.append({
                        "uuid": fact.get("uuid", ""),
                        "name": name,
                        "labels": ["Entity"],
                        "summary": fact.get("fact", ""),
                        "attributes": {},
                    })

        logger.info(f"Total de {len(nodes_data)} nos obtidos")
        return nodes_data

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        Obter todas as arestas (fatos) do grafo via busca ampla.
        """
        logger.info(f"Obtendo todas as arestas do grafo {graph_id}...")

        search_result = self.client.search(
            group_ids=[graph_id],
            query="*",
            max_facts=500,
        )

        raw_facts = search_result.get("facts", [])
        edges_data = []

        for fact in raw_facts:
            if isinstance(fact, dict):
                edges_data.append({
                    "uuid": fact.get("uuid", ""),
                    "name": fact.get("name", ""),
                    "fact": fact.get("fact", ""),
                    "source_node_uuid": "",
                    "target_node_uuid": "",
                    "attributes": {},
                })
            elif isinstance(fact, str):
                edges_data.append({
                    "uuid": "",
                    "name": "",
                    "fact": fact,
                    "source_node_uuid": "",
                    "target_node_uuid": "",
                    "attributes": {},
                })

        logger.info(f"Total de {len(edges_data)} arestas obtidas")
        return edges_data

    def get_node_edges(self, node_uuid: str) -> List[Dict[str, Any]]:
        """
        Obter arestas relacionadas a um no especifico.

        No Graphiti, buscamos pelo nome da entidade.
        """
        # Sem endpoint direto para listar arestas de um no no Graphiti
        logger.debug(f"get_node_edges nao disponivel diretamente no Graphiti para uuid {node_uuid}")
        return []

    def filter_defined_entities(
        self,
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True
    ) -> FilteredEntities:
        """
        Filtrar entidades por tipo, via busca semantica no Graphiti.

        Se defined_entity_types for fornecido, faz busca direcionada
        para cada tipo. Caso contrario, retorna todas as entidades encontradas.
        """
        logger.info(f"Iniciando filtragem de entidades do grafo {graph_id}...")

        all_facts = []
        seen_fact_ids = set()

        if defined_entity_types:
            # Busca direcionada por tipo
            for entity_type in defined_entity_types:
                search_result = self.client.search(
                    group_ids=[graph_id],
                    query=entity_type,
                    max_facts=100,
                )
                for fact in search_result.get("facts", []):
                    fact_id = fact.get("uuid", "") if isinstance(fact, dict) else fact
                    if fact_id not in seen_fact_ids:
                        seen_fact_ids.add(fact_id)
                        all_facts.append(fact)
        else:
            # Busca ampla
            search_result = self.client.search(
                group_ids=[graph_id],
                query="*",
                max_facts=500,
            )
            all_facts = search_result.get("facts", [])

        # Extrair entidades dos fatos
        entities = []
        entity_types_found = set()
        seen_names = set()

        for fact in all_facts:
            if isinstance(fact, dict):
                name = fact.get("name", "")
                fact_text = fact.get("fact", "")
            elif isinstance(fact, str):
                name = ""
                fact_text = fact
            else:
                continue

            if not name or name in seen_names:
                continue
            seen_names.add(name)

            # Determinar tipo de entidade
            entity_type = name  # No Graphiti, o nome da relacao funciona como tipo
            if defined_entity_types:
                matching = [t for t in defined_entity_types if t.lower() in name.lower() or t.lower() in fact_text.lower()]
                if not matching:
                    continue
                entity_type = matching[0]

            entity_types_found.add(entity_type)

            entity = EntityNode(
                uuid=fact.get("uuid", "") if isinstance(fact, dict) else "",
                name=name,
                labels=["Entity", entity_type],
                summary=fact_text,
                attributes={},
            )

            # Enriquecer com arestas relacionadas
            if enrich_with_edges:
                related_search = self.client.search(
                    group_ids=[graph_id],
                    query=name,
                    max_facts=20,
                )
                related_facts = related_search.get("facts", [])
                entity.related_edges = [
                    {
                        "direction": "related",
                        "edge_name": f.get("name", "") if isinstance(f, dict) else "",
                        "fact": f.get("fact", f) if isinstance(f, dict) else f,
                    }
                    for f in related_facts
                ]

            entities.append(entity)

        total_count = len(all_facts)
        logger.info(
            f"Filtragem concluida: total de fatos {total_count}, "
            f"entidades encontradas {len(entities)}, tipos: {entity_types_found}"
        )

        return FilteredEntities(
            entities=entities,
            entity_types=entity_types_found,
            total_count=total_count,
            filtered_count=len(entities),
        )

    def get_entity_with_context(
        self,
        graph_id: str,
        entity_uuid: str
    ) -> Optional[EntityNode]:
        """
        Obter uma entidade com contexto completo.

        No Graphiti, buscamos fatos relacionados ao nome da entidade.
        """
        try:
            # Primeiro buscar a entidade por UUID (via busca ampla)
            all_nodes = self.get_all_nodes(graph_id)
            target_node = None
            for node in all_nodes:
                if node["uuid"] == entity_uuid:
                    target_node = node
                    break

            if not target_node:
                return None

            entity_name = target_node["name"]

            # Buscar fatos relacionados
            search_result = self.client.search(
                group_ids=[graph_id],
                query=entity_name,
                max_facts=30,
            )

            related_facts = search_result.get("facts", [])
            related_edges = [
                {
                    "direction": "related",
                    "edge_name": f.get("name", "") if isinstance(f, dict) else "",
                    "fact": f.get("fact", f) if isinstance(f, dict) else f,
                }
                for f in related_facts
            ]

            return EntityNode(
                uuid=target_node["uuid"],
                name=target_node["name"],
                labels=target_node["labels"],
                summary=target_node["summary"],
                attributes=target_node.get("attributes", {}),
                related_edges=related_edges,
                related_nodes=[],
            )

        except Exception as e:
            logger.error(f"Falha ao obter entidade {entity_uuid}: {str(e)}")
            return None

    def get_entities_by_type(
        self,
        graph_id: str,
        entity_type: str,
        enrich_with_edges: bool = True
    ) -> List[EntityNode]:
        """Obter todas as entidades de um tipo especifico."""
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges
        )
        return result.entities
