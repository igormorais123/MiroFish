"""Testes do copiloto operacional da simulacao."""

import json
import os
from datetime import datetime, timedelta

import pytest

from app.services import simulation_copilot
from app.services.simulation_copilot import answer_operator_question, build_pulse
from app.services.simulation_runner import RunnerStatus, SimulationRunner, SimulationRunState


def _write_action(path, round_num, agent_id, action_type="CREATE_POST",
                  timestamp=None, success=True, content="texto"):
    record = {
        "round": round_num,
        "timestamp": (timestamp or datetime.now()).isoformat(),
        "agent_id": agent_id,
        "agent_name": f"Agent {agent_id}",
        "action_type": action_type,
        "action_args": {"content": content},
        "success": success,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


@pytest.fixture
def sim(tmp_path, monkeypatch):
    """Simulacao isolada com estado controlado, sem tocar disco real de runs."""
    sim_id = "sim_copilot_test"
    run_dir = tmp_path / sim_id
    (run_dir / "twitter").mkdir(parents=True)
    (run_dir / "reddit").mkdir(parents=True)

    monkeypatch.setattr(
        SimulationRunner, "_get_run_dir", classmethod(lambda cls, _id: str(tmp_path / _id))
    )
    SimulationRunner.invalidate_actions_cache()

    state = SimulationRunState(
        simulation_id=sim_id,
        runner_status=RunnerStatus.RUNNING,
        current_round=12,
        total_rounds=144,
        twitter_running=True,
        reddit_running=True,
    )
    monkeypatch.setattr(
        SimulationRunner, "get_run_state", classmethod(lambda cls, _id: state)
    )

    yield sim_id, run_dir, state
    SimulationRunner.invalidate_actions_cache()


def test_pulse_sem_simulacao_nao_quebra(monkeypatch):
    monkeypatch.setattr(SimulationRunner, "get_run_state", classmethod(lambda cls, _id: None))

    pulse = build_pulse("sim_inexistente")

    assert pulse["runner_status"] == "idle"
    assert pulse["alerts"] == []
    assert "Nenhuma simulação" in pulse["headline"]


def test_pulse_resume_atividade_corrente(sim):
    sim_id, run_dir, _ = sim
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")
    reddit_log = str(run_dir / "reddit" / "actions.jsonl")

    now = datetime.now()
    for i in range(10):
        _write_action(twitter_log, 12, i, timestamp=now - timedelta(seconds=60 - i))
    for i in range(10, 15):
        _write_action(reddit_log, 12, i, action_type="LIKE_POST",
                      timestamp=now - timedelta(seconds=60 - i))

    pulse = build_pulse(sim_id)

    assert pulse["runner_status"] == RunnerStatus.RUNNING
    assert pulse["progress"]["current_round"] == 12
    assert pulse["progress"]["progress_percent"] == round(12 / 144 * 100, 1)
    assert pulse["activity"]["actions_total"] == 15
    assert pulse["activity"]["distinct_agents_in_window"] == 15
    assert pulse["activity"]["by_platform"] == {"twitter": 10, "reddit": 5}
    assert pulse["activity"]["by_action_type"]["CREATE_POST"] == 10


def test_alerta_de_simulacao_travada(sim):
    """Runner diz que roda, mas nada e escrito ha muito tempo."""
    sim_id, run_dir, _ = sim
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    stale = datetime.now() - timedelta(seconds=simulation_copilot.STALL_SECONDS + 120)
    _write_action(twitter_log, 12, 1, timestamp=stale)

    pulse = build_pulse(sim_id)
    codes = [alert["code"] for alert in pulse["alerts"]]

    assert "stalled" in codes
    assert pulse["alerts"][0]["severity"] == "critical"
    assert "travou" in pulse["headline"]


def test_alerta_de_taxa_de_falha(sim):
    sim_id, run_dir, _ = sim
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    now = datetime.now()
    for i in range(10):
        _write_action(twitter_log, 12, i, success=(i >= 6), timestamp=now - timedelta(seconds=10 - i))

    pulse = build_pulse(sim_id)
    codes = [alert["code"] for alert in pulse["alerts"]]

    assert "high_failure_rate" in codes
    assert pulse["activity"]["failures_in_window"] == 6


def test_alerta_de_colapso_de_comportamento(sim):
    """Toda a populacao fazendo a mesma coisa deixou de gerar variacao util."""
    sim_id, run_dir, _ = sim
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    now = datetime.now()
    for i in range(30):
        _write_action(twitter_log, 12, i, action_type="LIKE_POST",
                      timestamp=now - timedelta(seconds=30 - i))

    pulse = build_pulse(sim_id)
    codes = [alert["code"] for alert in pulse["alerts"]]

    assert "behavior_collapse" in codes


def test_diversidade_saudavel_nao_gera_alerta(sim):
    sim_id, run_dir, _ = sim
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    now = datetime.now()
    types = ["CREATE_POST", "LIKE_POST", "REPOST", "CREATE_COMMENT"]
    for i in range(40):
        _write_action(twitter_log, 12, i, action_type=types[i % len(types)],
                      timestamp=now - timedelta(seconds=40 - i))

    pulse = build_pulse(sim_id)

    assert pulse["alerts"] == []
    assert "Rodada 12" in pulse["headline"]


def test_alerta_de_plataforma_silenciosa(sim):
    sim_id, run_dir, state = sim
    state.reddit_running = False
    state.reddit_completed = False

    twitter_log = str(run_dir / "twitter" / "actions.jsonl")
    _write_action(twitter_log, 12, 1, timestamp=datetime.now())

    pulse = build_pulse(sim_id)
    codes = [alert["code"] for alert in pulse["alerts"]]

    assert "platform_silent" in codes


def test_plataforma_concluida_nao_gera_alerta(sim):
    """Plataforma que terminou nao e plataforma morta."""
    sim_id, run_dir, state = sim
    state.reddit_running = False
    state.reddit_completed = True

    twitter_log = str(run_dir / "twitter" / "actions.jsonl")
    _write_action(twitter_log, 12, 1, timestamp=datetime.now())

    pulse = build_pulse(sim_id)
    codes = [alert["code"] for alert in pulse["alerts"]]

    assert "platform_silent" not in codes


def test_resposta_do_copiloto_recebe_estado_real_no_prompt(sim):
    """A resposta precisa ser ancorada no estado, nao em generalidade."""
    sim_id, run_dir, _ = sim
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    now = datetime.now()
    for i in range(5):
        _write_action(twitter_log, 12, i, content=f"conteudo {i}",
                      timestamp=now - timedelta(seconds=5 - i))

    captured = {}

    class FakeLLM:
        def chat(self, messages, **kwargs):
            captured["messages"] = messages
            return "  O ritmo esta estavel.  "

    result = answer_operator_question(
        simulation_id=sim_id,
        question="como esta o ritmo?",
        simulation_requirement="testar reacao a uma proposta",
        llm_client=FakeLLM(),
    )

    system_prompt = captured["messages"][0]["content"]
    assert "Rodada: 12 de 144" in system_prompt
    assert "testar reacao a uma proposta" in system_prompt
    assert "conteudo 4" in system_prompt  # amostra real das acoes
    assert captured["messages"][-1]["content"] == "como esta o ritmo?"

    assert result["response"] == "O ritmo esta estavel."
    assert result["pulse"]["progress"]["current_round"] == 12


def test_historico_do_operador_entra_limitado(sim):
    sim_id, _, _ = sim
    captured = {}

    class FakeLLM:
        def chat(self, messages, **kwargs):
            captured["messages"] = messages
            return "ok"

    history = [{"role": "user", "content": f"pergunta {i}"} for i in range(20)]

    answer_operator_question(
        simulation_id=sim_id,
        question="e agora?",
        chat_history=history,
        llm_client=FakeLLM(),
    )

    # system + 6 turnos de historico + pergunta atual
    assert len(captured["messages"]) == 8
    assert captured["messages"][1]["content"] == "pergunta 14"
