from __future__ import annotations

from flask import Flask

from app.api import graph as graph_api
from app.models.project import Project, ProjectStatus


def _project(project_id: str = "proj_json_ontology") -> Project:
    return Project(
        project_id=project_id,
        name="Teste",
        status=ProjectStatus.CREATED,
        created_at="2026-05-06T00:00:00",
        updated_at="2026-05-06T00:00:00",
    )


def test_generate_ontology_aceita_json_sem_arquivos(monkeypatch):
    app = Flask(__name__)
    project = _project()
    saved_text = {}
    saved_projects = []

    class FakeGenerator:
        def generate(self, document_texts, simulation_requirement, additional_context=None):
            saved_text["document_texts"] = document_texts
            saved_text["simulation_requirement"] = simulation_requirement
            saved_text["additional_context"] = additional_context
            return {
                "entity_types": [{"name": "Pessoa"}],
                "edge_types": [{"name": "INFLUENCIA", "source_type": "Pessoa", "target_type": "Pessoa"}],
                "analysis_summary": "Ontologia gerada a partir do objetivo.",
            }

    monkeypatch.setattr(graph_api.ProjectManager, "create_project", lambda name: project)
    monkeypatch.setattr(
        graph_api.ProjectManager,
        "save_extracted_text",
        lambda project_id, text: saved_text.__setitem__("extracted", text),
    )
    monkeypatch.setattr(
        graph_api.ProjectManager,
        "save_project",
        lambda item: saved_projects.append(item.to_dict()),
    )
    monkeypatch.setattr(graph_api, "OntologyGenerator", FakeGenerator)

    with app.test_request_context(
        "/api/graph/ontology/generate",
        method="POST",
        json={
            "simulation_requirement": "Simular julgamento e estrategia de defesa.",
            "additional_context": "Contexto complementar.",
        },
    ):
        response = graph_api.generate_ontology()

    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["project_id"] == "proj_json_ontology"
    assert data["data"]["ontology"]["entity_types"] == [{"name": "Pessoa"}]
    assert data["data"]["files"][0]["filename"] == "cenario_da_simulacao.txt"
    assert "Simular julgamento" in saved_text["extracted"]
    assert saved_text["simulation_requirement"] == "Simular julgamento e estrategia de defesa."
    assert saved_text["additional_context"] == "Contexto complementar."
    assert saved_projects[-1]["status"] == "ontology_generated"


def test_generate_ontology_json_sem_objetivo_retorna_400():
    app = Flask(__name__)

    with app.test_request_context(
        "/api/graph/ontology/generate",
        method="POST",
        json={"files": {}},
    ):
        response, status_code = graph_api.generate_ontology()

    assert status_code == 400
    assert response.get_json()["success"] is False
