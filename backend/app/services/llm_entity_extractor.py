"""
Extrator de entidades via LLM (fallback quando Graphiti esta indisponivel).
Usa a ontologia gerada + texto do documento para extrair entidades concretas.
"""

import uuid
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Set, Tuple

from ..utils.file_parser import PageSpan, locate_page
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .zep_entity_reader import EntityNode, FilteredEntities

logger = get_logger('mirofish.llm_entity_extractor')

# O texto inteiro nao cabe num prompt, entao e lido em pedacos. Antes ele era
# truncado nos primeiros 8000 caracteres: com nove PDFs concatenados, o grafo
# saia construido so a partir da capa do primeiro documento.
CHUNK_SIZE = int(os.environ.get('ENTITY_CHUNK_SIZE', '8000'))
# Sobreposicao para nao partir uma entidade exatamente na fronteira.
CHUNK_OVERLAP = int(os.environ.get('ENTITY_CHUNK_OVERLAP', '400'))
# Ler em paralelo so e viavel porque a ponte sustenta chamadas concorrentes.
MAX_WORKERS = int(os.environ.get('ENTITY_EXTRACTION_WORKERS', '8'))
# Guarda contra um corpus absurdo consumir a assinatura inteira num run.
MAX_CHUNKS = int(os.environ.get('ENTITY_MAX_CHUNKS', '120'))
# Janela de texto guardada como prova de onde a entidade foi encontrada.
EXCERPT_RADIUS = 220


# Fronteiras onde cortar sem partir uma frase no meio, na mesma ordem de
# preferencia usada por utils.file_parser.split_text_into_chunks.
FRONTEIRAS = ('.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ')


def split_into_chunks(text: str) -> List[Tuple[int, str]]:
    """
    Divide o texto em pedacos sobrepostos, devolvendo (offset, trecho).

    Existe `utils.file_parser.split_text_into_chunks`, mas ela devolve apenas
    as strings e aplica strip em cada bloco — o que descarta a posicao no texto
    original. Sem essa posicao nao ha como dizer de onde a entidade saiu, que e
    o ponto da proveniencia. A quebra por fronteira de sentenca vem de la.
    """
    if not text:
        return []
    if len(text) <= CHUNK_SIZE:
        return [(0, text)]

    pedacos: List[Tuple[int, str]] = []
    inicio = 0
    while inicio < len(text):
        fim = min(inicio + CHUNK_SIZE, len(text))
        if fim < len(text):
            janela = text[inicio:fim]
            for sep in FRONTEIRAS:
                corte = janela.rfind(sep)
                # Exige que o corte esteja adiantado no bloco, senao o pedaco
                # sai curto demais e o numero de chamadas explode.
                if corte > CHUNK_SIZE * 0.3:
                    fim = inicio + corte + len(sep)
                    break

        trecho = text[inicio:fim]
        if trecho.strip():
            pedacos.append((inicio, trecho))
        if len(pedacos) >= MAX_CHUNKS:
            logger.warning(
                "Corpus excede %d pedacos; %d de %d caracteres ficaram de fora",
                MAX_CHUNKS, len(text) - fim, len(text),
            )
            break
        if fim >= len(text):
            break
        inicio = max(fim - CHUNK_OVERLAP, inicio + 1)
    return pedacos


def find_excerpt(nome: str, trecho: str, offset: int) -> Optional[Dict[str, Any]]:
    """
    Localiza o nome da entidade dentro do pedaco que a originou.

    Devolve None quando o nome nao aparece no texto — sinal de que o modelo a
    inventou em vez de extrair. Sem esta checagem, entidade alucinada e
    entidade lida entram no grafo com o mesmo peso.
    """
    posicao = trecho.lower().find((nome or "").lower())
    if posicao < 0:
        return None
    inicio = max(posicao - EXCERPT_RADIUS, 0)
    return {
        "char_offset": offset + posicao,
        "excerpt": trecho[inicio:posicao + len(nome) + EXCERPT_RADIUS].strip(),
    }


class LLMEntityExtractor:
    """Extrai entidades de texto usando LLM como alternativa ao Graphiti."""

    def __init__(self):
        self.client = LLMClient()

    def extract_entities(
        self,
        text: str,
        ontology: Optional[Dict[str, Any]] = None,
        defined_entity_types: Optional[List[str]] = None,
        page_index: Optional[List[PageSpan]] = None,
    ) -> FilteredEntities:
        """
        Extrair entidades concretas do texto usando LLM.

        Args:
            text: Corpus completo, lido em pedacos sobrepostos
            ontology: Ontologia gerada previamente (entity_types, edge_types)
            defined_entity_types: Tipos de entidade para filtrar
            page_index: Spans de `FileParser.extract_with_page_index`. Com eles a
                entidade guarda documento e folha, e nao apenas o offset — que e
                a diferenca entre "a IA disse" e "esta na fl. X".

        Returns:
            FilteredEntities com as entidades extraidas
        """
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

        pedacos = split_into_chunks(text)
        if not pedacos:
            logger.warning("Texto vazio; nenhuma entidade a extrair")
            return FilteredEntities(entities=[], entity_types=set(), total_count=0, filtered_count=0)

        logger.info(
            "Extraindo entidades de %d caracteres em %d pedacos (%d em paralelo)",
            len(text), len(pedacos), MAX_WORKERS,
        )

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            colhidos = list(executor.map(
                lambda p: self._extract_from_chunk(p[0], p[1], ontology_context),
                pedacos,
            ))

        return self._merge(colhidos, len(pedacos), page_index)

    def _extract_from_chunk(
        self, offset: int, trecho: str, ontology_context: str
    ) -> List[Dict[str, Any]]:
        """Extrai de um pedaco. Falha isolada nao derruba o corpus inteiro."""
        prompt = f"""Analise o texto abaixo e extraia todas as entidades concretas (pessoas, organizacoes, lugares, eventos, conceitos-chave).

{ontology_context}

TEXTO:
{trecho}

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

Extraia entre 5 e 30 entidades. Use exatamente a grafia que aparece no texto."""

        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": "Voce e um extrator de entidades. Responda apenas com JSON valido."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=8000,
            )

            result = (result or "").strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1] if "\n" in result else result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                result = result.strip()

            brutas = json.loads(result).get("entities", [])
        except Exception as e:
            logger.error("Falha ao extrair entidades no offset %d: %s", offset, e)
            return []

        # Anexa a proveniencia aqui, onde o pedaco de origem ainda existe.
        for bruta in brutas:
            if isinstance(bruta, dict):
                bruta["_proveniencia"] = find_excerpt(bruta.get("name", ""), trecho, offset)
        return [b for b in brutas if isinstance(b, dict)]

    def _merge(
        self,
        colhidos: List[List[Dict[str, Any]]],
        total_pedacos: int,
        page_index: Optional[List[PageSpan]] = None,
    ) -> FilteredEntities:
        """
        Junta o que veio dos pedacos, deduplicando por nome.

        A sobreposicao entre pedacos faz a mesma entidade voltar mais de uma
        vez; cada reaparicao vira uma ocorrencia da mesma entidade, nao um no
        novo. Entidade sem trecho de origem e mantida, porem marcada, para que
        o gate a distinga de uma leitura ancorada.
        """
        por_nome: Dict[str, EntityNode] = {}
        tipos: Set[str] = set()
        sem_ancora = 0

        def citacao(offset: Optional[int]) -> Dict[str, Any]:
            """Documento e folha do offset, quando ha indice de paginas."""
            if offset is None or not page_index:
                return {"doc_id": None, "page": None, "citation": None}
            span = locate_page(offset, page_index)
            if span is None:
                return {"doc_id": None, "page": None, "citation": None}
            return {
                "doc_id": span.doc_id,
                "page": span.page,
                "citation": span.as_citation(),
            }

        for brutas in colhidos:
            for bruta in brutas:
                nome = (bruta.get("name") or "").strip()
                if not nome:
                    continue
                tipo = (bruta.get("type") or "Entity").strip()
                chave = nome.casefold()
                proveniencia = bruta.get("_proveniencia")

                existente = por_nome.get(chave)
                if existente is not None:
                    existente.attributes["occurrences"] += 1
                    if proveniencia and not existente.attributes.get("source_excerpt"):
                        existente.attributes.update({
                            "source_excerpt": proveniencia["excerpt"],
                            "char_offset": proveniencia["char_offset"],
                            "verbatim_found": True,
                            **citacao(proveniencia["char_offset"]),
                        })
                    continue

                tipos.add(tipo)
                if not proveniencia:
                    sem_ancora += 1
                por_nome[chave] = EntityNode(
                    uuid=str(uuid.uuid4()),
                    name=nome,
                    labels=["Entity", tipo],
                    summary=(bruta.get("summary") or "").strip(),
                    attributes={
                        "extraction_method": "llm_fallback",
                        "occurrences": 1,
                        "verbatim_found": bool(proveniencia),
                        "source_excerpt": proveniencia["excerpt"] if proveniencia else None,
                        "char_offset": proveniencia["char_offset"] if proveniencia else None,
                        **citacao(proveniencia["char_offset"] if proveniencia else None),
                    },
                    related_edges=[
                        {"direction": "related", "edge_name": "", "fact": rel}
                        for rel in (bruta.get("relations") or [])
                    ],
                    related_nodes=[],
                )

        entities = list(por_nome.values())
        logger.info(
            "LLM extraiu %d entidades de %d tipos em %d pedacos (%d sem trecho de origem)",
            len(entities), len(tipos), total_pedacos, sem_ancora,
        )
        return FilteredEntities(
            entities=entities,
            entity_types=tipos,
            total_count=len(entities),
            filtered_count=len(entities),
        )
