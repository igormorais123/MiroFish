"""Smoke test ponta-a-ponta: build_vox_science_artifacts gera os 11
artefatos + todos os campos novos R1-R8 da Fase 03 preenchidos."""

from __future__ import annotations

from app.services.vox_science import VOX_SCIENCE_FILENAMES, build_vox_science_artifacts
from app.services.vox_science.artifacts import (
    CORRELATION_ALERT_THRESHOLD,
    DPD_BLOCKER_THRESHOLD,
    LATENT_CONSTRUCT_CEILING,
)


def test_smoke_e2e_fase03_todos_artefatos_e_campos_novos():
    """Builder produz todos 11 artefatos + 8 campos novos R1-R8."""

    biography = {
        "biographical_context": "Servidora federal carreira X, 18 anos, regiao Centro-Oeste.",
        "role_context": "Gestora de auditoria. Funcao indicada.",
        "scenario_context": "Avaliar reacao a propostas de mudanca organizacional.",
    }
    replicators = [
        {
            "name": "claude-3.5-sonnet",
            "response_distribution": [0.40, 0.35, 0.25],
            "primary_distribution": [0.50, 0.30, 0.20],
        },
    ]

    artifacts = build_vox_science_artifacts(
        report_id="smoke_report_1",
        simulation_id="smoke_sim_1",
        graph_id="smoke_graph_1",
        simulation_requirement="Avaliar aceitacao entre servidores federais",
        quality_gate={
            "passes_gate": True,
            "metrics": {
                "profiles_count": 120,
                "total_actions_count": 240,
                "diversity": {
                    "distinct_2": 0.74,
                    "agent_activity_entropy_norm": 0.81,
                    "action_type_entropy_norm": 0.69,
                    "generated_texts_count": 180,
                    "total_actions": 240,
                },
            },
            "artifacts": {"simulation_config": {"exists": True}},
        },
        evidence_audit={"passes_gate": True},
        decision_packet={"conviction_operational": 0.77},
        forecast_ledger={"previsoes": [{"titulo": "tese central"}]},
        model_name="gpt-test",
        biography=biography,
        replicators=replicators,
        target_variable="persuadibilidade",
        subgroup_rates={"male": 0.50, "female": 0.48},
        baseline_distribution=[0.50, 0.30, 0.20],
        sample_distribution=[0.45, 0.35, 0.20],
        temporal_baseline=[0.48, 0.32, 0.20],
        samples_by_group={"male": [0.4, 0.5, 0.6], "female": [0.45, 0.50, 0.55]},
        reported_correlations={"acceptance": 0.45},
    )

    # ===== Critério 3 do SPEC §5: 11 artefatos presentes =====
    assert tuple(artifacts.keys()) == VOX_SCIENCE_FILENAMES, "11 artefatos obrigatorios"

    # ===== R1 multi-metric =====
    fidelity = artifacts["fidelity_report.json"]
    multi = fidelity["multi_metric"]
    # Vetores em memoria sem snapshot materializado/hash nao sao calibracao.
    assert multi["wasserstein_distance"] is None
    assert multi["kl_divergence"] is None
    assert multi["mae"] is None
    assert multi["dpd"] is not None
    assert multi["intra_group_variance"] is not None
    assert multi["temporal_stability"] is None

    # ===== R2 DPD threshold respeitado =====
    assert fidelity["dpd_threshold"] == DPD_BLOCKER_THRESHOLD
    assert fidelity["dpd_violation"] is False  # DPD 0.02 << 0.15

    # ===== R4 prompt_hash + git_sha =====
    prompts = artifacts["prompt_registry.json"]
    assert len(prompts["prompt_hash"]) == 64
    assert "git_commit_sha" in prompts  # pode ser None se rodando fora de git
    assert "osf_preregistration_url" in prompts

    # ===== R5 teto epistemico =====
    claim_policy = artifacts["claim_policy_audit.json"]
    assert claim_policy["latent_construct_ceiling"] == LATENT_CONSTRUCT_CEILING
    assert claim_policy["correlation_alert_threshold"] == CORRELATION_ALERT_THRESHOLD
    assert isinstance(claim_policy["blocked_claims"], list)

    # ===== R6 replicators =====
    model_registry = artifacts["model_run_registry.json"]
    assert len(model_registry["replicators"]) == 1
    assert model_registry["replicators"][0]["name"] == "claude-3.5-sonnet"
    assert model_registry["inter_model_divergence"] is not None

    # ===== R7 prompt biografico estruturado =====
    question = prompts["questions"][0]
    assert "biographical_context" in question
    assert "role_context" in question
    assert "scenario_context" in question
    assert question["legacy_schema"] is False
    assert "auditoria" in question["role_context"]

    # ===== R8 blind test passou =====
    blind = fidelity["blind_test"]
    assert blind["target_variable"] == "persuadibilidade"
    assert blind["masked_in_prompt"] is True  # variavel ausente do prompt

    # ===== Science gate aprovado =====
    gate = artifacts["harness_science_gate.json"]
    assert gate["passes_gate"] is True
    assert gate["claim_level"] == "C1"


def test_smoke_e2e_fase03_dpd_violation_e_blind_leak_bloqueiam_gate():
    """Construtos de violacao acionam blockers no science_gate."""

    biography = {
        "biographical_context": "Servidor.",
        "role_context": "Gestor.",
        "scenario_context": "Avaliar persuadibilidade do publico.",  # leak proposital
    }

    artifacts = build_vox_science_artifacts(
        report_id="smoke_report_2",
        simulation_id="smoke_sim_2",
        graph_id="smoke_graph_2",
        simulation_requirement="x",
        quality_gate={
            "passes_gate": True,
            "metrics": {
                "profiles_count": 120,
                "total_actions_count": 240,
                "diversity": {
                    "distinct_2": 0.74,
                    "agent_activity_entropy_norm": 0.81,
                    "action_type_entropy_norm": 0.69,
                    "generated_texts_count": 180,
                    "total_actions": 240,
                },
            },
            "artifacts": {"simulation_config": {"exists": True}},
        },
        evidence_audit={"passes_gate": True},
        biography=biography,
        target_variable="persuadibilidade",  # vai dar leak
        subgroup_rates={"male": 0.20, "female": 0.80},  # DPD 0.60 viola
        reported_correlations={"acceptance": 0.92},  # acima do 0.65
    )

    gate = artifacts["harness_science_gate.json"]
    fidelity = artifacts["fidelity_report.json"]
    claim_policy = artifacts["claim_policy_audit.json"]

    assert gate["passes_gate"] is False
    assert "demographic_parity_violation" in gate["blockers"]
    assert "blind_test_leak" in gate["blockers"]
    assert "claim_policy_rejected_assertion" in gate["claim_blockers"]
    assert fidelity["blind_test"]["masked_in_prompt"] is False
    assert len(claim_policy["blocked_claims"]) == 1
