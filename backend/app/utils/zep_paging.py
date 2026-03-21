"""Modulo de compatibilidade retroativa.

Este modulo existia para paginacao do SDK Zep Cloud. Agora o backend usa o
Graphiti Server via REST, e a paginacao nao e mais necessaria.

As funcoes fetch_all_nodes e fetch_all_edges sao mantidas como stubs para
evitar erros de importacao em codigo legado que ainda nao foi atualizado.
"""

from __future__ import annotations

from typing import Any

from .logger import get_logger

logger = get_logger('mirofish.zep_paging')


def fetch_all_nodes(client: Any, graph_id: str, **kwargs) -> list[Any]:
    """Stub de compatibilidade. O backend agora usa GraphitiClient.search()."""
    logger.warning(
        "fetch_all_nodes() e um stub legado. "
        "Use GraphitiClient.search() diretamente."
    )
    return []


def fetch_all_edges(client: Any, graph_id: str, **kwargs) -> list[Any]:
    """Stub de compatibilidade. O backend agora usa GraphitiClient.search()."""
    logger.warning(
        "fetch_all_edges() e um stub legado. "
        "Use GraphitiClient.search() diretamente."
    )
    return []
