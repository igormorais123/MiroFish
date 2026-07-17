import asyncio
import os
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI, status
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig  # type: ignore
from graphiti_core.nodes import EpisodeType  # type: ignore
from graphiti_core.utils.maintenance.graph_data_operations import clear_data  # type: ignore

from graph_service.config import get_settings
from graph_service.dto import AddEntityNodeRequest, AddMessagesRequest, Message, Result
from graph_service.zep_graphiti import ZepGraphiti, ZepGraphitiDep


class AsyncWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.task = None

    async def worker(self):
        while True:
            try:
                print(f'Got a job: (size of remaining queue: {self.queue.qsize()})')
                job = await self.queue.get()
                await job()
            except asyncio.CancelledError:
                break

    async def start(self):
        self.task = asyncio.create_task(self.worker())

    async def stop(self):
        if self.task:
            self.task.cancel()
            await self.task
        while not self.queue.empty():
            self.queue.get_nowait()


async_worker = AsyncWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await async_worker.start()
    yield
    await async_worker.stop()


router = APIRouter(lifespan=lifespan)


def _new_graphiti_client() -> ZepGraphiti:
    settings = get_settings()
    client = ZepGraphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    if settings.openai_base_url is not None:
        client.llm_client.config.base_url = settings.openai_base_url
    if settings.openai_api_key is not None:
        client.llm_client.config.api_key = settings.openai_api_key
    if settings.model_name is not None:
        client.llm_client.model = settings.model_name
        if hasattr(client.llm_client, "small_model"):
            client.llm_client.small_model = settings.model_name
    # O LLM pode vir do OmniRoute/Codex enquanto embeddings ficam no Ollama
    # local. Separar os endpoints evita exigir uma chave OpenAI paga apenas
    # para a vetorizacao do GraphRAG.
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
    # Graphiti 0.18 pesquisa e ingere por ``client.clients.embedder``. Manter
    # somente o atributo legado ``client.embedder`` deixa o endpoint antigo
    # ativo silenciosamente.
    if hasattr(client, 'clients'):
        client.clients.embedder = client.embedder
    return client


@router.post('/messages', status_code=status.HTTP_202_ACCEPTED)
async def add_messages(
    request: AddMessagesRequest,
):
    async def add_messages_task(m: Message):
        graphiti = _new_graphiti_client()
        try:
            await graphiti.add_episode(
                uuid=m.uuid,
                group_id=request.group_id,
                name=m.name,
                episode_body=f'{m.role or ""}({m.role_type}): {m.content}',
                reference_time=m.timestamp,
                source=EpisodeType.message,
                source_description=m.source_description,
            )
        finally:
            await graphiti.close()

    for m in request.messages:
        await async_worker.queue.put(partial(add_messages_task, m))

    return Result(message='Messages added to processing queue', success=True)


@router.post('/entity-node', status_code=status.HTTP_201_CREATED)
async def add_entity_node(
    request: AddEntityNodeRequest,
    graphiti: ZepGraphitiDep,
):
    node = await graphiti.save_entity_node(
        uuid=request.uuid,
        group_id=request.group_id,
        name=request.name,
        summary=request.summary,
    )
    return node


@router.delete('/entity-edge/{uuid}', status_code=status.HTTP_200_OK)
async def delete_entity_edge(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_entity_edge(uuid)
    return Result(message='Entity Edge deleted', success=True)


@router.delete('/group/{group_id}', status_code=status.HTTP_200_OK)
async def delete_group(group_id: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_group(group_id)
    return Result(message='Group deleted', success=True)


@router.delete('/episode/{uuid}', status_code=status.HTTP_200_OK)
async def delete_episode(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_episodic_node(uuid)
    return Result(message='Episode deleted', success=True)


@router.post('/clear', status_code=status.HTTP_200_OK)
async def clear(
    graphiti: ZepGraphitiDep,
):
    await clear_data(graphiti.driver)
    await graphiti.build_indices_and_constraints()
    return Result(message='Graph cleared', success=True)
