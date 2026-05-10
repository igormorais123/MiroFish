"""Backward-compatible Zep paging helpers.

The backend now talks to Graphiti Server through REST. These helpers remain as
safe stubs so older imports fail closed instead of crashing the process.
"""

from __future__ import annotations

from typing import Any

from .logger import get_logger


logger = get_logger("mirofish.zep_paging")


def fetch_all_nodes(client: Any, graph_id: str, **kwargs: Any) -> list[Any]:
    """Compatibility stub for legacy Zep SDK callers."""
    logger.warning(
        "fetch_all_nodes() is a legacy compatibility stub. "
        "Use GraphitiClient.search() directly."
    )
    return []


def fetch_all_edges(client: Any, graph_id: str, **kwargs: Any) -> list[Any]:
    """Compatibility stub for legacy Zep SDK callers."""
    logger.warning(
        "fetch_all_edges() is a legacy compatibility stub. "
        "Use GraphitiClient.search() directly."
    )
    return []
