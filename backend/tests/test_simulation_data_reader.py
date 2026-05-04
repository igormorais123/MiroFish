"""Testes de metricas locais de simulacao."""
from __future__ import annotations

import json
import sqlite3

from app.services.simulation_data_reader import SimulationDataReader


def _write_action(path, item):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def test_diversity_metrics_detecta_variedade_semantica_e_comportamental(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    sim_dir = uploads / "simulations" / "sim_test"
    twitter_dir = sim_dir / "twitter"
    reddit_dir = sim_dir / "reddit"
    twitter_dir.mkdir(parents=True)
    reddit_dir.mkdir(parents=True)

    (sim_dir / "simulation_config.json").write_text(
        json.dumps({
            "agent_configs": [
                {"agent_id": 1, "entity_type": "GeneralPublic"},
                {"agent_id": 2, "entity_type": "Hypester"},
            ]
        }),
        encoding="utf-8",
    )

    _write_action(twitter_dir / "actions.jsonl", {
        "agent_id": 1,
        "agent_name": "Ana",
        "action_type": "CREATE_POST",
        "action_args": {"content": "A proposta melhora transporte e reduz espera nas paradas"},
    })
    _write_action(twitter_dir / "actions.jsonl", {
        "agent_id": 2,
        "agent_name": "Bruno",
        "action_type": "REPOST",
        "action_args": {"content": "A crise cresce quando a resposta oficial demora"},
    })
    _write_action(reddit_dir / "actions.jsonl", {
        "agent_id": 1,
        "agent_name": "Ana",
        "action_type": "CREATE_COMMENT",
        "action_args": {"content": "Sem dado local a medida parece aposta"},
    })

    from app.config import Config
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(uploads))

    metrics = SimulationDataReader("sim_test").get_diversity_metrics()

    assert metrics["total_actions"] == 3
    assert metrics["generated_texts_count"] == 3
    assert metrics["action_type_entropy_norm"] > 0
    assert metrics["agent_activity_entropy_norm"] > 0
    assert metrics["distinct_2"] > 0.5
    assert metrics["entity_type_coverage"] == 2


def test_diversity_metrics_explica_simulacao_homogenea(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    sim_dir = uploads / "simulations" / "sim_flat" / "twitter"
    sim_dir.mkdir(parents=True)

    for index in range(3):
        _write_action(sim_dir / "actions.jsonl", {
            "agent_id": 1,
            "agent_name": "Ana",
            "action_type": "CREATE_POST",
            "action_args": {"content": "mesma frase repetida"},
        })

    from app.config import Config
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(uploads))

    metrics = SimulationDataReader("sim_flat").get_diversity_metrics()

    assert metrics["action_type_entropy_norm"] == 0.0
    assert metrics["agent_activity_entropy_norm"] == 0.0
    assert metrics["distinct_2"] < 0.5


def test_oasis_trace_metrics_detecta_interacoes_reais(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    sim_root = uploads / "simulations" / "sim_trace"
    sim_root.mkdir(parents=True)
    (sim_root / "simulation_config.json").write_text(
        json.dumps({"event_config": {"initial_posts": [{"content": "a"}, {"content": "b"}]}}),
        encoding="utf-8",
    )

    db_path = sim_root / "twitter_simulation.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE trace (user_id INTEGER, created_at TEXT, action TEXT, info TEXT)")
    cursor.executemany(
        "INSERT INTO trace VALUES (?, ?, ?, ?)",
        [
            (1, "1", "sign_up", "{}"),
            (1, "2", "create_post", '{"content":"a"}'),
            (2, "3", "create_post", '{"content":"b"}'),
            (3, "4", "like_post", '{"post_id":1}'),
            (4, "5", "create_comment", '{"post_id":1,"content":"discordo parcialmente"}'),
        ],
    )
    conn.commit()
    conn.close()

    from app.config import Config
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(uploads))

    metrics = SimulationDataReader("sim_trace").get_oasis_trace_metrics()

    assert metrics["db_files_found"] == 1
    assert metrics["expected_initial_posts_total"] == 2
    assert metrics["dynamic_create_posts_estimate"] == 0
    assert metrics["interactive_actions_total"] == 2
    assert metrics["behavioral_entropy_norm"] > 0
