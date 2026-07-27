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

    assert packet["schema"] == "mirofish.decision_packet.v2"
    assert packet["conviction_operational"] > 0.75

    # Os cenarios continuam enquadrando a analise, sem probabilidade atribuida:
    # ela era transformacao linear da propria conviccao, sem frequencia
    # observada nem classe de referencia por tras.
    for cenario in packet["scenarios"].values():
        assert "probability" not in cenario
        assert "probability_percent" not in cenario
        assert cenario["role"]

    # Cada risco aponta o componente medido que o sustenta.
    assert packet["risks"]["evidence"]["driver"] == "knowledge_backing"
    for risco in packet["risks"].values():
        assert "probability_percent" not in risco
        assert 0.0 <= risco["component_score"] <= 1.0

    assert packet["method_lock"]["status"] == "locked"
    assert not any(
        "percentuais oficiais" in regra for regra in packet["method_lock"]["rules"]
    )
    assert packet["convergence"]["score_percent"] > 0
    assert packet["red_team"]["opposing_thesis"]
    assert packet["red_team"]["reversal_triggers"]
    assert packet["structured_metrics"]["red_team_pressure_percent"] == packet["red_team"]["pressure_percent"]
    assert packet["structured_metrics"]["convergence_reversal_threshold_percent"] == 62
    assert packet["structured_metrics"]["convergence_recommended_next_runs"] == packet["convergence"]["recommended_next_runs"]


def test_conviccao_chega_a_zero_sem_evidencia_coletada():
    """
    O piso de 0.35, somado a formula linear que dele derivava os cenarios,
    impedia o pacote de produzir numero abaixo de 54% — nem com grafo vazio e
    nenhuma acao. Um indicador que nao pode ser baixo nao informa nada.
    """
    packet = build_decision_packet(
        simulation_id="sim_vazia",
        simulation_requirement="avaliar tese",
        quality_gate={
            "passes_gate": False,
            "metrics": {
                "min_actions": 10,
                "total_actions_count": 0,
                "profiles_count": 0,
                "total_rounds": 240,
                "current_round": 0,
                "graph_nodes_count": 0,
                "graph_edges_count": 0,
                "source_text_characters": 0,
                "diversity": {},
            },
        },
    )

    assert packet["conviction_operational"] == 0.0
    assert packet["conviction_operational_percent"] == 0
    # Sem lastro, a superficie de ataque e maxima.
    assert packet["red_team"]["pressure_percent"] == 100


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

    assert "Lastro de evidencia coletada" in block
    assert packet["scenarios"]["base"]["role"] in block
    assert packet["scenarios"]["contrary"]["role"] in block
    # O prompt nao pode mandar a Helena quantificar cenario: era assim que o
    # percentual fabricado chegava ao texto do relatorio.
    assert "Riscos oficiais para quantificar" not in block
    assert "Red team obrigatorio" in block
    assert packet["red_team"]["attack_vector"] in block
