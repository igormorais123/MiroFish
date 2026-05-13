"""Testes da integracao de eleitores sinteticos de Sergipe."""
from __future__ import annotations

import json

from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.sergipe_synthetic_voters import (
    SERGIPE_SYNTHETIC_VOTER_TYPE,
    SergipeSyntheticVoterRepository,
    augment_entities_for_sergipe_context,
    is_sergipe_research_context,
)
from app.services.simulation_config_generator import SimulationConfigGenerator
from app.services.zep_entity_reader import EntityNode, FilteredEntities


def _sample_voter() -> dict:
    return {
        "id": "se-0001",
        "nome": "Antonio Campos Farias",
        "idade": 37,
        "genero": "masculino",
        "municipio": "Simao Dias",
        "mesorregiao": "Agreste",
        "zona_residencia": "rural",
        "classe_social": "media",
        "profissao": "Mecanico(a)",
        "religiao": "catolica",
        "orientacao_politica": "centro_esquerda",
        "interesse_politico": "baixo",
        "preocupacoes": ["Saude publica", "Aposentadoria e INSS"],
        "fontes_informacao": ["Boca a boca", "Radio Cultura Itabaiana"],
        "valores": ["Fe", "Igualdade"],
        "historia_resumida": (
            "Sou Antonio, tenho 37 anos e moro em Simao Dias, Sergipe."
        ),
        "instrucao_comportamental": (
            "Tom: indiferente. Registro: popular, frases curtas."
        ),
        "voto_2t_2022": "Lula",
        "intencao_voto_2026_gov": "Rogerio",
        "intencao_voto_2026_pres": "Lula",
        "prob_lula_empirica": 0.714,
        "consumo_midia": {"fonte_principal_noticias": "tv"},
    }


def test_detecta_contexto_de_pesquisa_relacionada_a_sergipe():
    assert is_sergipe_research_context(
        "Pesquisa eleitoral em Sergipe sobre governo 2026",
        "",
    )
    assert is_sergipe_research_context(
        "Medir percepcao local",
        "Amostra com Aracaju, Itabaiana e interior.",
    )
    assert not is_sergipe_research_context(
        "Pesquisa eleitoral em Sao Paulo",
        "Sem recorte local.",
    )


def test_repositorio_converte_eleitores_para_entidades(tmp_path):
    data_path = tmp_path / "eleitores.json"
    data_path.write_text(json.dumps([_sample_voter()]), encoding="utf-8")

    entities = SergipeSyntheticVoterRepository(data_path=data_path).load_entities()

    assert len(entities) == 1
    entity = entities[0]
    assert entity.uuid == "sergipe-voter-se-0001"
    assert entity.name == "Antonio Campos Farias"
    assert entity.get_entity_type() == SERGIPE_SYNTHETIC_VOTER_TYPE
    assert "Simao Dias" in entity.summary
    assert "Sergipe" in entity.summary
    assert entity.attributes["synthetic_voter_source"] == "sergipe_eleitores_1000_v9"


def test_base_embutida_de_sergipe_tem_1000_eleitores():
    voters = SergipeSyntheticVoterRepository().load_raw_voters()

    assert len(voters) == 1000
    assert voters[0]["id"] == "se-0001"
    assert voters[-1]["id"] == "se-1000"


def test_augmentacao_aplica_eleitores_sinteticos_sem_duplicar(tmp_path):
    data_path = tmp_path / "eleitores.json"
    data_path.write_text(json.dumps([_sample_voter()]), encoding="utf-8")
    repository = SergipeSyntheticVoterRepository(data_path=data_path)
    existing = EntityNode(
        uuid="entity-1",
        name="Universidade Federal de Sergipe",
        labels=["Entity", "University"],
        summary="Instituicao local.",
        attributes={},
    )
    filtered = FilteredEntities(
        entities=[existing],
        entity_types={"University"},
        total_count=1,
        filtered_count=1,
    )

    result = augment_entities_for_sergipe_context(
        filtered,
        simulation_requirement="Pesquisa em Sergipe",
        document_text="",
        repository=repository,
    )
    result_again = augment_entities_for_sergipe_context(
        result.filtered,
        simulation_requirement="Pesquisa em Sergipe",
        document_text="",
        repository=repository,
    )

    assert result.applied is True
    assert result.added_count == 1
    assert result.filtered.filtered_count == 2
    assert SERGIPE_SYNTHETIC_VOTER_TYPE in result.filtered.entity_types
    assert result_again.added_count == 0
    assert result_again.filtered.filtered_count == 2


def test_oasis_profile_usa_eleitor_sintetico_sem_llm():
    entity = SergipeSyntheticVoterRepository(voters=[_sample_voter()]).load_entities()[0]
    generator = object.__new__(OasisProfileGenerator)

    profile = generator.generate_profile_from_entity(
        entity=entity,
        user_id=7,
        use_llm=True,
    )

    assert profile.user_id == 7
    assert profile.user_name == "se_0001_antonio_campos_farias"
    assert profile.age == 37
    assert profile.gender == "male"
    assert profile.country == "Brazil"
    assert profile.profession == "Mecanico(a)"
    assert "Simao Dias" in profile.persona
    assert "Rogerio" in profile.persona
    assert "Saude publica" in profile.interested_topics


def test_config_de_agentes_sinteticos_usa_regras_sem_llm():
    entity = SergipeSyntheticVoterRepository(voters=[_sample_voter()]).load_entities()[0]
    generator = object.__new__(SimulationConfigGenerator)
    generator._call_llm_with_retry = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("LLM nao deve ser chamado para eleitores sinteticos")
    )

    configs = generator._generate_agent_configs_batch(
        context="",
        entities=[entity],
        start_idx=5,
        simulation_requirement="Pesquisa eleitoral em Sergipe",
    )

    assert len(configs) == 1
    assert configs[0].agent_id == 5
    assert configs[0].entity_type == SERGIPE_SYNTHETIC_VOTER_TYPE
    assert configs[0].active_hours
