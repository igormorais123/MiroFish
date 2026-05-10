from __future__ import annotations

from app.utils import zep_paging


def test_zep_paging_compat_stubs_fail_closed():
    assert zep_paging.fetch_all_nodes(object(), "graph-id") == []
    assert zep_paging.fetch_all_edges(object(), "graph-id") == []
