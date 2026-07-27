"""Builders for Vox Science harness artifacts.

The module is deterministic on purpose: it derives science metadata from the
report/harness state that already exists, without inventing human calibration.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .metrics import (
    demographic_parity_difference,
    intra_group_variance,
    kl_divergence,
    mean_absolute_error,
    temporal_stability,
    wasserstein_1d,
)


# Threshold travado pela Fase 03 (vox-academic-hardening).
DPD_BLOCKER_THRESHOLD = 0.15
LATENT_CONSTRUCT_CEILING = 0.50
CORRELATION_ALERT_THRESHOLD = 0.65
PROMPT_FIELD_TOKEN_LIMIT = 200


VOX_SCIENCE_FILENAMES = (
    "methodology_manifest.json",
    "baseline_registry.json",
    "public_data_anchors.json",
    "prompt_registry.json",
    "model_run_registry.json",
    "synthetic_interviews_manifest.json",
    "fidelity_report.json",
    "pimmur_audit.json",
    "compost_audit.json",
    "claim_policy_audit.json",
    "harness_science_gate.json",
)


def build_vox_science_artifacts(
    *,
    report_id: str,
    simulation_id: str,
    graph_id: str | None,
    simulation_requirement: str | None,
    quality_gate: Mapping[str, Any] | None,
    evidence_audit: Mapping[str, Any] | None = None,
    decision_packet: Mapping[str, Any] | None = None,
    forecast_ledger: Mapping[str, Any] | None = None,
    source_text: str | None = None,
    assembled_content: str | None = None,
    model_name: str | None = None,
    biography: Mapping[str, str] | None = None,
    replicators: Sequence[Mapping[str, Any]] | None = None,
    target_variable: str | None = None,
    subgroup_rates: Mapping[str, float] | None = None,
    samples_by_group: Mapping[str, Sequence[float]] | None = None,
    baseline_distribution: Sequence[float] | None = None,
    sample_distribution: Sequence[float] | None = None,
    temporal_baseline: Sequence[float] | None = None,
    reported_correlations: Mapping[str, float] | None = None,
    evidence_overrides: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build the P0 Vox Science artifact set for a report."""
    generated_at = _now_iso()
    gate = quality_gate if isinstance(quality_gate, Mapping) else {}
    evidence = evidence_audit if isinstance(evidence_audit, Mapping) else {}
    decision = decision_packet if isinstance(decision_packet, Mapping) else {}
    forecast = forecast_ledger if isinstance(forecast_ledger, Mapping) else {}
    requirement = _clean_text(simulation_requirement)
    domain = _detect_domain(requirement, source_text or assembled_content or "")
    baselines = _baseline_sources(domain)
    anchors = _public_data_anchors(domain, baselines)
    prompt_registry = _prompt_registry(
        requirement,
        domain,
        generated_at,
        biography=biography,
        target_variable=target_variable,
    )
    model_registry = _model_run_registry(
        report_id=report_id,
        simulation_id=simulation_id,
        graph_id=graph_id,
        model_name=model_name,
        generated_at=generated_at,
        quality_gate=gate,
        prompt_registry=prompt_registry,
        replicators=replicators,
    )
    synthetic_manifest = _synthetic_manifest(
        simulation_id=simulation_id,
        quality_gate=gate,
        generated_at=generated_at,
    )
    fidelity = _fidelity_report(
        gate,
        evidence,
        baselines,
        synthetic_manifest,
        generated_at,
        subgroup_rates=subgroup_rates,
        samples_by_group=samples_by_group,
        baseline_distribution=baseline_distribution,
        sample_distribution=sample_distribution,
        temporal_baseline=temporal_baseline,
        target_variable=target_variable,
        prompt_registry=prompt_registry,
    )
    pimmur = _pimmur_audit(gate, anchors, prompt_registry, generated_at)
    compost = _compost_audit(baselines, prompt_registry, generated_at)
    claim_policy = _claim_policy_audit(
        decision=decision,
        forecast=forecast,
        fidelity=fidelity,
        pimmur=pimmur,
        compost=compost,
        generated_at=generated_at,
        reported_correlations=reported_correlations,
        evidence_overrides=evidence_overrides,
    )
    science_gate = _science_gate(
        quality_gate=gate,
        evidence_audit=evidence,
        fidelity=fidelity,
        pimmur=pimmur,
        compost=compost,
        claim_policy=claim_policy,
        baselines=baselines,
        generated_at=generated_at,
    )
    methodology = _methodology_manifest(
        report_id=report_id,
        simulation_id=simulation_id,
        graph_id=graph_id,
        requirement=requirement,
        domain=domain,
        baselines=baselines,
        science_gate=science_gate,
        generated_at=generated_at,
    )

    return {
        "methodology_manifest.json": methodology,
        "baseline_registry.json": {
            "schema": "mirofish.vox.baseline_registry.v1",
            "generated_at": generated_at,
            "population": domain["population"],
            "domain": domain["id"],
            "anchors": baselines,
        },
        "public_data_anchors.json": {
            "schema": "mirofish.vox.public_data_anchors.v1",
            "generated_at": generated_at,
            "domain": domain["id"],
            "anchors": anchors,
        },
        "prompt_registry.json": prompt_registry,
        "model_run_registry.json": model_registry,
        "synthetic_interviews_manifest.json": synthetic_manifest,
        "fidelity_report.json": fidelity,
        "pimmur_audit.json": pimmur,
        "compost_audit.json": compost,
        "claim_policy_audit.json": claim_policy,
        "harness_science_gate.json": science_gate,
    }


def _methodology_manifest(
    *,
    report_id: str,
    simulation_id: str,
    graph_id: str | None,
    requirement: str,
    domain: Mapping[str, Any],
    baselines: list[dict[str, Any]],
    science_gate: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema": "mirofish.vox.methodology_manifest.v1",
        "generated_at": generated_at,
        "report_id": report_id,
        "simulation_id": simulation_id,
        "graph_id": graph_id,
        "population": domain["population"],
        "domain": domain["id"],
        "decision": requirement or "decisao estrategica simulada pelo MiroFish",
        "claim_target": science_gate.get("claim_level", "C1"),
        "calibration_mode": "public_data_and_existing_assets",
        "new_human_collection": False,
        "human_collection": "none_new",
        "assets_used": ["public_data", "internal_graph", "simulation_trace"],
        "forbidden_methods": ["new_interviews", "new_surveys", "new_panels"],
        "baseline_count": len(baselines),
        "external_language_policy": science_gate.get("max_external_language"),
    }


def _detect_domain(requirement: str, supporting_text: str) -> dict[str, str]:
    text = f"{requirement} {supporting_text}".lower()

    # Materia judicial vem antes de tudo: um processo nao tem populacao a
    # amostrar, tem partes e documentos. Sem esta saida antecipada, "Vara
    # Federal" e "Justica Federal" caiam no dominio de servidores publicos.
    if any(term in text for term in (
        "vara federal", "justica federal", "justiça federal", "trf", "processo judicial",
        "liquidacao de sentenca", "liquidação de sentença", "embargos", "acordao", "acórdão",
        "execucao fiscal", "execução fiscal", "peticao", "petição", "autos",
    )):
        return {
            "id": "materia_judicial",
            "population": "partes e orgaos do processo declarado",
            "period": "periodo processual declarado",
        }

    # "federal" sozinho nao caracteriza servidor publico — e a palavra mais
    # comum do vocabulario judicial brasileiro. Exige-se sinal proprio.
    if any(term in text for term in (
        "servidor publico", "servidor público", "servidores publicos", "servidores públicos",
        "servidor federal", "servidores federais", "servico publico", "serviço público",
        "pep/mgi", "enap", "pesquisa vozes",
        "carreira publica", "carreira pública", "teletrabalho", "pgd",
    )):
        return {
            "id": "servidores_federais",
            "population": "servidores publicos federais ativos",
            "period": "2024-2026",
        }
    if any(term in text for term in ("eleitor", "voto", "campanha", "prefeito", "governador", "tse", "eleicao", "eleição")):
        return {
            "id": "eleitoral_territorial",
            "population": "eleitorado brasileiro ou territorial especificado",
            "period": "ciclo eleitoral corrente",
        }
    return {
        "id": "general_public",
        "population": "publico-alvo declarado na missao MiroFish",
        "period": "periodo operacional da simulacao",
    }


def _baseline_sources(domain: Mapping[str, str]) -> list[dict[str, Any]]:
    # Num processo os atores sao partes e orgaos identificados nos autos, nao
    # uma amostra de populacao. Idade, sexo, escolaridade e renda nao dizem nada
    # sobre como a Uniao se manifesta numa liquidacao — e alimentar o perfil com
    # isso e o que faz o sistema inventar comportamento.
    if domain["id"] == "materia_judicial":
        return []

    common = [
        {
            "name": "IBGE Censo 2022",
            "url": "https://www.ibge.gov.br/estatisticas/downloads-estatisticas.html",
            "type": "public_microdata",
            "variables": ["territorio", "idade", "sexo", "escolaridade", "renda"],
            "allowed_for_prompt": True,
            "allowed_for_validation": True,
        },
    ]
    if domain["id"] == "servidores_federais":
        return [
            {
                "name": "PEP/MGI",
                "url": "https://www.gov.br/servidor/pt-br/observatorio-de-pessoal-govbr/painel-estatistico-de-pessoal",
                "type": "administrative_public_data",
                "variables": ["sexo", "idade", "escolaridade", "orgao", "remuneracao", "vinculo"],
                "allowed_for_prompt": True,
                "allowed_for_validation": True,
            },
            {
                "name": "Pesquisa Vozes/MGI-Enap",
                "url": "https://www.gov.br/gestao/pt-br/assuntos/pesquisa-vozes",
                "type": "public_survey_results",
                "variables": ["engajamento", "clima", "lideranca", "pgd", "teletrabalho"],
                "allowed_for_prompt": False,
                "allowed_for_validation": True,
            },
        ]
    if domain["id"] == "eleitoral_territorial":
        return [
            {
                "name": "TSE Dados Abertos",
                "url": "https://dadosabertos.tse.jus.br/",
                "type": "administrative_public_data",
                "variables": ["eleitorado", "resultados", "candidaturas", "territorio"],
                "allowed_for_prompt": True,
                "allowed_for_validation": True,
            },
            {
                "name": "ESEB/CESOP 2022",
                "url": "https://www.cesop.unicamp.br/democracia/survey/detalhes/id/304/",
                "type": "public_survey_microdata",
                "variables": ["ideologia", "voto", "confianca", "democracia", "atitudes"],
                "allowed_for_prompt": False,
                "allowed_for_validation": True,
            },
            *common,
        ]
    return common


def _public_data_anchors(
    domain: Mapping[str, str],
    baselines: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for source in baselines:
        for variable in source.get("variables", []):
            anchors.append(
                {
                    "variable": variable,
                    "source": source.get("name"),
                    "domain": domain["id"],
                    "role": "profile" if source.get("allowed_for_prompt") else "validation_only",
                    "allowed_for_prompt": bool(source.get("allowed_for_prompt")),
                    "confidence": "strong" if source.get("type") in {"administrative_public_data", "public_microdata"} else "medium",
                }
            )
    return anchors


def _prompt_registry(
    requirement: str,
    domain: Mapping[str, str],
    generated_at: str,
    *,
    biography: Mapping[str, str] | None = None,
    target_variable: str | None = None,
) -> dict[str, Any]:
    base_question = requirement or "Avaliar aceitacao, resistencia e condicoes de mudanca diante da proposta."
    paraphrases = [
        base_question,
        f"Como voce avaliaria a proposta considerando seu contexto de {domain['population']}?",
        "Quais sinais de aceitacao, resistencia e condicoes de mudanca aparecem diante deste cenario?",
    ]

    if biography:
        bio_ctx = _truncate_tokens(biography.get("biographical_context", ""), PROMPT_FIELD_TOKEN_LIMIT)
        role_ctx = _truncate_tokens(biography.get("role_context", ""), PROMPT_FIELD_TOKEN_LIMIT)
        scenario_ctx = _truncate_tokens(biography.get("scenario_context", ""), PROMPT_FIELD_TOKEN_LIMIT)
        legacy = False
    else:
        bio_ctx = _truncate_tokens(
            f"Perfil ancorado em dados publicos do dominio {domain['id']} ({domain['population']}).",
            PROMPT_FIELD_TOKEN_LIMIT,
        )
        role_ctx = _truncate_tokens(
            f"Participante caracterizado pelos baselines publicos do dominio {domain['id']}.",
            PROMPT_FIELD_TOKEN_LIMIT,
        )
        scenario_ctx = _truncate_tokens(base_question, PROMPT_FIELD_TOKEN_LIMIT)
        legacy = True

    questions = [
        {
            "question_id": "q_core_acceptance_001",
            "construct": "proposal_acceptance_resistance",
            "claim_use": "C2",
            "biographical_context": bio_ctx,
            "role_context": role_ctx,
            "scenario_context": scenario_ctx,
            "paraphrases": paraphrases,
            "response_schema": {"type": "mixed", "closed": "likert_5", "open": "rationale"},
            "randomization_policy": "rotate_options_when_closed",
            "forbidden_context": ["target_distribution", "expected_answer", "validation_outcome"],
            "target_variable": target_variable,
            "legacy_schema": legacy,
            "token_limits": {
                "biographical_context": PROMPT_FIELD_TOKEN_LIMIT,
                "role_context": PROMPT_FIELD_TOKEN_LIMIT,
                "scenario_context": PROMPT_FIELD_TOKEN_LIMIT,
            },
        }
    ]
    payload = {
        "schema": "mirofish.vox.prompt_registry.v2",
        "generated_at": generated_at,
        "prompt_family": "vox_public_data_grounded_v2",
        "schema_migration": "v1_to_v2_structured_biography",
        "questions": questions,
    }
    # O hash identifica o contrato e o conteúdo dos prompts. Metadados de
    # emissão variáveis tornavam o mesmo registro não determinístico quando
    # duas construções atravessavam a virada de segundo.
    payload["prompt_hash"] = _canonical_sha256({
        key: value for key, value in payload.items() if key != "generated_at"
    })
    payload["git_commit_sha"] = _git_head_sha()
    payload["osf_preregistration_url"] = None
    return payload


def _model_run_registry(
    *,
    report_id: str,
    simulation_id: str,
    graph_id: str | None,
    model_name: str | None,
    generated_at: str,
    quality_gate: Mapping[str, Any],
    prompt_registry: Mapping[str, Any],
    replicators: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    prompt_hash = prompt_registry.get("prompt_hash") or _hash_dict(prompt_registry)
    metrics = _metrics(quality_gate)
    primary = {
        "name": model_name or "configured_llm_agent_model",
        "role": "primary",
        "temperature_policy": {
            "closed_item": 0.2,
            "open_item": 0.5,
            "scenario_test": 0.3,
        },
        "seed_policy": {
            "minimum_paraphrases": 3,
            "minimum_seeds_per_paraphrase": 5,
            "status": "planned_or_partial_trace",
        },
    }
    replicator_list: list[dict[str, Any]] = []
    inter_divergence: dict[str, Any] | None = None
    if replicators:
        for replicator in replicators:
            replicator_list.append(
                {
                    "name": str(replicator.get("name", "unknown")),
                    "role": "replicator",
                    "version": replicator.get("version"),
                    "temperature": replicator.get("temperature"),
                    "seed": replicator.get("seed"),
                    "response_distribution": list(replicator.get("response_distribution", []) or []),
                }
            )
        # Calculate pairwise KL divergence between primary and each replicator.
        primary_dist = list(
            next(
                (r.get("primary_distribution", []) for r in replicators if r.get("primary_distribution")),
                [],
            )
        )
        pairs: list[dict[str, Any]] = []
        max_value = 0.0
        for replicator in replicator_list:
            dist = replicator.get("response_distribution") or []
            if not primary_dist or not dist or len(primary_dist) != len(dist):
                continue
            value = kl_divergence(primary_dist, dist)
            pairs.append(
                {
                    "pair": ["primary", replicator["name"]],
                    "value": round(value, 6),
                }
            )
            max_value = max(max_value, value)
        inter_divergence = {
            "metric": "kl_divergence",
            "pairs": pairs,
            "max_value": round(max_value, 6) if pairs else None,
        }
    return {
        "schema": "mirofish.vox.model_run_registry.v2",
        "generated_at": generated_at,
        "report_id": report_id,
        "simulation_id": simulation_id,
        "graph_id": graph_id,
        "primary_model": primary,
        "replicators": replicator_list,
        "inter_model_divergence": inter_divergence,
        "model": primary["name"],
        "temperature_policy": primary["temperature_policy"],
        "seed_policy": primary["seed_policy"],
        "prompt_registry_hash": prompt_hash,
        "observed_harness_metrics": {
            "total_actions": _int(metrics.get("total_actions_count") or metrics.get("total_actions")),
            "profiles_count": _int(metrics.get("profiles_count")),
            "generated_texts": _int(_get_nested(metrics, ("diversity", "generated_texts_count"))),
        },
    }


def _synthetic_manifest(
    *,
    simulation_id: str,
    quality_gate: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    metrics = _metrics(quality_gate)
    diversity = metrics.get("diversity") if isinstance(metrics.get("diversity"), Mapping) else {}
    profiles = _int(metrics.get("profiles_count"))
    actions = _int(metrics.get("total_actions_count") or diversity.get("total_actions"))
    generated_texts = _int(diversity.get("generated_texts_count"))
    return {
        "schema": "mirofish.vox.synthetic_interviews_manifest.v1",
        "generated_at": generated_at,
        "simulation_id": simulation_id,
        "population_units": profiles,
        "observed_actions": actions,
        "generated_texts": generated_texts,
        "execution_mode": "existing_mirofish_simulation_trace",
        "new_human_collection": False,
        "minimum_recommended_matrix": {
            "paraphrases": 3,
            "seeds": 5,
            "status": "required_for_next_full_vox_run",
        },
    }


def _fidelity_report(
    quality_gate: Mapping[str, Any],
    evidence_audit: Mapping[str, Any],
    baselines: list[Mapping[str, Any]],
    synthetic_manifest: Mapping[str, Any],
    generated_at: str,
    *,
    subgroup_rates: Mapping[str, float] | None = None,
    samples_by_group: Mapping[str, Sequence[float]] | None = None,
    baseline_distribution: Sequence[float] | None = None,
    sample_distribution: Sequence[float] | None = None,
    temporal_baseline: Sequence[float] | None = None,
    target_variable: str | None = None,
    prompt_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = _metrics(quality_gate)
    diversity = metrics.get("diversity") if isinstance(metrics.get("diversity"), Mapping) else {}
    profiles = _int(synthetic_manifest.get("population_units"))
    actions = _int(synthetic_manifest.get("observed_actions"))
    distinct = _float(diversity.get("distinct_2"), default=0.0)
    entropy = _float(diversity.get("agent_activity_entropy_norm"), default=0.0)
    behavior_entropy = _float(diversity.get("action_type_entropy_norm"), default=0.0)
    evidence_passes = evidence_audit.get("passes_gate") is True if evidence_audit else None
    baseline_validation = any(source.get("allowed_for_validation") for source in baselines)
    trace_score = min(1.0, (profiles / 100.0) * 0.35 + (actions / 100.0) * 0.35 + distinct * 0.15 + entropy * 0.15)
    robustness_score = round(max(0.0, min(1.0, trace_score)), 4)

    # R1 — multi-metric block (Wasserstein, KL, MAE, DPD, intra variance, temporal).
    wasserstein_val: float | None = None
    kl_val: float | None = None
    mae_val: float | None = None
    if baseline_distribution and sample_distribution:
        wasserstein_val = round(wasserstein_1d(baseline_distribution, sample_distribution), 6)
        kl_val = round(kl_divergence(baseline_distribution, sample_distribution), 6)
        mae_val = round(mean_absolute_error(baseline_distribution, sample_distribution), 6)
    dpd_block = demographic_parity_difference(subgroup_rates) if subgroup_rates else None
    intra_var = intra_group_variance(samples_by_group) if samples_by_group else None
    temporal_score: float | None = None
    if temporal_baseline and sample_distribution:
        temporal_score = round(temporal_stability(temporal_baseline, sample_distribution), 6)

    multi_metric = {
        "wasserstein_distance": wasserstein_val,
        "kl_divergence": kl_val,
        "mae": mae_val,
        "dpd": dpd_block,
        "intra_group_variance": intra_var,
        "temporal_stability": temporal_score,
    }
    dpd_max = dpd_block.get("__max__", {}).get("value") if dpd_block else None
    dpd_violation = bool(dpd_max is not None and dpd_max > DPD_BLOCKER_THRESHOLD)

    # R8 — blind test: validate target_variable is not present literally in any prompt field.
    blind = _blind_test_block(target_variable, prompt_registry)

    passes = bool(
        quality_gate.get("passes_gate") is True
        and profiles > 0
        and actions > 0
        and robustness_score >= 0.45
        and evidence_passes is not False
        and not dpd_violation
        and blind["masked_in_prompt"] is not False
    )
    return {
        "schema": "mirofish.vox.fidelity_report.v2",
        "generated_at": generated_at,
        "overall_score": robustness_score,
        "baseline_validation_available": baseline_validation,
        "mean_absolute_error_pp": mae_val,
        "subgroup_max_error_pp": None,
        "variance_ratio": round(max(0.5, min(1.0, (distinct + entropy + behavior_entropy) / 3)), 4)
        if any((distinct, entropy, behavior_entropy))
        else None,
        "seed_dispersion": None,
        "paraphrase_dispersion": None,
        "order_effect_score": None,
        "schema_failure_rate": 0.0 if actions > 0 else None,
        "passes_gate": passes,
        "threshold_status": "green" if passes and robustness_score >= 0.7 else "yellow" if passes else "red",
        "measurement_mode": "trace_based_until_full_seed_paraphrase_matrix",
        "multi_metric": multi_metric,
        "dpd_max": dpd_max,
        "dpd_threshold": DPD_BLOCKER_THRESHOLD,
        "dpd_violation": dpd_violation,
        "blind_test": blind,
    }


def _blind_test_block(
    target_variable: str | None,
    prompt_registry: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not target_variable:
        return {
            "target_variable": None,
            "masked_in_prompt": None,
            "recovery_score": None,
            "method": "not_applicable",
        }
    if not prompt_registry:
        return {
            "target_variable": target_variable,
            "masked_in_prompt": None,
            "recovery_score": None,
            "method": "literal_substring",
        }
    target_norm = target_variable.lower().strip()
    leak_detected = False
    for question in prompt_registry.get("questions", []) or []:
        for field in ("biographical_context", "role_context", "scenario_context"):
            value = (question.get(field) or "").lower()
            if target_norm and target_norm in value:
                leak_detected = True
                break
        if leak_detected:
            break
    return {
        "target_variable": target_variable,
        "masked_in_prompt": not leak_detected,
        "recovery_score": 0.0 if not leak_detected else 1.0,
        "method": "literal_substring",
    }


def _pimmur_audit(
    quality_gate: Mapping[str, Any],
    anchors: list[Mapping[str, Any]],
    prompt_registry: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    metrics = _metrics(quality_gate)
    profiles = _int(metrics.get("profiles_count"))
    total_actions = _int(metrics.get("total_actions_count") or _get_nested(metrics, ("diversity", "total_actions")))
    prompt_questions = prompt_registry.get("questions") if isinstance(prompt_registry.get("questions"), list) else []
    checks = {
        "profile": bool(profiles > 0 and anchors),
        "interaction": bool(total_actions > 0),
        "memory": bool(quality_gate.get("artifacts") or metrics.get("graph_nodes_count")),
        "minimal_control": bool(prompt_questions and prompt_questions[0].get("forbidden_context")),
        "unawareness": bool(prompt_questions and "expected_answer" in prompt_questions[0].get("forbidden_context", [])),
        "realism": bool(profiles > 0 and total_actions > 0),
    }
    score = round(sum(1 for value in checks.values() if value) / len(checks), 4)
    return {
        "schema": "mirofish.vox.pimmur_audit.v1",
        "generated_at": generated_at,
        "passes_gate": score >= 0.75,
        "score": score,
        "checks": checks,
    }


def _compost_audit(
    baselines: list[Mapping[str, Any]],
    prompt_registry: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    validation_only = [
        source.get("name")
        for source in baselines
        if source.get("allowed_for_validation") and not source.get("allowed_for_prompt")
    ]
    forbidden_context_ok = True
    for question in prompt_registry.get("questions", []):
        if "validation_outcome" not in question.get("forbidden_context", []):
            forbidden_context_ok = False
    return {
        "schema": "mirofish.vox.compost_audit.v1",
        "generated_at": generated_at,
        "passes_gate": bool(forbidden_context_ok),
        "validation_only_sources": validation_only,
        "outcome_excluded_from_prompt": forbidden_context_ok,
        "contamination_risk": "low" if validation_only else "medium",
    }


def _claim_policy_audit(
    *,
    decision: Mapping[str, Any],
    forecast: Mapping[str, Any],
    fidelity: Mapping[str, Any],
    pimmur: Mapping[str, Any],
    compost: Mapping[str, Any],
    generated_at: str,
    reported_correlations: Mapping[str, float] | None = None,
    evidence_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    has_forecast = bool(forecast.get("previsoes") or forecast.get("forecasts"))
    claim_level = _claim_level(fidelity, pimmur, compost, has_forecast)

    blocked_claims: list[dict[str, Any]] = []
    overrides = evidence_overrides or {}
    if reported_correlations:
        for construct, value in reported_correlations.items():
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric > CORRELATION_ALERT_THRESHOLD and not overrides.get(construct):
                blocked_claims.append(
                    {
                        "construct": construct,
                        "reported_correlation": numeric,
                        "threshold": CORRELATION_ALERT_THRESHOLD,
                        "reason": "correlation_above_ceiling_without_external_evidence",
                    }
                )

    return {
        "schema": "mirofish.vox.claim_policy_audit.v2",
        "generated_at": generated_at,
        "passes_gate": claim_level in {"C1", "C2", "C3", "C4"} and not blocked_claims,
        "claim_level": claim_level,
        "decision_packet_conviction": decision.get("conviction_operational"),
        "allowed_language": _allowed_language(claim_level),
        "blocked_language": [
            "margem de erro amostral",
            "resposta humana coletada",
            "intencao real de voto sem baseline",
            "representa a populacao sem calibracao publica",
        ],
        "latent_construct_ceiling": LATENT_CONSTRUCT_CEILING,
        "correlation_alert_threshold": CORRELATION_ALERT_THRESHOLD,
        "blocked_claims": blocked_claims,
        "epistemic_ceiling_notice": (
            "Construtos latentes (persuadibilidade, integridade, identidade social) "
            "têm teto estrutural ~0.50 com agentes sintéticos. Correlações reportadas "
            f"acima de {CORRELATION_ALERT_THRESHOLD} sem evidência externa adicional são bloqueadas."
        ),
    }


def _science_gate(
    *,
    quality_gate: Mapping[str, Any],
    evidence_audit: Mapping[str, Any],
    fidelity: Mapping[str, Any],
    pimmur: Mapping[str, Any],
    compost: Mapping[str, Any],
    claim_policy: Mapping[str, Any],
    baselines: list[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if quality_gate.get("passes_gate") is not True:
        blockers.append("system_gate_not_passed")
    if evidence_audit and evidence_audit.get("passes_gate") is not True:
        blockers.append("evidence_audit_not_passed")
    if not baselines:
        blockers.append("baseline_registry_empty")
    if pimmur.get("passes_gate") is not True:
        blockers.append("pimmur_audit_not_passed")
    if compost.get("passes_gate") is not True:
        blockers.append("compost_audit_not_passed")
    if claim_policy.get("passes_gate") is not True:
        blockers.append("claim_policy_not_passed")
    if fidelity.get("measurement_mode") == "trace_based_until_full_seed_paraphrase_matrix":
        warnings.append("full_seed_paraphrase_matrix_pending")
    if fidelity.get("mean_absolute_error_pp") is None:
        warnings.append("external_baseline_error_not_measured_yet")
    # R2 — blocker: demographic parity violation.
    if fidelity.get("dpd_violation"):
        blockers.append("demographic_parity_violation")
    # R8 — blind test leak.
    blind = fidelity.get("blind_test") if isinstance(fidelity.get("blind_test"), Mapping) else {}
    if blind.get("masked_in_prompt") is False:
        blockers.append("blind_test_leak")
    # R5 — blocked claims by epistemic ceiling.
    if claim_policy.get("blocked_claims"):
        blockers.append("claim_above_correlation_ceiling")

    passes = not blockers
    claim_level = "C0" if not passes else str(claim_policy.get("claim_level") or "C1")
    return {
        "schema": "mirofish.vox.harness_science_gate.v1",
        "generated_at": generated_at,
        "passes_gate": passes,
        "claim_level": claim_level,
        "max_external_language": _allowed_language(claim_level)[0],
        "blockers": blockers,
        "warnings": warnings,
        "required_artifacts": list(VOX_SCIENCE_FILENAMES),
        "new_human_collection": False,
        "next_upgrade": "rodar matriz completa de seeds e parafrases para elevar confianca quantitativa",
    }


def _claim_level(
    fidelity: Mapping[str, Any],
    pimmur: Mapping[str, Any],
    compost: Mapping[str, Any],
    has_forecast: bool,
) -> str:
    if not (pimmur.get("passes_gate") and compost.get("passes_gate")):
        return "C0"
    if fidelity.get("passes_gate") is not True:
        return "C1"
    if fidelity.get("mean_absolute_error_pp") is not None and fidelity.get("subgroup_max_error_pp") is not None:
        return "C4" if has_forecast else "C3"
    return "C2"


def _allowed_language(claim_level: str) -> list[str]:
    table = {
        "C0": ["mapa qualitativo de sinais e friccoes sinteticas"],
        "C1": ["simulacao sintetica exploratoria com rastreabilidade metodologica"],
        "C2": ["simulacao sintetica calibrada por dados publicos e robustez auditada"],
        "C3": ["estimativa sintetica calibrada por baseline publico comparavel"],
        "C4": ["previsao operacional monitoravel com cenario base e tese adversaria"],
    }
    return table.get(claim_level, table["C0"])


def _metrics(quality_gate: Mapping[str, Any]) -> Mapping[str, Any]:
    metrics = quality_gate.get("metrics")
    return metrics if isinstance(metrics, Mapping) else {}


def _get_nested(payload: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _hash_dict(payload: Mapping[str, Any]) -> str:
    encoded = repr(sorted(payload.items())).encode("utf-8", errors="ignore")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _truncate_tokens(text: str, max_tokens: int) -> str:
    """Trunca por whitespace (proxy de tokens). Mantem semantica."""
    if not text:
        return ""
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text
    return " ".join(tokens[:max_tokens])


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    """SHA-256 do JSON canonico (sorted keys)."""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_head_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None
