from app.services.decision_packet import build_decision_packet, decision_packet_prompt_block


def test_decision_packet_gera_probabilidades_deterministicas_com_soma_100():
    packet = build_decision_packet(
        simulation_id="sim_pred",
        simulation_requirement="avaliar tese",
        outline_summary="Tese vencedora operacional",
        quality_gate={
            "passes_gate": True,
            "metrics": {
                "min_actions": 10,
                "total_actions_count": 40,
                "profiles_count": 12,
                "total_rounds": 72,
                "current_round": 72,
                "graph_nodes_count": 8,
                "graph_edges_count": 12,
                "source_text_characters": 1200,
                "diversity": {
                    "total_actions": 40,
                    "generated_texts_count": 30,
                    "distinct_2": 0.82,
                    "agent_activity_entropy_norm": 0.86,
                    "action_type_entropy_norm": 0.8,
                    "entity_type_coverage": 3,
                    "oasis_trace": {
                        "behavioral_entropy_norm": 0.78,
                        "emergent_interactive_actions_estimate": 11,
                        "dynamic_create_posts_estimate": 3,
                    },
                },
            },
        },
    )

    probabilities = [
        scenario["probability_percent"]
        for scenario in packet["scenarios"].values()
    ]

    assert packet["schema"] == "mirofish.decision_packet.v1"
    assert sum(probabilities) == 100
    assert packet["scenarios"]["base"]["probability_percent"] > packet["scenarios"]["contrary"]["probability_percent"]
    assert packet["conviction_operational"] > 0.75
    assert packet["structured_metrics"]["scenario_base_probability_percent"] == packet["scenarios"]["base"]["probability_percent"]


def test_decision_packet_prompt_expoe_percentuais_oficiais():
    packet = build_decision_packet(
        simulation_id="sim_pred",
        simulation_requirement="avaliar tese",
        quality_gate={
            "passes_gate": True,
            "metrics": {
                "min_actions": 10,
                "total_actions_count": 10,
                "profiles_count": 5,
                "diversity": {
                    "generated_texts_count": 10,
                    "distinct_2": 0.6,
                    "agent_activity_entropy_norm": 0.6,
                    "action_type_entropy_norm": 0.6,
                    "entity_type_coverage": 2,
                    "oasis_trace": {"emergent_interactive_actions_estimate": 2},
                },
            },
        },
    )

    block = decision_packet_prompt_block(packet)

    assert "Conviccao operacional INTEIA" in block
    assert f"Base: {packet['scenarios']['base']['probability_percent']}%" in block
    assert f"Contrario: {packet['scenarios']['contrary']['probability_percent']}%" in block
