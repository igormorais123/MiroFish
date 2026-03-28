"""
Extrator de entidades via LLM (fallback quando Graphiti esta indisponivel).
Usa a ontologia gerada + texto do documento para extrair entidades concretas.
"""

import uuid
import json
from typing import Dict, Any, List, Optional, Set

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .zep_entity_reader import EntityNode, FilteredEntities

logger = get_logger('mirofish.llm_entity_extractor')


class LLMEntityExtractor:
    """Extrai entidades de texto usando LLM como alternativa ao Graphiti."""

    def __init__(self):
        self.client = LLMClient()

    def extract_entities(
        self,
        text: str,
        ontology: Optional[Dict[str, Any]] = None,
        defined_entity_types: Optional[List[str]] = None,
    ) -> FilteredEntities:
        """
        Extrair entidades concretas do texto usando LLM.

        Args:
            text: Texto do documento (pode ser truncado se muito longo)
            ontology: Ontologia gerada previamente (entity_types, edge_types)
            defined_entity_types: Tipos de entidade para filtrar

        Returns:
            FilteredEntities com as entidades extraidas
        """
        # Truncar texto se necessario (limite ~8000 chars para caber no prompt)
        max_text_len = 8000
        truncated_text = text[:max_text_len] if len(text) > max_text_len else text

        # Montar contexto de ontologia
        ontology_context = ""
        if ontology:
            entity_types = ontology.get("entity_types", [])
            edge_types = ontology.get("edge_types", [])
            if entity_types:
                types_str = "\n".join(
                    f"- {et.get('name', '?')}: {et.get('description', '')}"
                    for et in entity_types
                )
                ontology_context += f"\nTipos de entidade definidos:\n{types_str}\n"
            if edge_types:
                edges_str = "\n".join(
                    f"- {ed.get('name', '?')}: {ed.get('description', '')}"
                    for ed in edge_types
                )
                ontology_context += f"\nTipos de relacao:\n{edges_str}\n"

        if defined_entity_types:
            ontology_context += f"\nFiltrar apenas estes tipos: {', '.join(defined_entity_types)}\n"

        prompt = f"""Analise o texto abaixo e extraia todas as entidades concretas (pessoas, organizacoes, lugares, eventos, conceitos-chave).

{ontology_context}

TEXTO:
{truncated_text}

Responda APENAS com um JSON valido no formato:
{{
  "entities": [
    {{
      "name": "Nome da Entidade",
      "type": "Tipo (Pessoa, Organizacao, Lugar, Evento, Conceito, etc.)",
      "summary": "Descricao breve baseada no texto",
      "relations": ["Descricao de relacao com outra entidade"]
    }}
  ]
}}

Extraia entre 5 e 30 entidades. Priorize as mais relevantes para uma simulacao de interacao social."""

        logger.info("Extraindo entidades via LLM...")

        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": "Voce e um extrator de entidades. Responda apenas com JSON valido."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )

            # Limpar e parsear JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1] if "\n" in result else result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                result = result.strip()

            data = json.loads(result)
            raw_entities = data.get("entities", [])

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Falha ao extrair entidades via LLM: {e}")
            return FilteredEntities(
                entities=[],
                entity_types=set(),
                total_count=0,
                filtered_count=0,
            )

        # Converter para EntityNode
        entities: List[EntityNode] = []
        entity_types_found: Set[str] = set()

        for raw in raw_entities:
            name = raw.get("name", "").strip()
            etype = raw.get("type", "Entity").strip()
            summary = raw.get("summary", "").strip()
            relations = raw.get("relations", [])

            if not name:
                continue

            entity_types_found.add(etype)

            entity = EntityNode(
                uuid=str(uuid.uuid4()),
                name=name,
                labels=["Entity", etype],
                summary=summary,
                attributes={"extraction_method": "llm_fallback"},
                related_edges=[
                    {"direction": "related", "edge_name": "", "fact": rel}
                    for rel in relations
                ],
                related_nodes=[],
            )
            entities.append(entity)

        logger.info(f"LLM extraiu {len(entities)} entidades de {len(entity_types_found)} tipos")

        return FilteredEntities(
            entities=entities,
            entity_types=entity_types_found,
            total_count=len(entities),
            filtered_count=len(entities),
        )
