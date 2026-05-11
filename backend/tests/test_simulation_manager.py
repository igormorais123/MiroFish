"""Testes do contrato entre runner e estado mestre da simulacao."""
from __future__ import annotations

import json

from app.services import simulation_manager as simulation_manager_module
from app.services.simulation_manager import SimulationManager, SimulationState, SimulationStatus
from app.services.simulation_config_generator import SimulationParameters
from app.services.simulation_runner import RunnerStatus, SimulationRunState
from app.services.zep_entity_reader import EntityNode, FilteredEntities


def test_apply_runner_status_consolida_status_completed(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "simulations"))

    manager = SimulationManager()
    state = SimulationState(
        simulation_id="sim_sync",
        project_id="proj_1",
        graph_id="graph_1",
        enable_twitter=True,
        enable_reddit=False,
        status=SimulationStatus.RUNNING,
    )
    manager._save_simulation_state(state)

    run_state = SimulationRunState(
        simulation_id="sim_sync",
        runner_status=RunnerStatus.COMPLETED,
        current_round=7,
        twitter_completed=True,
        reddit_completed=False,
    )

    updated = manager.apply_runner_status("sim_sync", run_state)

    assert updated is not None
    assert updated.status == SimulationStatus.COMPLETED
    assert updated.current_round == 7
    assert updated.twitter_status == "completed"
    assert updated.reddit_status == "disabled"

    reloaded = manager.get_simulation("sim_sync")
    assert reloaded.status == SimulationStatus.COMPLETED


def test_apply_runner_status_preserva_erro_em_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "simulations"))

    manager = SimulationManager()
    manager._save_simulation_state(SimulationState(
        simulation_id="sim_failed",
        project_id="proj_1",
        graph_id="graph_1",
        status=SimulationStatus.RUNNING,
    ))

    run_state = SimulationRunState(
        simulation_id="sim_failed",
        runner_status=RunnerStatus.FAILED,
        error="falha controlada",
    )

    updated = manager.apply_runner_status("sim_failed", run_state)

    assert updated.status == SimulationStatus.FAILED
    assert updated.twitter_status == "failed"
    assert updated.reddit_status == "failed"
    assert updated.error == "falha controlada"


def test_list_simulations_respeita_limite_e_ordem_recente(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "simulations"))

    manager = SimulationManager()
    for index in range(4):
        manager._save_simulation_state(SimulationState(
            simulation_id=f"sim_{index}",
            project_id="proj_1",
            graph_id="graph_1",
            created_at=f"2026-05-0{index + 1}T00:00:00",
            updated_at=f"2026-05-0{index + 1}T00:00:00",
        ))

    simulations = manager.list_simulations(limit=2)

    assert [simulation.simulation_id for simulation in simulations] == ["sim_3", "sim_2"]


def test_prepare_simulation_limpa_erro_antigo_apos_sucesso(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "simulations"))

    entity = EntityNode(
        uuid="entity_1",
        name="Igor",
        labels=["Entity", "Pessoa"],
        summary="Participante da simulacao",
        attributes={},
    )

    class FakeReader:
        def filter_defined_entities(self, **kwargs):
            return FilteredEntities(
                entities=[entity],
                entity_types={"Pessoa"},
                total_count=1,
                filtered_count=1,
            )

    class FakeProfileGenerator:
        def __init__(self, **kwargs):
            pass

        def generate_profiles_from_entities(self, **kwargs):
            return [{"user_id": 1, "username": "igor"}]

        def save_profiles(self, profiles, file_path, platform):
            if platform == "reddit":
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(profiles, file)
            else:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write("user_id,username\n1,igor\n")

    class FakeConfigGenerator:
        def generate_config(self, **kwargs):
            return SimulationParameters(
                simulation_id=kwargs["simulation_id"],
                project_id=kwargs["project_id"],
                graph_id=kwargs["graph_id"],
                simulation_requirement=kwargs["simulation_requirement"],
                generation_reasoning="config de teste",
            )

    monkeypatch.setattr(simulation_manager_module, "ZepEntityReader", FakeReader)
    monkeypatch.setattr(simulation_manager_module, "OasisProfileGenerator", FakeProfileGenerator)
    monkeypatch.setattr(simulation_manager_module, "SimulationConfigGenerator", FakeConfigGenerator)

    manager = SimulationManager()
    manager._save_simulation_state(SimulationState(
        simulation_id="sim_retry",
        project_id="proj_1",
        graph_id="graph_1",
        status=SimulationStatus.FAILED,
        error="Nenhuma entidade encontrada, verifique se o grafo foi construido corretamente",
    ))

    updated = manager.prepare_simulation(
        simulation_id="sim_retry",
        simulation_requirement="simular tema",
        document_text="contexto com entidade Igor",
    )

    assert updated.status == SimulationStatus.READY
    assert updated.entities_count == 1
    assert updated.config_generated is True
    assert updated.error is None

    reloaded = manager.get_simulation("sim_retry")
    assert reloaded.error is None
