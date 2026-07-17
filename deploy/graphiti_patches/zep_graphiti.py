import json
import logging
import os
import re
from types import SimpleNamespace
from typing import Annotated

from fastapi import Depends, HTTPException
from graphiti_core import Graphiti  # type: ignore
from graphiti_core.edges import EntityEdge  # type: ignore
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig  # type: ignore
from graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError, NodeNotFoundError
from graphiti_core.llm_client import LLMClient, LLMConfig  # type: ignore
from graphiti_core.llm_client.openai_client import OpenAIClient  # type: ignore
from graphiti_core.nodes import EntityNode, EpisodicNode  # type: ignore

from graph_service.config import ZepEnvDep
from graph_service.dto import FactResult

logger = logging.getLogger(__name__)


def _luna_reasoning_effort() -> str:
    effort = os.environ.get('LUNA_REASONING_EFFORT', 'low').strip().lower()
    return effort if effort in {'none', 'low', 'medium', 'high', 'xhigh'} else 'low'


def _is_gpt5(model: str) -> bool:
    return 'gpt-5' in model.lower()


def _decode_json_content(content: str):
    cleaned = (content or '').strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return json.loads(cleaned)


def _validate_structured_payload(data, response_model):
    """Aceita pequenas variacoes comuns sem afrouxar o schema final."""
    fields = getattr(response_model, 'model_fields', {}) or {}
    if len(fields) == 1:
        field = next(iter(fields))
        if field == 'root':
            return response_model.model_validate(data)
        if isinstance(data, list):
            data = {field: data}
        elif isinstance(data, dict) and field not in data:
            short_name = field.removeprefix('extracted_')
            if short_name in data:
                data = {**data, field: data[short_name]}
            else:
                list_values = [value for value in data.values() if isinstance(value, list)]
                if len(list_values) == 1:
                    data = {**data, field: list_values[0]}
    return response_model.model_validate(data)


class LunaOpenAIClient(OpenAIClient):
    """Graphiti client compatible with GPT-5 models routed by OmniRoute."""

    async def _create_structured_completion(
        self, model, messages, temperature, max_tokens, response_model
    ):
        if not _is_gpt5(model):
            return await super()._create_structured_completion(
                model, messages, temperature, max_tokens, response_model
            )
        # Alguns gateways nao preservam o JSON Schema do beta.parse e o modelo
        # pode devolver cerca Markdown ou um alias como "entities". Pedimos
        # JSON, normalizamos somente o envelope e validamos no modelo Pydantic.
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens,
            reasoning_effort=_luna_reasoning_effort(),
            response_format={'type': 'json_object'},
        )
        data = _decode_json_content(response.choices[0].message.content or '{}')
        parsed = _validate_structured_payload(data, response_model)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed, refusal=None))]
        )

    async def _create_completion(
        self, model, messages, temperature, max_tokens, response_model=None
    ):
        if not _is_gpt5(model):
            return await super()._create_completion(
                model, messages, temperature, max_tokens, response_model
            )
        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens,
            reasoning_effort=_luna_reasoning_effort(),
            response_format={'type': 'json_object'},
        )


class ZepGraphiti(Graphiti):
    def __init__(self, uri: str, user: str, password: str, llm_client: LLMClient | None = None):
        super().__init__(uri, user, password, llm_client)

    async def save_entity_node(self, name: str, uuid: str, group_id: str, summary: str = ''):
        new_node = EntityNode(
            name=name,
            uuid=uuid,
            group_id=group_id,
            summary=summary,
        )
        await new_node.generate_name_embedding(self.embedder)
        await new_node.save(self.driver)
        return new_node

    async def get_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            return edge
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_group(self, group_id: str):
        try:
            edges = await EntityEdge.get_by_group_ids(self.driver, [group_id])
        except GroupsEdgesNotFoundError:
            logger.warning(f'No edges found for group {group_id}')
            edges = []

        nodes = await EntityNode.get_by_group_ids(self.driver, [group_id])
        episodes = await EpisodicNode.get_by_group_ids(self.driver, [group_id])

        for edge in edges:
            await edge.delete(self.driver)
        for node in nodes:
            await node.delete(self.driver)
        for episode in episodes:
            await episode.delete(self.driver)

    async def delete_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            await edge.delete(self.driver)
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_episodic_node(self, uuid: str):
        try:
            episode = await EpisodicNode.get_by_uuid(self.driver, uuid)
            await episode.delete(self.driver)
        except NodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e


def _configure_client(client: ZepGraphiti, settings) -> ZepGraphiti:
    if settings.openai_base_url is not None:
        client.llm_client.config.base_url = settings.openai_base_url
    if settings.openai_api_key is not None:
        client.llm_client.config.api_key = settings.openai_api_key
    if settings.model_name is not None:
        client.llm_client.model = settings.model_name
        if hasattr(client.llm_client, "small_model"):
            client.llm_client.small_model = settings.model_name
    # A dependencia compartilhada atende busca, inicializacao e mutacoes. Ela
    # precisa usar o mesmo endpoint local de embeddings configurado no ingest;
    # caso contrario /search ainda tenta vetorizar pelo provedor do LLM.
    embedder_base_url = os.getenv('EMBEDDER_BASE_URL') or settings.openai_base_url
    embedder_api_key = os.getenv('EMBEDDER_API_KEY') or settings.openai_api_key
    embedder_model = (
        os.getenv('EMBEDDER_MODEL_NAME')
        or settings.embedding_model_name
        or 'nomic-embed-text'
    )
    try:
        embedder_dim = int(os.getenv('EMBEDDER_DIM', '768'))
    except ValueError:
        embedder_dim = 768

    client.embedder = OpenAIEmbedder(
        OpenAIEmbedderConfig(
            api_key=embedder_api_key,
            base_url=embedder_base_url,
            embedding_model=embedder_model,
            embedding_dim=embedder_dim,
        )
    )
    if hasattr(client, 'clients'):
        client.clients.embedder = client.embedder
    return client


def _new_zep_graphiti(settings) -> ZepGraphiti:
    llm_client = LunaOpenAIClient(
        LLMConfig(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.model_name,
            small_model=settings.model_name,
            max_tokens=8192,
        )
    )
    return _configure_client(
        ZepGraphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm_client=llm_client,
        ),
        settings,
    )


async def get_graphiti(settings: ZepEnvDep):
    client = _new_zep_graphiti(settings)
    try:
        yield client
    finally:
        await client.close()


async def initialize_graphiti(settings: ZepEnvDep):
    client = _new_zep_graphiti(settings)
    try:
        await client.build_indices_and_constraints()
    finally:
        await client.close()


def get_fact_result_from_edge(edge: EntityEdge):
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
    )


ZepGraphitiDep = Annotated[ZepGraphiti, Depends(get_graphiti)]
