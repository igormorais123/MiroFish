from __future__ import annotations

from app.services.vox_science import VOX_SCIENCE_FILENAMES, build_vox_science_artifacts


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
    assert len(registry["prompt_registry_hash"]) == 16


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
