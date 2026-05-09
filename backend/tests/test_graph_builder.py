import pytest

from app.services.graph_builder import GraphBuilderService


def test_wait_for_graph_materialization_returns_empty_gracefully(monkeypatch):
    """Quando o grafo nao materializa, retorna os dados vazios (degradacao graciosa)."""
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

    result = service.wait_for_graph_materialization("graph_x")
    assert result["node_count"] == 0
    assert result["edge_count"] == 0


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


def test_schema_fallback_graph_persiste_dados_locais(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.graph_builder.LOCAL_GRAPH_DIR", str(tmp_path))
    service = GraphBuilderService()

    graph_data = service.build_schema_fallback_graph(
        text="Texto do caso",
        ontology={
            "entity_types": [
                {"name": "Pessoa", "description": "Pessoa fisica", "examples": ["Maria"]},
                {"name": "Organizacao", "description": "Organizacao", "examples": ["ONG"]},
            ],
            "edge_types": [
                {
                    "name": "INFLUENCIA",
                    "description": "Influencia",
                    "source_targets": [{"source": "Pessoa", "target": "Organizacao"}],
                }
            ],
        },
        graph_name="Fallback",
        unavailable_reason="NameResolutionError graphiti",
    )

    loaded = service.get_graph_data(graph_data["graph_id"])

    assert loaded["graph_backend"] == "local_fallback"
    assert loaded["unavailable"] is True
    assert loaded["node_count"] == 2
    assert loaded["edge_count"] == 1
