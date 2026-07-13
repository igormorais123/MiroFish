"""Builders for Vox Science harness artifacts.

The module is deterministic on purpose: it derives science metadata from the
report/harness state that already exists, without inventing human calibration.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .baseline_snapshot import (
    BaselineSnapshot,
    SnapshotValidationError,
    load_baseline_snapshot,
    validate_numeric_vector,
)
from .authority import AuthorizedEvidence, resolve_authorized_evidence
from .claim_evidence import ClaimEvidence, load_claim_evidence
from .metrics import (
    categorical_temporal_stability,
    categorical_wasserstein_1d,
    demographic_parity_difference,
    intra_group_variance,
    kl_divergence,
    mean_absolute_error,
    multiclass_brier_score,
    multiclass_log_loss,
)
from .verification import (
    C4_MATERIAL_POLICY_ID,
    PREREGISTERED_SCORING_ALGORITHM,
    sign_gate,
    signing_key,
)


# Threshold travado pela Fase 03 (vox-academic-hardening).
DPD_BLOCKER_THRESHOLD = 0.15
LATENT_CONSTRUCT_CEILING = 0.50
CORRELATION_ALERT_THRESHOLD = 0.65
PROMPT_FIELD_TOKEN_LIMIT = 200
MIN_C3_SUBGROUP_N = 30
C3_MAX_MAE = 0.15
C3_MAX_KL = 0.15
C3_MAX_WASSERSTEIN = 0.15
C3_MAX_SUBGROUP_ERROR = 0.15
C3_MIN_STABILITY = 0.70
C4_PER_ID_SCORING_VERSION = PREREGISTERED_SCORING_ALGORITHM
MAX_EVIDENCE_ITEMS = 256
MAX_REPLICATORS = 32
MAX_REPLICATOR_VECTOR_LENGTH = 256
MAX_REPLICATOR_NAME_LENGTH = 128
MAX_REPLICATOR_VERSION_LENGTH = 128
MAX_REPLICATOR_RESPONSE_TEXT_LENGTH = 4096


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
    baseline_snapshot_path: str | None = None,
    baseline_snapshot_root: str | None = None,
    baseline_snapshot_sha256: str | None = None,
    stability_runs: Sequence[Sequence[float]] | None = None,
    prospective_evidence: Mapping[str, Any] | None = None,
    authorized_baseline_snapshot_path: str | None = None,
    claim_evidence_path: str | None = None,
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
    for catalog_entry in baselines:
        catalog_entry["materialization_status"] = "metadata_only"
        catalog_entry["loaded_baseline"] = False
    snapshot: BaselineSnapshot | None = None
    snapshot_error = "materialized_baseline_snapshot_missing"
    authority: AuthorizedEvidence | None = None
    if any((authorized_baseline_snapshot_path, claim_evidence_path)):
        if not all((authorized_baseline_snapshot_path, claim_evidence_path)):
            snapshot_error = "authorized_claim_artifact_arguments_incomplete"
        else:
            try:
                authority = resolve_authorized_evidence(
                    baseline_path=authorized_baseline_snapshot_path or "",
                    claim_evidence_path=claim_evidence_path or "",
                )
                snapshot = load_baseline_snapshot(
                    relative_path=authority.baseline_path,
                    trusted_root=authority.trusted_root,
                    expected_sha256=authority.baseline_sha256,
                    target_variable=target_variable,
                )
                snapshot_error = ""
            except SnapshotValidationError as exc:
                snapshot_error = str(exc)
    elif any((baseline_snapshot_path, baseline_snapshot_root, baseline_snapshot_sha256)):
        # Deprecated caller-authorized inputs remain diagnostic-only and cannot
        # establish a calibrated claim.
        if not all((baseline_snapshot_path, baseline_snapshot_root, baseline_snapshot_sha256)):
            snapshot_error = "legacy_baseline_snapshot_arguments_incomplete"
        else:
            try:
                load_baseline_snapshot(
                    relative_path=baseline_snapshot_path or "",
                    trusted_root=baseline_snapshot_root or "",
                    expected_sha256=baseline_snapshot_sha256 or "",
                    target_variable=target_variable,
                )
                snapshot_error = "legacy_caller_authorized_snapshot_not_claim_evidence"
            except SnapshotValidationError as exc:
                snapshot_error = str(exc)
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
    claim_evidence: ClaimEvidence | None = None
    claim_evidence_error = "materialized_claim_evidence_missing"
    if (
        authority is not None
        and snapshot is not None
        and snapshot.payload.get("data", {}).get("kind") == "distributions"
    ):
        try:
            claim_evidence = load_claim_evidence(
                relative_path=authority.claim_evidence_path,
                trusted_root=authority.trusted_root,
                expected_sha256=authority.claim_evidence_sha256,
                authority_manifest_sha256=authority.authority_manifest_sha256,
                baseline_snapshot=snapshot,
                expected_report_id=report_id,
                expected_simulation_id=simulation_id,
                expected_run_id=str(model_registry["run_id"]),
                expected_config_sha256=str(model_registry["config_sha256"]),
                expected_input_sha256=str(model_registry["prompt_registry_hash"]),
                authorized_stability_runs=authority.stability_runs,
                authorized_preregistered_forecasts=authority.preregistered_forecasts,
            )
            claim_evidence_error = ""
        except SnapshotValidationError as exc:
            claim_evidence_error = str(exc)
    elif authority is not None and snapshot is not None:
        claim_evidence_error = "row_baseline_probability_metrics_not_implemented"
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
        baseline_snapshot=snapshot,
        baseline_snapshot_error=snapshot_error,
        stability_runs=stability_runs,
        prospective_evidence=prospective_evidence,
        report_id=report_id,
        simulation_id=simulation_id,
        claim_evidence=claim_evidence,
        claim_evidence_error=claim_evidence_error,
        run_id=str(model_registry["run_id"]),
        config_sha256=str(model_registry["config_sha256"]),
        authority=authority,
        replicator_input_valid=bool(model_registry["replicator_input_valid"]),
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

    artifacts = {
        "methodology_manifest.json": methodology,
        "baseline_registry.json": {
            "schema": "mirofish.vox.baseline_registry.v2",
            "generated_at": generated_at,
            "population": domain["population"],
            "domain": domain["id"],
            "anchors": baselines,
            "catalog_semantics": "metadata_only_not_a_loaded_calibration_baseline",
            "loaded_baseline": snapshot is not None,
            "loaded_snapshot": snapshot.public_summary() if snapshot else {
                "status": "unavailable",
                "reason": snapshot_error,
            },
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
    _downgrade_unsigned_calibration(artifacts)
    _bind_artifact_generation(
        artifacts,
        report_id=report_id,
        simulation_id=simulation_id,
        generated_at=generated_at,
    )
    return artifacts


def _bind_artifact_generation(
    artifacts: dict[str, dict[str, Any]],
    *,
    report_id: str,
    simulation_id: str,
    generated_at: str,
) -> None:
    """Bind the 11-file legacy surface into one detectable generation."""

    generation_id = _canonical_sha256(
        {
            "report_id": report_id,
            "simulation_id": simulation_id,
            "generated_at": generated_at,
            "prompt_hash": artifacts["prompt_registry.json"].get("prompt_hash"),
            "evidence_binding": artifacts["fidelity_report.json"].get("evidence_binding"),
        }
    )
    for payload in artifacts.values():
        payload["generation_id"] = generation_id
    hashes = {
        name: _canonical_sha256(payload)
        for name, payload in artifacts.items()
        if name != "harness_science_gate.json"
    }
    gate = artifacts["harness_science_gate.json"]
    gate["artifact_hashes"] = hashes
    gate["generation_contract"] = "gate_written_last; consumers reject mixed generations"
    model = artifacts["model_run_registry.json"]
    binding_value = artifacts["fidelity_report.json"].get("evidence_binding")
    binding = binding_value if isinstance(binding_value, Mapping) else {}
    gate.update(
        {
            "report_id": report_id,
            "simulation_id": simulation_id,
            "run_id": model.get("run_id"),
            "config_sha256": model.get("config_sha256"),
            "input_sha256": model.get("prompt_registry_hash"),
            "baseline_snapshot_path": binding.get("baseline_snapshot_path"),
            "baseline_snapshot_sha256": binding.get("baseline_snapshot_sha256"),
            "claim_evidence_path": binding.get("claim_evidence_path"),
            "claim_evidence_sha256": binding.get("claim_evidence_sha256"),
            "authority_manifest_sha256": binding.get("authority_manifest_sha256"),
        }
    )
    sign_gate(gate)


def _downgrade_unsigned_calibration(artifacts: dict[str, dict[str, Any]]) -> None:
    """A host key is mandatory before any generated surface may emit C2+."""

    gate = artifacts["harness_science_gate.json"]
    if gate.get("claim_level") not in {"C2", "C3", "C4"} or signing_key() is not None:
        return
    fidelity = artifacts["fidelity_report.json"]
    eligibility = fidelity.get("claim_eligibility")
    if isinstance(eligibility, dict):
        eligibility.update({"C2": False, "C3": False, "C4": False})
    fidelity.setdefault("claim_blockers", []).append("host_signing_key_unavailable")
    policy = artifacts["claim_policy_audit.json"]
    policy["claim_level"] = "C1"
    policy["allowed_language"] = _allowed_language("C1")
    methodology = artifacts["methodology_manifest.json"]
    methodology["claim_target"] = "C1"
    methodology["calibration_mode"] = "synthetic_trace_only"
    methodology["external_language_policy"] = _allowed_language("C1")[0]
    gate["claim_level"] = "C1"
    gate["max_external_language"] = _allowed_language("C1")[0]
    gate.setdefault("claim_blockers", []).append("host_signing_key_unavailable")


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
        "calibration_mode": (
            "materialized_snapshot_measured"
            if science_gate.get("claim_level") in {"C2", "C3", "C4"}
            else "synthetic_trace_only"
        ),
        "new_human_collection": False,
        "human_collection": "none_new",
        "assets_used": ["public_data", "internal_graph", "simulation_trace"],
        "forbidden_methods": ["new_interviews", "new_surveys", "new_panels"],
        "baseline_count": len(baselines),
        "external_language_policy": science_gate.get("max_external_language"),
    }


def _detect_domain(requirement: str, supporting_text: str) -> dict[str, str]:
    text = f"{requirement} {supporting_text}".lower()
    if any(term in text for term in ("servidor", "servico publico", "serviço público", "federal", "mgI".lower(), "vozes")):
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
    baselines: Sequence[Mapping[str, Any]],
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
    payload: dict[str, Any] = {
        "schema": "mirofish.vox.prompt_registry.v2",
        "generated_at": generated_at,
        "prompt_family": "vox_public_data_grounded_v2",
        "schema_migration": "v1_to_v2_structured_biography",
        "questions": questions,
    }
    payload["prompt_hash"] = _canonical_sha256(
        {key: value for key, value in payload.items() if key != "generated_at"}
    )
    payload["git_commit_sha"] = _git_head_sha()
    payload["osf_preregistration_url"] = None
    return payload


def _valid_replicator_input(
    replicators: Sequence[Mapping[str, Any]] | None,
) -> bool:
    if replicators is None:
        return True
    if (
        not isinstance(replicators, Sequence)
        or isinstance(replicators, (str, bytes))
        or len(replicators) > MAX_REPLICATORS
    ):
        return False
    for item in replicators:
        if not isinstance(item, Mapping):
            return False
        if not set(item).issubset(
            {
                "name",
                "version",
                "temperature",
                "seed",
                "response_distribution",
                "primary_distribution",
                "response_text",
            }
        ):
            return False
        name = item.get("name")
        version = item.get("version")
        temperature = item.get("temperature")
        seed = item.get("seed")
        response_text = item.get("response_text")
        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name) > MAX_REPLICATOR_NAME_LENGTH
        ):
            return False
        if version is not None and (
            not isinstance(version, str)
            or len(version) > MAX_REPLICATOR_VERSION_LENGTH
        ):
            return False
        if response_text is not None and (
            not isinstance(response_text, str)
            or len(response_text) > MAX_REPLICATOR_RESPONSE_TEXT_LENGTH
        ):
            return False
        if temperature is not None and (
            not _is_finite_number(temperature) or not 0 <= float(temperature) <= 2
        ):
            return False
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            return False
        try:
            response_raw = item.get("response_distribution")
            if (
                not isinstance(response_raw, Sequence)
                or isinstance(response_raw, (str, bytes))
                or not 1 <= len(response_raw) <= MAX_REPLICATOR_VECTOR_LENGTH
            ):
                return False
            response = validate_numeric_vector(
                response_raw,
                reason="replicator_response_distribution_invalid",
            )
            primary_raw = item.get("primary_distribution")
            if primary_raw is not None:
                if (
                    not isinstance(primary_raw, Sequence)
                    or isinstance(primary_raw, (str, bytes))
                    or not 1 <= len(primary_raw) <= MAX_REPLICATOR_VECTOR_LENGTH
                ):
                    return False
                validate_numeric_vector(
                    primary_raw,
                    expected_length=len(response),
                    reason="replicator_primary_distribution_invalid",
                )
        except SnapshotValidationError:
            return False
    return True


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
    replicator_input_valid = _valid_replicator_input(replicators)
    replicator_input = (
        list(replicators)
        if replicator_input_valid and replicators is not None
        else []
    )
    if replicator_input:
        for replicator in replicator_input:
            if not isinstance(replicator, Mapping):
                continue
            replicator_list.append(
                {
                    "name": str(replicator.get("name", "unknown")),
                    "role": "replicator",
                    "version": replicator.get("version"),
                    "temperature": replicator.get("temperature"),
                    "seed": replicator.get("seed"),
                    "response_distribution": list(replicator.get("response_distribution", []) or []),
                    "response_text": replicator.get("response_text"),
                }
            )
        # Calculate pairwise KL divergence between primary and each replicator.
        primary_dist = list(
            next(
                (r.get("primary_distribution", []) for r in replicator_input if isinstance(r, Mapping) and r.get("primary_distribution")),
                [],
            )
        )
        pairs: list[dict[str, Any]] = []
        max_value = 0.0
        for replicator in replicator_list:
            dist = replicator.get("response_distribution") or []
            if not primary_dist or not dist or len(primary_dist) != len(dist):
                continue
            try:
                value = kl_divergence(primary_dist, dist)
            except ValueError:
                continue
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
    config_sha256 = _canonical_sha256(
        {
            "report_id": report_id,
            "simulation_id": simulation_id,
            "graph_id": graph_id,
            "model": primary["name"],
            "prompt_registry_hash": prompt_hash,
            "temperature_policy": primary["temperature_policy"],
        }
    )
    run_id = _canonical_sha256(
        {
            "report_id": report_id,
            "simulation_id": simulation_id,
            "config_sha256": config_sha256,
        }
    )
    return {
        "schema": "mirofish.vox.model_run_registry.v2",
        "generated_at": generated_at,
        "report_id": report_id,
        "simulation_id": simulation_id,
        "graph_id": graph_id,
        "primary_model": primary,
        "replicators": replicator_list,
        "replicator_input_valid": replicator_input_valid,
        "replicator_limit": MAX_REPLICATORS,
        "replicator_budgets": {
            "response_distribution_max_items": MAX_REPLICATOR_VECTOR_LENGTH,
            "primary_distribution_max_items": MAX_REPLICATOR_VECTOR_LENGTH,
            "name_max_chars": MAX_REPLICATOR_NAME_LENGTH,
            "version_max_chars": MAX_REPLICATOR_VERSION_LENGTH,
            "response_text_max_chars": MAX_REPLICATOR_RESPONSE_TEXT_LENGTH,
        },
        "inter_model_divergence": inter_divergence,
        "model": primary["name"],
        "temperature_policy": primary["temperature_policy"],
        "seed_policy": primary["seed_policy"],
        "prompt_registry_hash": prompt_hash,
        "config_sha256": config_sha256,
        "run_id": run_id,
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
    diversity_value = metrics.get("diversity")
    diversity: Mapping[str, Any] = diversity_value if isinstance(diversity_value, Mapping) else {}
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
    baselines: Sequence[Mapping[str, Any]],
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
    baseline_snapshot: BaselineSnapshot | None = None,
    baseline_snapshot_error: str = "materialized_baseline_snapshot_missing",
    stability_runs: Sequence[Sequence[float]] | None = None,
    prospective_evidence: Mapping[str, Any] | None = None,
    report_id: str = "",
    simulation_id: str = "",
    claim_evidence: ClaimEvidence | None = None,
    claim_evidence_error: str = "materialized_claim_evidence_missing",
    run_id: str = "",
    config_sha256: str = "",
    authority: AuthorizedEvidence | None = None,
    replicator_input_valid: bool = True,
) -> dict[str, Any]:
    metrics = _metrics(quality_gate)
    diversity_value = metrics.get("diversity")
    diversity: Mapping[str, Any] = diversity_value if isinstance(diversity_value, Mapping) else {}
    profiles = _int(synthetic_manifest.get("population_units"))
    actions = _int(synthetic_manifest.get("observed_actions"))
    distinct = _float(diversity.get("distinct_2"), default=0.0)
    entropy = _float(diversity.get("agent_activity_entropy_norm"), default=0.0)
    behavior_entropy = _float(diversity.get("action_type_entropy_norm"), default=0.0)
    evidence_passes = evidence_audit.get("passes_gate") is True if evidence_audit else None
    # A registry URL is discovery metadata. Only a validated local snapshot is evidence.
    baseline_validation = baseline_snapshot is not None
    trace_score = min(1.0, (profiles / 100.0) * 0.35 + (actions / 100.0) * 0.35 + distinct * 0.15 + entropy * 0.15)
    robustness_score = round(max(0.0, min(1.0, trace_score)), 4)

    # Claim metrics are recomputed only from an authority-approved local bundle.
    wasserstein_val: float | None = None
    kl_val: float | None = None
    mae_val: float | None = None
    sample_values: list[float] | None = None
    claim_blockers: list[str] = []
    baseline_kind = (
        baseline_snapshot.payload.get("data", {}).get("kind")
        if baseline_snapshot is not None
        else None
    )
    if baseline_kind == "rows":
        claim_blockers.append("row_baseline_probability_metrics_not_implemented")
    if not replicator_input_valid:
        claim_blockers.append("replicator_input_invalid")
    if evidence_audit.get("passes_gate") is not True:
        claim_blockers.append("evidence_audit_missing_or_not_passed")
    if baseline_snapshot is None or claim_evidence is None:
        claim_blockers.append(baseline_snapshot_error or "materialized_baseline_snapshot_missing")
        claim_blockers.append(claim_evidence_error or "materialized_claim_evidence_missing")
    else:
        try:
            sample_values = list(claim_evidence.evaluation_predicted)
            observed_values = list(claim_evidence.evaluation_observed)
            wasserstein_val = _finite_metric(
                categorical_wasserstein_1d(observed_values, sample_values)
            )
            kl_val = _finite_metric(kl_divergence(observed_values, sample_values))
            mae_val = _finite_metric(mean_absolute_error(observed_values, sample_values))
        except (SnapshotValidationError, ArithmeticError, ValueError, OverflowError):
            claim_blockers.append("calibration_metrics_unavailable_or_invalid")
    if any(
        value is not None
        for value in (
            baseline_distribution,
            sample_distribution,
            samples_by_group,
            stability_runs,
            prospective_evidence,
        )
    ):
        claim_blockers.append("legacy_in_memory_evidence_is_diagnostic_only")

    dpd_block = _safe_dpd(subgroup_rates)
    if subgroup_rates is not None and dpd_block is None:
        claim_blockers.append("subgroup_rates_invalid")
    intra_var = _safe_intra_group_variance(samples_by_group)
    if samples_by_group is not None and intra_var is None:
        claim_blockers.append("samples_by_group_invalid")

    subgroup_metrics: dict[str, Any] = {"status": "planned", "reason": "subgroup_evidence_incomplete"}
    subgroup_max_error: float | None = None
    if baseline_snapshot is not None and claim_evidence is not None and claim_evidence.subgroup_predictions:
        expected_groups = set(baseline_snapshot.subgroup_observed)
        if len(expected_groups) < 2:
            claim_blockers.append("c3_requires_at_least_two_baseline_subgroups")
        elif set(claim_evidence.subgroup_predictions) != expected_groups:
            claim_blockers.append("c3_subgroup_set_mismatch")
        elif any(
            claim_evidence.subgroup_sample_sizes.get(group, 0) < MIN_C3_SUBGROUP_N
            for group in expected_groups
        ):
            claim_blockers.append("c3_subgroup_minimum_n_not_met")
        else:
            try:
                errors: dict[str, float] = {}
                for group in sorted(expected_groups):
                    synthetic = list(claim_evidence.subgroup_predictions[group])
                    errors[group] = _finite_metric(
                        mean_absolute_error(baseline_snapshot.subgroup_observed[group], synthetic)
                    )
                subgroup_max_error = max(errors.values())
                subgroup_metrics = {
                    "status": "computed",
                    "algorithm": "mean_absolute_error.v1",
                    "errors": errors,
                    "max_error": subgroup_max_error,
                    "minimum_n": MIN_C3_SUBGROUP_N,
                    "sample_sizes": dict(claim_evidence.subgroup_sample_sizes),
                    "claim_evidence_sha256": claim_evidence.sha256,
                }
            except (SnapshotValidationError, ArithmeticError, ValueError, OverflowError):
                claim_blockers.append("c3_subgroup_metrics_unavailable_or_invalid")

    stability: dict[str, Any] = {"status": "planned", "reason": "stability_runs_missing"}
    temporal_score: float | None = None
    if claim_evidence is not None and claim_evidence.stability_runs:
        try:
            validated_runs = [list(run.distribution) for run in claim_evidence.stability_runs]
            scores = [
                _finite_metric(categorical_temporal_stability(left, right))
                for left, right in zip(validated_runs, validated_runs[1:])
            ]
            dispersions = [
                _finite_metric(categorical_wasserstein_1d(left, right))
                for left, right in zip(validated_runs, validated_runs[1:])
            ]
            temporal_score = min(scores)
            stability = {
                "status": "computed",
                "algorithm": "declared_category_order_adjacent_run_stability.v2",
                "run_count": len(validated_runs),
                "minimum_score": temporal_score,
                "maximum_wasserstein": max(dispersions),
                "run_ids": [run.run_id for run in claim_evidence.stability_runs],
                "seeds": [run.seed for run in claim_evidence.stability_runs],
                "claim_evidence_sha256": claim_evidence.sha256,
            }
        except (SnapshotValidationError, ArithmeticError, ValueError, OverflowError):
            claim_blockers.append("c3_stability_metrics_unavailable_or_invalid")

    c3_thresholds = {
        "mae_max": C3_MAX_MAE,
        "kl_max": C3_MAX_KL,
        "wasserstein_max": C3_MAX_WASSERSTEIN,
        "subgroup_error_max": C3_MAX_SUBGROUP_ERROR,
        "stability_min": C3_MIN_STABILITY,
    }
    calibration_thresholds_pass = bool(
        mae_val is not None
        and kl_val is not None
        and wasserstein_val is not None
        and mae_val <= C3_MAX_MAE
        and kl_val <= C3_MAX_KL
        and wasserstein_val <= C3_MAX_WASSERSTEIN
    )
    c2_ready = bool(
        baseline_snapshot is not None
        and baseline_kind == "distributions"
        and claim_evidence is not None
        and sample_values is not None
        and evidence_audit.get("passes_gate") is True
        and all(_is_finite_number(value) for value in (mae_val, kl_val, wasserstein_val))
        and calibration_thresholds_pass
    )
    c3_ready = bool(
        c2_ready
        and subgroup_metrics.get("status") == "computed"
        and stability.get("status") == "computed"
        and calibration_thresholds_pass
        and subgroup_max_error is not None
        and subgroup_max_error <= C3_MAX_SUBGROUP_ERROR
        and temporal_score is not None
        and temporal_score >= C3_MIN_STABILITY
    )
    prospective = _materialized_prospective_validation(claim_evidence)
    prospective_metrics_value = prospective.get("metrics")
    prospective_metrics: Mapping[str, Any] = (
        prospective_metrics_value
        if isinstance(prospective_metrics_value, Mapping)
        else {}
    )
    c4_ready = bool(
        c3_ready
        and prospective.get("status") == "measured"
        and prospective.get("heldout_count", 0) >= 30
        and isinstance(prospective.get("per_id_scoring"), Mapping)
        and prospective["per_id_scoring"].get("passes_thresholds") is True
        and all(
            _is_finite_number(prospective_metrics.get(name))
            and float(prospective_metrics[name]) <= threshold
            for name, threshold in {
                "mae": C3_MAX_MAE,
                "kl": C3_MAX_KL,
                "wasserstein": C3_MAX_WASSERSTEIN,
            }.items()
        )
    )
    if c2_ready and not c3_ready:
        claim_blockers.append("c3_subgroup_or_stability_evidence_not_eligible")
    if sample_values is not None and not calibration_thresholds_pass:
        claim_blockers.append("c2_calibration_thresholds_not_met")
    if c3_ready and not c4_ready:
        claim_blockers.append("c4_prospective_out_of_sample_evidence_not_measured")

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

    passes_execution_gate = bool(
        quality_gate.get("passes_gate") is True
        and replicator_input_valid
        and profiles > 0
        and actions > 0
        and robustness_score >= 0.45
        and evidence_passes is not False
        and not dpd_violation
        and blind["masked_in_prompt"] is not False
    )
    sample_hash = claim_evidence.evaluation_sample_sha256 if claim_evidence else None
    evidence_binding = {
        "report_id": report_id,
        "simulation_id": simulation_id,
        "run_id": run_id,
        "config_sha256": config_sha256,
        "baseline_snapshot_sha256": baseline_snapshot.sha256 if baseline_snapshot else None,
        "sample_sha256": sample_hash,
        "claim_evidence_sha256": claim_evidence.sha256 if claim_evidence else None,
        "authority_manifest_sha256": (
            claim_evidence.authority_manifest_sha256 if claim_evidence else None
        ),
        "baseline_snapshot_path": authority.baseline_path if claim_evidence and authority else None,
        "claim_evidence_path": authority.claim_evidence_path if claim_evidence and authority else None,
    }
    evidence_binding["binding_sha256"] = _canonical_sha256(evidence_binding)
    return {
        "schema": "mirofish.vox.fidelity_report.v3",
        "generated_at": generated_at,
        "overall_score": robustness_score,
        "baseline_validation_available": baseline_validation,
        "mean_absolute_error_pp": mae_val,
        "subgroup_max_error_pp": subgroup_max_error,
        "variance_ratio": round(max(0.5, min(1.0, (distinct + entropy + behavior_entropy) / 3)), 4)
        if any((distinct, entropy, behavior_entropy))
        else None,
        "seed_dispersion": None,
        "paraphrase_dispersion": None,
        "order_effect_score": None,
        "schema_failure_rate": 0.0 if actions > 0 else None,
        "passes_execution_gate": passes_execution_gate,
        "passes_gate": passes_execution_gate,
        "passes_gate_deprecation": "alias_of_passes_execution_gate; never implies C2+ calibration",
        "threshold_status": "green" if passes_execution_gate and robustness_score >= 0.7 else "yellow" if passes_execution_gate else "red",
        "measurement_mode": "trace_based_until_full_seed_paraphrase_matrix",
        "multi_metric": multi_metric,
        "dpd_max": dpd_max,
        "dpd_threshold": DPD_BLOCKER_THRESHOLD,
        "dpd_violation": dpd_violation,
        "blind_test": blind,
        "calibration_evidence": {
            "status": "measured" if c2_ready else "planned",
            "snapshot": baseline_snapshot.public_summary() if baseline_snapshot else None,
            "claim_evidence": claim_evidence.public_summary() if claim_evidence else None,
            "metrics": {
                "mae": _metric_evidence("mean_absolute_error.v1", mae_val, baseline_snapshot, sample_values),
                "kl": _metric_evidence("kl_divergence.v1", kl_val, baseline_snapshot, sample_values),
                "wasserstein": _metric_evidence(
                    "categorical_wasserstein_declared_order.v2",
                    wasserstein_val,
                    baseline_snapshot,
                    sample_values,
                ),
            },
        },
        "subgroup_evidence": subgroup_metrics,
        "stability_evidence": stability,
        "prospective_evidence": prospective,
        "claim_eligibility": {"C2": c2_ready, "C3": c3_ready, "C4": c4_ready},
        "claim_blockers": sorted(set(claim_blockers)),
        "c3_thresholds": c3_thresholds,
        "evidence_binding": evidence_binding,
    }


def _metric_evidence(
    algorithm: str,
    value: float | None,
    snapshot: BaselineSnapshot | None,
    sample: Sequence[float] | None,
) -> dict[str, Any]:
    if snapshot is None or sample is None or not _is_finite_number(value):
        return {"status": "planned", "algorithm": algorithm, "value": None}
    return {
        "status": "computed",
        "algorithm": algorithm,
        "value": value,
        "baseline_snapshot_sha256": snapshot.sha256,
        "observed_n": len(snapshot.observed),
        "synthetic_n": len(sample),
        "variable_id": snapshot.variable_id,
    }


def _materialized_prospective_validation(
    evidence: ClaimEvidence | None,
) -> dict[str, Any]:
    if evidence is None or evidence.prospective is None:
        return {"status": "planned", "reason": "materialized_prospective_evidence_missing"}
    value = evidence.prospective
    try:
        observed = list(value["observed_distribution"])
        predicted = list(value["predicted_distribution"])
        categories = list(value["categories"])
        heldout_ids = list(value["heldout_ids"])
        observed_by_id = value["observed_by_id"]
        predicted_by_id = value["predicted_by_id"]
        baseline_distribution = list(value["baseline_distribution"])
        performance_criteria = value["performance_criteria"]
        if (
            not isinstance(observed_by_id, Mapping)
            or not isinstance(predicted_by_id, Mapping)
            or set(observed_by_id) != set(heldout_ids)
            or set(predicted_by_id) != set(heldout_ids)
            or len(categories) < 2
        ):
            raise ValueError("prospective_per_id_binding_invalid")
        predictions = [list(predicted_by_id[item]) for item in heldout_ids]
        observed_indices = [categories.index(observed_by_id[item]) for item in heldout_ids]
        brier = _finite_metric(multiclass_brier_score(predictions, observed_indices))
        log_loss = _finite_metric(multiclass_log_loss(predictions, observed_indices))
        baseline_predictions = [baseline_distribution for _ in heldout_ids]
        baseline_brier = _finite_metric(
            multiclass_brier_score(baseline_predictions, observed_indices)
        )
        baseline_log_loss = _finite_metric(
            multiclass_log_loss(baseline_predictions, observed_indices)
        )
        brier_skill = _finite_metric(
            1.0 - brier / baseline_brier if baseline_brier > 0 else 0.0
        )
        log_loss_ratio = _finite_metric(
            log_loss / baseline_log_loss if baseline_log_loss > 0 else math.inf
        )
        passes_per_id = _passes_preregistered_performance(
            brier_skill=brier_skill,
            log_loss=log_loss,
            baseline_log_loss=baseline_log_loss,
            criteria=performance_criteria,
        )
        metrics = {
            "mae": _finite_metric(mean_absolute_error(observed, predicted)),
            "kl": _finite_metric(kl_divergence(observed, predicted)),
            "wasserstein": _finite_metric(
                categorical_wasserstein_1d(observed, predicted)
            ),
            "brier_score": brier,
            "log_loss": log_loss,
        }
    except (KeyError, ArithmeticError, ValueError, OverflowError):
        return {"status": "invalid", "reason": "prospective_metrics_unavailable_or_invalid"}
    return {
        "status": "measured",
        "mode": value["mode"],
        "preregistration_id": value["preregistration_id"],
        "preregistered_at": value["preregistered_at"],
        "training_cutoff": value["training_cutoff"],
        "evaluated_at": value["evaluated_at"],
        "heldout_ids": heldout_ids,
        "heldout_count": len(heldout_ids),
        "metrics": metrics,
        "per_id_scoring": {
            "algorithm": C4_PER_ID_SCORING_VERSION,
            "passes_thresholds": passes_per_id,
            "brier_score": brier,
            "log_loss": log_loss,
            "baseline_brier_score": baseline_brier,
            "baseline_log_loss": baseline_log_loss,
            "brier_skill_score": brier_skill,
            "log_loss_ratio": log_loss_ratio,
            "preregistered_criteria": dict(performance_criteria),
            "category_count": len(categories),
        },
        "sample_sha256": value["sample_sha256"],
        "forecast_sha256": value["forecast_sha256"],
        "preregistration_receipt_sha256": value[
            "preregistration_receipt_sha256"
        ],
        "claim_evidence_sha256": evidence.sha256,
        "authority_manifest_sha256": evidence.authority_manifest_sha256,
    }


def _passes_preregistered_performance(
    *,
    brier_skill: float,
    log_loss: float,
    baseline_log_loss: float,
    criteria: Mapping[str, Any],
) -> bool:
    """Apply only material-effect floors signed into the pre-cutoff receipt."""

    minimum_skill = criteria.get("minimum_brier_skill_score")
    maximum_ratio = criteria.get("maximum_log_loss_ratio")
    if (
        isinstance(minimum_skill, bool)
        or not isinstance(minimum_skill, (int, float))
        or isinstance(maximum_ratio, bool)
        or not isinstance(maximum_ratio, (int, float))
    ):
        return False
    return bool(
        criteria.get("policy_id") == C4_MATERIAL_POLICY_ID
        and criteria.get("algorithm") == C4_PER_ID_SCORING_VERSION
        and _is_finite_number(brier_skill)
        and _is_finite_number(log_loss)
        and _is_finite_number(baseline_log_loss)
        and baseline_log_loss > 0
        and _is_finite_number(minimum_skill)
        and _is_finite_number(maximum_ratio)
        and float(brier_skill) >= float(minimum_skill)
        and float(log_loss) <= float(baseline_log_loss) * float(maximum_ratio)
    )


def _safe_dpd(rates: Mapping[str, float] | None) -> dict[str, Any] | None:
    if not isinstance(rates, Mapping) or not 2 <= len(rates) <= MAX_EVIDENCE_ITEMS:
        return None
    clean: dict[str, float] = {}
    for group, value in rates.items():
        if not isinstance(group, str) or not group or not _is_finite_number(value):
            return None
        numeric = float(value)
        if not 0.0 <= numeric <= 1.0:
            return None
        clean[group] = numeric
    return demographic_parity_difference(clean)


def _safe_intra_group_variance(
    groups: Mapping[str, Sequence[float]] | None,
) -> dict[str, float] | None:
    if not isinstance(groups, Mapping) or not 1 <= len(groups) <= MAX_EVIDENCE_ITEMS:
        return None
    clean: dict[str, list[float]] = {}
    try:
        for group, values in groups.items():
            if not isinstance(group, str) or not group:
                return None
            clean[group] = validate_numeric_vector(values, reason="group_values_invalid")
    except SnapshotValidationError:
        return None
    return intra_group_variance(clean)


def _finite_metric(value: Any) -> float:
    if not _is_finite_number(value):
        raise ValueError("metric_not_finite")
    return round(float(value), 6)


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


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
    target_norm = _normalized_prompt_text(target_variable)
    aliases = {target_norm, target_norm.replace("_", " "), target_norm.replace(" ", "_")}
    prompt_text = " ".join(
        _iter_prompt_bearing_strings(prompt_registry.get("questions", []))
    )
    prompt_norm = _normalized_prompt_text(prompt_text)
    leak_detected = any(alias and alias in prompt_norm for alias in aliases)
    return {
        "target_variable": target_variable,
        "masked_in_prompt": not leak_detected,
        "recovery_score": 0.0 if not leak_detected else 1.0,
        "method": "recursive_normalized_alias_scan.v1",
    }


def _pimmur_audit(
    quality_gate: Mapping[str, Any],
    anchors: Sequence[Mapping[str, Any]],
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
    baselines: Sequence[Mapping[str, Any]],
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
    claim_level = _claim_level(fidelity, pimmur, compost)

    blocked_claims: list[dict[str, Any]] = []
    overrides = evidence_overrides if isinstance(evidence_overrides, Mapping) else {}
    if isinstance(reported_correlations, Mapping):
        if len(reported_correlations) > MAX_EVIDENCE_ITEMS:
            blocked_claims.append({"reason": "correlation_item_budget_exceeded"})
        for construct, value in reported_correlations.items():
            if not isinstance(construct, str) or not construct or not _is_finite_number(value):
                blocked_claims.append(
                    {"construct": str(construct), "reason": "correlation_value_invalid"}
                )
                continue
            numeric = float(value)
            if numeric > CORRELATION_ALERT_THRESHOLD and not _valid_evidence_override(
                overrides.get(construct), construct
            ):
                blocked_claims.append(
                    {
                        "construct": construct,
                        "reported_correlation": numeric,
                        "threshold": CORRELATION_ALERT_THRESHOLD,
                        "reason": "correlation_above_ceiling_without_external_evidence",
                    }
                )

    if blocked_claims:
        claim_level = "C1" if fidelity.get("passes_execution_gate") is True else "C0"
    return {
        "schema": "mirofish.vox.claim_policy_audit.v3",
        "generated_at": generated_at,
        "passes_claim_policy": not blocked_claims,
        "passes_gate": not blocked_claims,
        "passes_gate_deprecation": "alias_of_passes_claim_policy; not an execution or calibration result",
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
        "evidence_binding": fidelity.get("evidence_binding"),
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
    baselines: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if quality_gate.get("passes_gate") is not True:
        blockers.append("system_gate_not_passed")
    if evidence_audit and evidence_audit.get("passes_gate") is not True:
        blockers.append("evidence_audit_not_passed")
    if pimmur.get("passes_gate") is not True:
        blockers.append("pimmur_audit_not_passed")
    if compost.get("passes_gate") is not True:
        blockers.append("compost_audit_not_passed")
    if fidelity.get("passes_execution_gate") is not True:
        blockers.append("fidelity_execution_gate_not_passed")
    if fidelity.get("measurement_mode") == "trace_based_until_full_seed_paraphrase_matrix":
        warnings.append("full_seed_paraphrase_matrix_pending")
    if fidelity.get("mean_absolute_error_pp") is None:
        warnings.append("external_baseline_error_not_measured_yet")
    # R2 — blocker: demographic parity violation.
    if fidelity.get("dpd_violation"):
        blockers.append("demographic_parity_violation")
    # R8 — blind test leak.
    blind_value = fidelity.get("blind_test")
    blind: Mapping[str, Any] = blind_value if isinstance(blind_value, Mapping) else {}
    if blind.get("masked_in_prompt") is False:
        blockers.append("blind_test_leak")
    # R5 — blocked claims by epistemic ceiling.
    claim_blockers = list(fidelity.get("claim_blockers") or [])
    if claim_policy.get("blocked_claims"):
        claim_blockers.append("claim_policy_rejected_assertion")

    passes_execution_gate = not blockers
    claim_level = str(claim_policy.get("claim_level") or "C0")
    if not passes_execution_gate:
        claim_level = "C0"
    elif claim_policy.get("passes_claim_policy") is not True:
        claim_level = "C1"
    return {
        "schema": "mirofish.vox.harness_science_gate.v2",
        "generated_at": generated_at,
        "passes_execution_gate": passes_execution_gate,
        "passes_gate": passes_execution_gate,
        "passes_gate_deprecation": "legacy alias of passes_execution_gate only; never implies C2+",
        "claim_level": claim_level,
        "max_external_language": _allowed_language(claim_level)[0],
        "blockers": blockers,
        "claim_blockers": sorted(set(claim_blockers)),
        "evidence_binding": fidelity.get("evidence_binding"),
        "prospective_validation": fidelity.get("prospective_evidence"),
        "warnings": warnings,
        "required_artifacts": list(VOX_SCIENCE_FILENAMES),
        "new_human_collection": False,
        "next_upgrade": "rodar matriz completa de seeds e parafrases para elevar confianca quantitativa",
    }


def _claim_level(
    fidelity: Mapping[str, Any],
    pimmur: Mapping[str, Any],
    compost: Mapping[str, Any],
) -> str:
    if not (pimmur.get("passes_gate") and compost.get("passes_gate")):
        return "C0"
    if fidelity.get("passes_execution_gate") is not True:
        return "C0"
    eligibility = fidelity.get("claim_eligibility")
    if isinstance(eligibility, Mapping):
        if eligibility.get("C4") is True:
            return "C4"
        if eligibility.get("C3") is True:
            return "C3"
        if eligibility.get("C2") is True:
            return "C2"
    return "C1"


def _allowed_language(claim_level: str) -> list[str]:
    table = {
        "C0": ["mapa qualitativo de sinais e friccoes sinteticas"],
        "C1": ["simulacao sintetica exploratoria com rastreabilidade metodologica"],
        "C2": ["simulacao sintetica calibrada por dados publicos e robustez auditada"],
        "C3": ["estimativa sintetica calibrada por baseline publico comparavel"],
        "C4": ["previsao operacional monitoravel com cenario base e tese adversaria"],
    }
    return table.get(claim_level, table["C0"])


def _iter_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        out: list[str] = []
        for key, nested in value.items():
            out.extend(_iter_string_values(key))
            out.extend(_iter_string_values(nested))
        return out
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        out = []
        for nested in value:
            out.extend(_iter_string_values(nested))
        return out
    return []


def _iter_prompt_bearing_strings(
    value: Any, path: tuple[Any, ...] = ()
) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        out: list[str] = []
        for key, nested in value.items():
            # Only the declared metadata field on each top-level question is
            # excluded. A nested prompt field with the same key is content.
            if len(path) == 1 and isinstance(path[0], int) and key == "target_variable":
                continue
            out.extend(_iter_prompt_bearing_strings(key, path + (key,)))
            out.extend(_iter_prompt_bearing_strings(nested, path + (key,)))
        return out
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        out = []
        for index, nested in enumerate(value):
            out.extend(_iter_prompt_bearing_strings(nested, path + (index,)))
        return out
    return []


def _normalized_prompt_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", decomposed.lower()).strip()


def _valid_evidence_override(value: Any, construct: str) -> bool:
    # Legacy inline overrides are diagnostic only. Promotion requires a future
    # authority-manifest artifact contract, never a caller string plus digest.
    return False


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
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    numeric = float(value)
    if not math.isfinite(numeric):
        return default
    return max(0, int(numeric))


def _float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    numeric = float(value)
    return numeric if math.isfinite(numeric) else default


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
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
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
