from app.services.social_bootstrap import (
    build_social_bootstrap_plan,
    get_social_bootstrap_target,
)


def _config():
    return {
        "agent_configs": [
            {"agent_id": 1, "activity_level": 0.4, "influence_weight": 1.0},
            {"agent_id": 2, "activity_level": 0.9, "influence_weight": 2.0},
            {"agent_id": 3, "activity_level": 0.7, "influence_weight": 1.5},
            {"agent_id": 4, "activity_level": 0.3, "influence_weight": 0.5},
        ],
        "social_dynamics": {
            "bootstrap_max_actions": 3,
        },
    }


def test_bootstrap_reddit_planeja_interacoes_contra_posts_de_outros_agentes():
    plan = build_social_bootstrap_plan(
        _config(),
        "reddit",
        [
            {"post_id": 10, "agent_id": 1, "content": "post A"},
            {"post_id": 20, "agent_id": 2, "content": "post B"},
        ],
    )

    assert len(plan) == 3
    assert {item["action_type"] for item in plan} == {
        "CREATE_COMMENT",
        "LIKE_POST",
        "DISLIKE_POST",
    }
    assert all(item["agent_id"] != item["target_agent_id"] for item in plan)
    assert plan[0]["action_args"]["content"]


def test_bootstrap_twitter_respeita_mix_e_limite_configurados():
    config = _config()
    config["social_dynamics"].update({
        "twitter_bootstrap_actions": 2,
        "twitter_bootstrap_action_mix": ["QUOTE_POST"],
    })

    plan = build_social_bootstrap_plan(
        config,
        "twitter",
        [
            {"post_id": 10, "agent_id": 1, "content": "post A"},
            {"post_id": 20, "agent_id": 2, "content": "post B"},
        ],
    )

    assert len(plan) == 2
    assert [item["action_type"] for item in plan] == ["QUOTE_POST", "QUOTE_POST"]
    assert all("quote_content" in item["action_args"] for item in plan)


def test_bootstrap_desabilitado_nao_planeja_acoes():
    config = _config()
    config["social_dynamics"]["bootstrap_enabled"] = False

    assert get_social_bootstrap_target(config, "reddit", seed_post_count=2, candidate_count=4) == 0
    assert build_social_bootstrap_plan(
        config,
        "reddit",
        [{"post_id": 10, "agent_id": 1}],
    ) == []
