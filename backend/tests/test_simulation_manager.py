"""Testes do contrato entre runner e estado mestre da simulacao."""
from __future__ import annotations

from app.services.simulation_manager import SimulationManager, SimulationState, SimulationStatus
from app.services.simulation_runner import RunnerStatus, SimulationRunState


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
