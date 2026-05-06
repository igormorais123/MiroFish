"""Regressoes de reconciliacao do estado auditavel da simulacao."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.simulation_runner import RunnerStatus, SimulationRunner


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_get_run_state_reconcilia_stopped_quando_logs_indicam_fim(tmp_path, monkeypatch):
    simulation_id = "sim_reconcile"
    sim_dir = tmp_path / simulation_id
    sim_dir.mkdir(parents=True)
    monkeypatch.setattr(SimulationRunner, "RUN_STATE_DIR", str(tmp_path))
    SimulationRunner._run_states.pop(simulation_id, None)

    (sim_dir / "run_state.json").write_text(
        json.dumps(
            {
                "simulation_id": simulation_id,
                "runner_status": "stopped",
                "current_round": 0,
                "total_rounds": 72,
                "twitter_current_round": 0,
                "reddit_current_round": 0,
                "twitter_completed": False,
                "reddit_completed": False,
                "twitter_actions_count": 0,
                "reddit_actions_count": 0,
                "twitter_running": False,
                "reddit_running": False,
                "error": "estado antigo parado",
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        sim_dir / "twitter" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 1, "agent_name": "A", "round": 72, "action_type": "CREATE_POST"},
            {"agent_id": 2, "agent_name": "B", "round": 72, "action_type": "LIKE_POST"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 2},
        ],
    )
    write_jsonl(
        sim_dir / "reddit" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 3, "agent_name": "C", "round": 72, "action_type": "CREATE_COMMENT"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 1},
        ],
    )

    state = SimulationRunner.get_run_state(simulation_id)

    assert state is not None
    assert state.runner_status == RunnerStatus.COMPLETED
    assert state.current_round == 72
    assert state.twitter_current_round == 72
    assert state.reddit_current_round == 72
    assert state.twitter_completed is True
    assert state.reddit_completed is True
    assert state.twitter_actions_count == 2
    assert state.reddit_actions_count == 1
    assert state.error is None


def test_get_run_state_nao_promove_stopped_sem_eventos_de_fim(tmp_path, monkeypatch):
    simulation_id = "sim_incomplete"
    sim_dir = tmp_path / simulation_id
    sim_dir.mkdir(parents=True)
    monkeypatch.setattr(SimulationRunner, "RUN_STATE_DIR", str(tmp_path))
    SimulationRunner._run_states.pop(simulation_id, None)

    (sim_dir / "run_state.json").write_text(
        json.dumps(
            {
                "simulation_id": simulation_id,
                "runner_status": "stopped",
                "current_round": 12,
                "total_rounds": 72,
                "twitter_completed": False,
                "reddit_completed": False,
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        sim_dir / "twitter" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 12, "simulated_hours": 12},
            {"agent_id": 1, "agent_name": "A", "round": 12, "action_type": "CREATE_POST"},
        ],
    )

    state = SimulationRunner.get_run_state(simulation_id)

    assert state is not None
    assert state.runner_status == RunnerStatus.STOPPED
    assert state.current_round == 12
    assert state.twitter_completed is False


def test_get_run_state_reconstroi_estado_quando_run_state_sumiu(tmp_path, monkeypatch):
    simulation_id = "sim_missing_state"
    sim_dir = tmp_path / simulation_id
    sim_dir.mkdir(parents=True)
    monkeypatch.setattr(SimulationRunner, "RUN_STATE_DIR", str(tmp_path))
    SimulationRunner._run_states.pop(simulation_id, None)

    (sim_dir / "simulation_config.json").write_text(
        json.dumps({"time_config": {"total_simulation_hours": 72, "minutes_per_round": 60}}),
        encoding="utf-8",
    )
    write_jsonl(
        sim_dir / "twitter" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 1, "agent_name": "A", "round": 72, "action_type": "CREATE_POST"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 1},
        ],
    )
    write_jsonl(
        sim_dir / "reddit" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 2, "agent_name": "B", "round": 72, "action_type": "CREATE_COMMENT"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 1},
        ],
    )

    state = SimulationRunner.get_run_state(simulation_id)

    assert state is not None
    assert state.runner_status == RunnerStatus.COMPLETED
    assert state.total_rounds == 72
    assert state.current_round == 72
    assert state.twitter_actions_count == 1
    assert state.reddit_actions_count == 1


def test_get_run_state_ignora_numeros_invalidos_no_log_auditavel(tmp_path, monkeypatch):
    simulation_id = "sim_malformed_log"
    sim_dir = tmp_path / simulation_id
    sim_dir.mkdir(parents=True)
    monkeypatch.setattr(SimulationRunner, "RUN_STATE_DIR", str(tmp_path))
    SimulationRunner._run_states.pop(simulation_id, None)

    (sim_dir / "run_state.json").write_text(
        json.dumps(
            {
                "simulation_id": simulation_id,
                "runner_status": "stopped",
                "current_round": 0,
                "total_rounds": 72,
                "twitter_completed": False,
                "reddit_completed": False,
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        sim_dir / "twitter" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": "nao-numero", "simulated_hours": "??"},
            {"agent_id": 1, "agent_name": "A", "round": "72", "action_type": "CREATE_POST"},
            {"event_type": "simulation_end", "total_rounds": "72", "total_actions": "x"},
        ],
    )
    write_jsonl(
        sim_dir / "reddit" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 2, "agent_name": "B", "round": 72, "action_type": "CREATE_COMMENT"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 1},
        ],
    )

    state = SimulationRunner.get_run_state(simulation_id)

    assert state is not None
    assert state.runner_status == RunnerStatus.COMPLETED
    assert state.twitter_current_round == 72
    assert state.twitter_actions_count == 1
    assert state.error is None


def test_cleanup_all_nao_sobrescreve_conclusao_auditavel_com_stopped(tmp_path, monkeypatch):
    simulation_id = "sim_cleanup_completed"
    sim_dir = tmp_path / simulation_id
    sim_dir.mkdir(parents=True)
    monkeypatch.setattr(SimulationRunner, "RUN_STATE_DIR", str(tmp_path))
    SimulationRunner._run_states.pop(simulation_id, None)
    SimulationRunner._processes.clear()
    SimulationRunner._action_queues.clear()
    SimulationRunner._stdout_files.clear()
    SimulationRunner._stderr_files.clear()
    SimulationRunner._graph_memory_enabled.clear()
    monkeypatch.setattr(SimulationRunner, "_cleanup_done", False)

    (sim_dir / "run_state.json").write_text(
        json.dumps(
            {
                "simulation_id": simulation_id,
                "runner_status": "running",
                "current_round": 0,
                "total_rounds": 72,
                "twitter_running": True,
                "reddit_running": True,
                "twitter_completed": False,
                "reddit_completed": False,
            }
        ),
        encoding="utf-8",
    )
    (sim_dir / "state.json").write_text(
        json.dumps(
            {
                "simulation_id": simulation_id,
                "project_id": "proj_test",
                "graph_id": "graph_test",
                "status": "running",
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        sim_dir / "twitter" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 1, "agent_name": "A", "round": 72, "action_type": "CREATE_POST"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 1},
        ],
    )
    write_jsonl(
        sim_dir / "reddit" / "actions.jsonl",
        [
            {"event_type": "round_end", "round": 72, "simulated_hours": 72},
            {"agent_id": 2, "agent_name": "B", "round": 72, "action_type": "CREATE_COMMENT"},
            {"event_type": "simulation_end", "total_rounds": 72, "total_actions": 1},
        ],
    )

    class FakeProcess:
        pid = 12345

        def poll(self):
            return None

    SimulationRunner._processes[simulation_id] = FakeProcess()
    monkeypatch.setattr(SimulationRunner, "_terminate_process", lambda *args, **kwargs: None)

    SimulationRunner.cleanup_all_simulations()

    run_state_data = json.loads((sim_dir / "run_state.json").read_text(encoding="utf-8"))
    state_data = json.loads((sim_dir / "state.json").read_text(encoding="utf-8"))

    assert run_state_data["runner_status"] == "completed"
    assert run_state_data["twitter_completed"] is True
    assert run_state_data["reddit_completed"] is True
    assert run_state_data.get("error") is None
    assert state_data["status"] == "completed"
