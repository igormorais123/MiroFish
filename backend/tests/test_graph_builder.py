import pytest

from app.services.graph_builder import GraphBuilderService


def test_wait_for_graph_materialization_fails_when_graph_stays_empty(monkeypatch):
    service = GraphBuilderService()

    monkeypatch.setattr(service, "_wait_for_episodes", lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        service,
        "get_graph_data",
        lambda graph_id: {
            "graph_id": graph_id,
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
        },
    )
    monkeypatch.setattr(service.client, "get_episodes", lambda *args, **kwargs: [])
    monkeypatch.setattr("app.services.graph_builder.time.sleep", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="nao materializou dados"):
        service.wait_for_graph_materialization("graph_x")


def test_wait_for_graph_materialization_accepts_populated_graph(monkeypatch):
    service = GraphBuilderService()

    monkeypatch.setattr(service, "_wait_for_episodes", lambda *args, **kwargs: 2)
    monkeypatch.setattr(service.client, "get_episodes", lambda *args, **kwargs: [{"id": "ep1"}])
    monkeypatch.setattr("app.services.graph_builder.time.sleep", lambda *_args, **_kwargs: None)

    responses = iter([
        {
            "graph_id": "graph_x",
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
        },
        {
            "graph_id": "graph_x",
            "nodes": [{"uuid": "n1"}],
            "edges": [{"uuid": "e1"}],
            "node_count": 1,
            "edge_count": 1,
        },
    ])
    monkeypatch.setattr(service, "get_graph_data", lambda graph_id: next(responses))

    result = service.wait_for_graph_materialization("graph_x")

    assert result["node_count"] == 1
    assert result["edge_count"] == 1
