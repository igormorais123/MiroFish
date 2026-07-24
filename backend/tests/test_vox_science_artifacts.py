from __future__ import annotations

from app.services.vox_science import VOX_SCIENCE_FILENAMES, build_vox_science_artifacts
from app.services.vox_science import artifacts as vox_artifacts


def _gate(passes: bool = True) -> dict:
    return {
        "passes_gate": passes,
        "metrics": {
            "profiles_count": 120,
            "total_actions_count": 240,
            "graph_nodes_count": 32,
            "diversity": {
                "distinct_2": 0.74,
                "agent_activity_entropy_norm": 0.81,
                "action_type_entropy_norm": 0.69,
                "generated_texts_count": 180,
                "total_actions": 240,
            },
        },
        "artifacts": {"simulation_config": {"exists": True}},
    }


def _build(requirement: str = "Avaliar aceitacao entre servidores federais") -> dict:
    return build_vox_science_artifacts(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement=requirement,
        quality_gate=_gate(),
        evidence_audit={"passes_gate": True},
        decision_packet={"conviction_operational": 0.77},
        forecast_ledger={"previsoes": [{"titulo": "tese central"}]},
        source_text="material de apoio",
        assembled_content="relatorio final",
        model_name="gpt-test",
    )


def test_vox_science_gera_todos_os_artefatos_p0():
    artifacts = _build()

    assert tuple(artifacts.keys()) == VOX_SCIENCE_FILENAMES


def test_methodology_manifest_registra_sem_nova_coleta_humana():
    methodology = _build()["methodology_manifest.json"]

    assert methodology["new_human_collection"] is False
    assert methodology["human_collection"] == "none_new"
    assert "new_surveys" in methodology["forbidden_methods"]


def test_detecta_dominio_servidores_federais():
    baseline = _build("Simular proposta para servidores publicos federais")["baseline_registry.json"]

    assert baseline["domain"] == "servidores_federais"
    assert baseline["population"] == "servidores publicos federais ativos"


def test_baseline_servidores_inclui_pep_e_vozes():
    anchors = _build()["baseline_registry.json"]["anchors"]
    names = {item["name"] for item in anchors}

    assert {"PEP/MGI", "Pesquisa Vozes/MGI-Enap"} <= names


def test_detecta_dominio_eleitoral():
    baseline = _build("Avaliar narrativa com eleitores em campanha municipal")["baseline_registry.json"]
    names = {item["name"] for item in baseline["anchors"]}

    assert baseline["domain"] == "eleitoral_territorial"
    assert "TSE Dados Abertos" in names


def test_public_data_anchors_separam_prompt_e_validacao():
    anchors = _build()["public_data_anchors.json"]["anchors"]

    assert any(item["allowed_for_prompt"] is True for item in anchors)
    assert any(item["role"] == "validation_only" for item in anchors)


def test_prompt_registry_tem_parafrases_e_contexto_proibido():
    question = _build()["prompt_registry.json"]["questions"][0]

    assert len(question["paraphrases"]) == 3
    assert "expected_answer" in question["forbidden_context"]
    assert "validation_outcome" in question["forbidden_context"]


def test_model_run_registry_registra_modelo_e_hash():
    registry = _build()["model_run_registry.json"]

    assert registry["model"] == "gpt-test"
    # R4: prompt_registry_hash agora é SHA-256 (64 hex chars).
    assert len(registry["prompt_registry_hash"]) == 64


def test_synthetic_manifest_usa_metricas_do_gate():
    manifest = _build()["synthetic_interviews_manifest.json"]

    assert manifest["population_units"] == 120
    assert manifest["observed_actions"] == 240
    assert manifest["new_human_collection"] is False


def test_fidelity_report_aprova_trace_robusto():
    fidelity = _build()["fidelity_report.json"]

    assert fidelity["passes_gate"] is True
    assert fidelity["overall_score"] > 0.7
    assert fidelity["measurement_mode"] == "trace_based_until_full_seed_paraphrase_matrix"


def test_fidelity_report_nao_inventa_erro_humano_sem_baseline_comparado():
    fidelity = _build()["fidelity_report.json"]

    # Sem baseline_distribution/sample_distribution, MAE permanece None.
    assert fidelity["mean_absolute_error_pp"] is None
    assert fidelity["subgroup_max_error_pp"] is None


def test_pimmur_audit_aprova_quando_profile_interaction_e_prompt_ok():
    audit = _build()["pimmur_audit.json"]

    assert audit["passes_gate"] is True
    assert audit["checks"]["profile"] is True
    assert audit["checks"]["minimal_control"] is True


def test_compost_audit_exclui_outcome_do_prompt():
    audit = _build()["compost_audit.json"]

    assert audit["passes_gate"] is True
    assert audit["outcome_excluded_from_prompt"] is True


def test_claim_policy_define_c2_para_trace_robusto_sem_erro_externo():
    audit = _build()["claim_policy_audit.json"]

    assert audit["claim_level"] == "C2"
    assert "margem de erro amostral" in audit["blocked_language"]


def test_science_gate_carrega_claim_e_linguagem_maxima():
    gate = _build()["harness_science_gate.json"]

    assert gate["passes_gate"] is True
    assert gate["claim_level"] == "C2"
    assert "simulacao sintetica calibrada" in gate["max_external_language"]


def test_science_gate_bloqueia_se_system_gate_falhar():
    artifacts = build_vox_science_artifacts(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="servidores federais",
        quality_gate=_gate(False),
        evidence_audit={"passes_gate": True},
    )

    science_gate = artifacts["harness_science_gate.json"]
    assert science_gate["passes_gate"] is False
    assert "system_gate_not_passed" in science_gate["blockers"]


# ---------------------------------------------------------------------------
# Fase 03 — Vox Academic Hardening (R1-R8)
# ---------------------------------------------------------------------------


def _build_with(**extra):
    base = dict(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="Avaliar aceitacao entre servidores federais",
        quality_gate=_gate(),
        evidence_audit={"passes_gate": True},
        decision_packet={"conviction_operational": 0.77},
        forecast_ledger={"previsoes": [{"titulo": "tese central"}]},
        source_text="material de apoio",
        assembled_content="relatorio final",
        model_name="gpt-test",
    )
    base.update(extra)
    return build_vox_science_artifacts(**base)


def test_R1_fidelity_multi_metric_block_existe():
    fidelity = _build()["fidelity_report.json"]
    assert "multi_metric" in fidelity
    keys = fidelity["multi_metric"].keys()
    assert {"wasserstein_distance", "kl_divergence", "mae", "dpd", "intra_group_variance", "temporal_stability"} <= set(keys)


def test_R1_fidelity_calcula_wasserstein_quando_baseline_fornecido():
    fidelity = _build_with(
        baseline_distribution=[0.5, 0.3, 0.2],
        sample_distribution=[0.4, 0.4, 0.2],
    )["fidelity_report.json"]
    assert fidelity["multi_metric"]["wasserstein_distance"] is not None
    assert fidelity["multi_metric"]["kl_divergence"] is not None
    assert fidelity["multi_metric"]["mae"] is not None


def test_R2_dpd_violation_dispara_blocker_no_science_gate():
    artifacts = _build_with(subgroup_rates={"male": 0.30, "female": 0.60})
    fidelity = artifacts["fidelity_report.json"]
    science_gate = artifacts["harness_science_gate.json"]
    assert fidelity["dpd_max"] == 0.30
    assert fidelity["dpd_violation"] is True
    assert "demographic_parity_violation" in science_gate["blockers"]
    assert science_gate["passes_gate"] is False


def test_R2_dpd_baixo_nao_dispara_blocker():
    artifacts = _build_with(subgroup_rates={"male": 0.50, "female": 0.55})
    science_gate = artifacts["harness_science_gate.json"]
    assert "demographic_parity_violation" not in science_gate["blockers"]


def test_R4_prompt_registry_inclui_sha256_e_git_sha():
    prompts = _build()["prompt_registry.json"]
    assert len(prompts["prompt_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in prompts["prompt_hash"])
    # git_commit_sha pode ser None (sem git) ou string com 40 chars
    git_sha = prompts["git_commit_sha"]
    assert git_sha is None or (isinstance(git_sha, str) and len(git_sha) == 40)


def test_R4_prompt_hash_determinismo(monkeypatch):
    timestamps = iter(("2026-07-24T00:00:00Z", "2026-07-24T00:00:01Z"))
    monkeypatch.setattr(vox_artifacts, "_now_iso", lambda: next(timestamps))
    h1 = _build()["prompt_registry.json"]["prompt_hash"]
    h2 = _build()["prompt_registry.json"]["prompt_hash"]
    assert h1 == h2


def test_R5_claim_policy_inclui_teto_epistemico():
    audit = _build()["claim_policy_audit.json"]
    assert audit["latent_construct_ceiling"] == 0.50
    assert audit["correlation_alert_threshold"] == 0.65
    assert audit["blocked_claims"] == []
    assert "0.65" in audit["epistemic_ceiling_notice"]


def test_R5_correlacao_acima_de_0_65_sem_evidencia_bloqueia():
    artifacts = _build_with(reported_correlations={"persuadibilidade": 0.72})
    audit = artifacts["claim_policy_audit.json"]
    assert len(audit["blocked_claims"]) == 1
    assert audit["blocked_claims"][0]["construct"] == "persuadibilidade"
    assert audit["passes_gate"] is False


def test_R5_correlacao_acima_com_evidencia_externa_permite():
    artifacts = _build_with(
        reported_correlations={"persuadibilidade": 0.72},
        evidence_overrides={"persuadibilidade": {"source": "Br-STPS Durelli 2017"}},
    )
    audit = artifacts["claim_policy_audit.json"]
    assert audit["blocked_claims"] == []


def test_R6_model_registry_single_model_nao_calcula_divergencia():
    registry = _build()["model_run_registry.json"]
    assert registry["replicators"] == []
    assert registry["inter_model_divergence"] is None


def test_R6_model_registry_com_replicators_calcula_divergencia():
    registry = _build_with(
        replicators=[
            {
                "name": "claude-3.5-sonnet",
                "response_distribution": [0.40, 0.35, 0.25],
                "primary_distribution": [0.50, 0.30, 0.20],
            },
            {
                "name": "llama-3.1-70b",
                "response_distribution": [0.45, 0.30, 0.25],
            },
        ],
    )["model_run_registry.json"]
    assert len(registry["replicators"]) == 2
    assert registry["inter_model_divergence"] is not None
    assert registry["inter_model_divergence"]["metric"] == "kl_divergence"


def test_R7_prompt_default_marca_legacy_e_respeita_token_limit():
    question = _build()["prompt_registry.json"]["questions"][0]
    assert question["legacy_schema"] is True
    assert len(question["biographical_context"].split()) <= 200
    assert len(question["role_context"].split()) <= 200
    assert len(question["scenario_context"].split()) <= 200


def test_R7_prompt_estruturado_aceita_biografia_explicita():
    bio = {
        "biographical_context": "Servidora federal, ativa, com 18 anos de carreira em órgão de controle.",
        "role_context": "Coordenadora-Geral de auditoria, gestora indicada.",
        "scenario_context": "Avaliar adoção de IA generativa em fluxos disciplinares.",
    }
    question = _build_with(biography=bio)["prompt_registry.json"]["questions"][0]
    assert question["legacy_schema"] is False
    assert "auditoria" in question["role_context"]


def test_R8_blind_test_detecta_quando_target_esta_no_prompt():
    bio = {
        "biographical_context": "Servidor federal.",
        "role_context": "Gestor.",
        "scenario_context": "Avaliar persuadibilidade frente a propostas de mudança.",
    }
    artifacts = _build_with(biography=bio, target_variable="persuadibilidade")
    fidelity = artifacts["fidelity_report.json"]
    science_gate = artifacts["harness_science_gate.json"]
    assert fidelity["blind_test"]["masked_in_prompt"] is False
    assert "blind_test_leak" in science_gate["blockers"]


def test_R8_blind_test_passa_quando_target_ausente_do_prompt():
    bio = {
        "biographical_context": "Servidor federal.",
        "role_context": "Gestor.",
        "scenario_context": "Avaliar reação a propostas de mudança organizacional.",
    }
    artifacts = _build_with(biography=bio, target_variable="persuadibilidade")
    fidelity = artifacts["fidelity_report.json"]
    assert fidelity["blind_test"]["masked_in_prompt"] is True


def test_R8_blind_test_inativo_quando_target_nao_declarado():
    fidelity = _build()["fidelity_report.json"]
    assert fidelity["blind_test"]["masked_in_prompt"] is None
    assert fidelity["blind_test"]["method"] == "not_applicable"
