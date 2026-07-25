"""Testes do cache incremental e do delta de acoes do SimulationRunner."""

import json
import os

import pytest

from app.services.simulation_runner import SimulationRunner


def _write_action(path, round_num, agent_id, action_type="CREATE_POST", timestamp=None):
    """Acrescenta uma acao ao log, como o simulador faz."""
    record = {
        "round": round_num,
        "timestamp": timestamp or f"2026-01-01T10:{agent_id:02d}:00",
        "agent_id": agent_id,
        "agent_name": f"Agent {agent_id}",
        "action_type": action_type,
        "action_args": {"content": "x"},
        "success": True,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


@pytest.fixture
def sim_dir(tmp_path, monkeypatch):
    """Isola o diretorio de runs e limpa o cache entre testes."""
    sim_id = "sim_delta_test"
    run_dir = tmp_path / sim_id
    (run_dir / "twitter").mkdir(parents=True)
    (run_dir / "reddit").mkdir(parents=True)

    monkeypatch.setattr(
        SimulationRunner, "_get_run_dir", classmethod(lambda cls, _id: str(tmp_path / _id))
    )
    SimulationRunner.invalidate_actions_cache()
    yield sim_id, run_dir
    SimulationRunner.invalidate_actions_cache()


def test_delta_retorna_apenas_acoes_novas(sim_dir):
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    _write_action(twitter_log, 1, 1)
    _write_action(twitter_log, 1, 2)

    first = SimulationRunner.get_actions_delta(sim_id)
    assert len(first["actions"]) == 2
    assert first["cursor"]["twitter"] == 2
    assert first["total"] == 2

    # Nada novo: delta vazio, cursor estavel.
    second = SimulationRunner.get_actions_delta(sim_id, cursor=first["cursor"])
    assert second["actions"] == []
    assert second["cursor"]["twitter"] == 2

    _write_action(twitter_log, 2, 3)
    third = SimulationRunner.get_actions_delta(sim_id, cursor=second["cursor"])
    assert len(third["actions"]) == 1
    assert third["actions"][0].agent_id == 3
    assert third["cursor"]["twitter"] == 3


def test_delta_ordena_cronologicamente_ascendente(sim_dir):
    """A timeline acrescenta no fim: o mais recente precisa vir por ultimo."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")
    reddit_log = str(run_dir / "reddit" / "actions.jsonl")

    _write_action(twitter_log, 1, 1, timestamp="2026-01-01T10:00:00")
    _write_action(reddit_log, 1, 2, timestamp="2026-01-01T10:00:30")
    _write_action(twitter_log, 2, 3, timestamp="2026-01-01T10:01:00")

    result = SimulationRunner.get_actions_delta(sim_id)
    timestamps = [action.timestamp for action in result["actions"]]

    assert timestamps == sorted(timestamps)
    assert result["actions"][-1].agent_id == 3


def test_cursor_por_plataforma_nao_perde_acoes_intercaladas(sim_dir):
    """Twitter e Reddit crescem independentes; um indice unico perderia eventos."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")
    reddit_log = str(run_dir / "reddit" / "actions.jsonl")

    _write_action(twitter_log, 1, 1, timestamp="2026-01-01T10:00:00")
    first = SimulationRunner.get_actions_delta(sim_id)

    # Reddit escreve um evento ANTERIOR ao ja entregue (chegada fora de ordem).
    _write_action(reddit_log, 1, 2, timestamp="2026-01-01T09:59:00")
    second = SimulationRunner.get_actions_delta(sim_id, cursor=first["cursor"])

    assert len(second["actions"]) == 1
    assert second["actions"][0].agent_id == 2


def test_linha_parcial_nao_e_consumida(sim_dir):
    """O simulador pode estar no meio de uma escrita; a linha entra na proxima leitura."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    _write_action(twitter_log, 1, 1)
    with open(twitter_log, "a", encoding="utf-8") as f:
        f.write('{"round": 2, "agent_id": 2, "action_ty')  # sem newline

    first = SimulationRunner.get_actions_delta(sim_id)
    assert len(first["actions"]) == 1

    # Escrita concluida: agora a acao aparece.
    with open(twitter_log, "a", encoding="utf-8") as f:
        f.write('pe": "LIKE_POST", "timestamp": "2026-01-01T10:05:00", '
                '"agent_name": "Agent 2", "action_args": {}, "success": true}\n')

    second = SimulationRunner.get_actions_delta(sim_id, cursor=first["cursor"])
    assert len(second["actions"]) == 1
    assert second["actions"][0].agent_id == 2


def test_cache_invalida_quando_arquivo_encolhe(sim_dir):
    """Restart com force reescreve o log; servir o parse antigo mostraria run morta."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    for agent_id in range(1, 6):
        _write_action(twitter_log, 1, agent_id)
    assert SimulationRunner.get_actions_delta(sim_id)["total"] == 5

    # Log reescrito do zero, menor que antes.
    with open(twitter_log, "w", encoding="utf-8") as f:
        f.write("")
    _write_action(twitter_log, 1, 9)

    result = SimulationRunner.get_actions_delta(sim_id)
    assert result["total"] == 1
    assert result["actions"][0].agent_id == 9


def test_primeira_carga_limita_cauda(sim_dir):
    """Sem cursor, so a cauda recente viaja: o cliente nao renderiza o historico inteiro."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    for agent_id in range(1, 31):
        _write_action(twitter_log, 1, agent_id, timestamp=f"2026-01-01T10:{agent_id:02d}:00")

    result = SimulationRunner.get_actions_delta(sim_id, initial_limit=10)

    assert len(result["actions"]) == 10
    assert result["total"] == 30
    assert result["cursor"]["twitter"] == 30
    # A cauda e a parte recente, nao o comeco da run.
    assert result["actions"][-1].agent_id == 30


def test_leitura_incremental_nao_reparseia_o_arquivo(sim_dir, monkeypatch):
    """O ganho do cache: linhas ja lidas nao voltam ao parser."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")

    for agent_id in range(1, 21):
        _write_action(twitter_log, 1, agent_id)
    SimulationRunner.get_actions_delta(sim_id)

    parsed_lines = []
    original = SimulationRunner._action_from_line

    def counting_parser(line, default_platform):
        parsed_lines.append(line)
        return original(line, default_platform)

    monkeypatch.setattr(SimulationRunner, "_action_from_line", staticmethod(counting_parser))

    _write_action(twitter_log, 2, 21)
    SimulationRunner.get_actions_delta(sim_id)

    assert len(parsed_lines) == 1


def test_filtros_continuam_validos_sobre_o_cache(sim_dir):
    """get_all_actions mantem contrato (desc) mesmo lendo do cache."""
    sim_id, run_dir = sim_dir
    twitter_log = str(run_dir / "twitter" / "actions.jsonl")
    reddit_log = str(run_dir / "reddit" / "actions.jsonl")

    _write_action(twitter_log, 1, 1, timestamp="2026-01-01T10:00:00")
    _write_action(reddit_log, 2, 2, timestamp="2026-01-01T10:02:00")
    _write_action(twitter_log, 3, 3, timestamp="2026-01-01T10:03:00")

    todas = SimulationRunner.get_all_actions(sim_id)
    assert [a.agent_id for a in todas] == [3, 2, 1]  # recentes primeiro

    so_twitter = SimulationRunner.get_all_actions(sim_id, platform="twitter")
    assert {a.agent_id for a in so_twitter} == {1, 3}

    rodada_3 = SimulationRunner.get_all_actions(sim_id, round_num=3)
    assert [a.agent_id for a in rodada_3] == [3]
