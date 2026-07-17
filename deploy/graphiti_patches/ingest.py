import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from functools import partial

from fastapi import APIRouter, FastAPI, status
from graphiti_core.nodes import EpisodeType  # type: ignore
from graphiti_core.utils.maintenance.graph_data_operations import clear_data  # type: ignore

from graph_service.config import get_settings
from graph_service.dto import AddEntityNodeRequest, AddMessagesRequest, Message, Result
from graph_service.zep_graphiti import (
    ZepGraphiti,
    ZepGraphitiDep,
    create_graphiti_client,
)


logger = logging.getLogger(__name__)


class AsyncWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.task = None

    async def worker(self):
        while True:
            try:
                print(f'Got a job: (size of remaining queue: {self.queue.qsize()})')
                job = await self.queue.get()
                try:
                    await job()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # Uma falha de ingestao nao pode encerrar silenciosamente o
                    # consumidor e deixar todas as mensagens seguintes na fila.
                    logger.exception('Graphiti message ingestion failed')
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break

    async def start(self):
        # Lifespans de APIRouter nao sao executados quando o router e incluido
        # em algumas versoes do FastAPI. O endpoint tambem chama start(), entao
        # este metodo precisa ser idempotente.
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.worker())

    async def stop(self):
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()


async_worker = AsyncWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await async_worker.start()
    yield
    await async_worker.stop()


router = APIRouter(lifespan=lifespan)


def _new_graphiti_client() -> ZepGraphiti:
    # Ingestao e consulta devem compartilhar o mesmo adaptador GPT-5/OmniRoute
    # e o mesmo embedder local. Duplicar esta configuracao fez o POST /messages
    # ignorar a compatibilidade de saida estruturada usada pelo /search.
    return create_graphiti_client(get_settings())


@router.post('/messages', status_code=status.HTTP_202_ACCEPTED)
async def add_messages(
    request: AddMessagesRequest,
):
    # O lifespan deste APIRouter nao e propagado pelo app principal da imagem
    # Graphiti. Iniciar sob demanda garante que o 202 corresponda a trabalho
    # efetivamente consumido, inclusive depois de uma falha anterior.
    await async_worker.start()

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
