from app.services.ontology_generator import OntologyGenerator


class FakeLLMClient:
    def chat_json(self, **_kwargs):
        return {
            "entity_types": [
                {
                    "name": "AtorPolitico",
                    "description": "Ator politico diretamente envolvido.",
                    "attributes": [{"name": "papel", "type": "text", "description": "Papel"}],
                    "examples": ["prefeito"],
                }
            ],
            "edge_types": [
                {
                    "name": "INFLUENCIA",
                    "description": "Influencia decisao.",
                    "source_targets": [{"source": "AtorPolitico", "target": "Pessoa"}],
                    "attributes": [],
                }
            ],
            "analysis_summary": "Resumo.",
        }


def test_ontology_generator_expande_camadas_de_stakeholders():
    generator = OntologyGenerator(llm_client=FakeLLMClient())

    result = generator.generate(
        document_texts=["Crise publica com imprensa, regulador e comunidade afetada."],
        simulation_requirement="Simular reacao de stakeholders.",
    )

    names = [entity["name"] for entity in result["entity_types"]]

    assert 12 <= len(names) <= 24
    assert names[-2:] == ["Pessoa", "Organizacao"]
    assert "AtorPolitico" in names
    assert "StakeholderInstitucional" in names
    assert "OrgaoRegulador" in names
    assert len(result["edge_types"]) >= 8
