"""Strict materialized evidence bundle for Vox C2-C4 claims."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from .baseline_snapshot import (
    BaselineSnapshot,
    SnapshotValidationError,
    canonical_json_bytes,
    load_materialized_json,
    revalidate_materialized_json,
    validate_probability_distribution,
)
from .preregistered_forecast import load_preregistered_forecast
from .verification import (
    C4_MATERIAL_POLICY_ID,
    MAX_ALLOWED_LOG_LOSS_RATIO,
    MIN_ALLOWED_BRIER_SKILL_SCORE,
    PREREGISTERED_SCORING_ALGORITHM,
    load_preregistration_receipt,
)


CLAIM_EVIDENCE_SCHEMA = "mirofish.vox.claim_evidence_bundle.v1"
MIN_STABILITY_RUNS = 3
MIN_EVALUATION_N = 30
MIN_SUBGROUP_N = 30
MIN_PROSPECTIVE_N = 30
MAX_IDS = 10_000


@dataclass(frozen=True)
class StabilityRun:
    run_id: str
    seed: int
    distribution: tuple[float, ...]
    sample_sha256: str
    artifact_path: str
    artifact_sha256: str
    sample_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClaimEvidence:
    sha256: str
    authority_manifest_sha256: str
    evaluation_observed: tuple[float, ...]
    evaluation_predicted: tuple[float, ...]
    evaluation_sample_sha256: str
    evaluation_sample_ids: tuple[str, ...]
    subgroup_predictions: Mapping[str, tuple[float, ...]]
    subgroup_sample_sizes: Mapping[str, int]
    stability_runs: tuple[StabilityRun, ...]
    prospective: Mapping[str, Any] | None

    def public_summary(self) -> dict[str, Any]:
        return {
            "status": "measured",
            "schema": CLAIM_EVIDENCE_SCHEMA,
            "sha256": self.sha256,
            "authority_manifest_sha256": self.authority_manifest_sha256,
            "evaluation_sample_sha256": self.evaluation_sample_sha256,
            "evaluation_n": len(self.evaluation_sample_ids),
            "stability_run_count": len(self.stability_runs),
            "subgroups": sorted(self.subgroup_predictions),
            "prospective_status": "measured" if self.prospective else "planned",
        }


def load_claim_evidence(
    *,
    relative_path: str,
    trusted_root: str,
    expected_sha256: str,
    authority_manifest_sha256: str,
    baseline_snapshot: BaselineSnapshot,
    expected_report_id: str,
    expected_simulation_id: str,
    expected_run_id: str,
    expected_config_sha256: str,
    expected_input_sha256: str,
    authorized_stability_runs: Mapping[str, str],
    authorized_preregistered_forecasts: Mapping[str, str],
) -> ClaimEvidence:
    materialized = load_materialized_json(
        relative_path=relative_path,
        trusted_root=trusted_root,
        expected_sha256=expected_sha256,
        reason_prefix="claim_evidence",
    )
    payload = materialized.payload
    _exact_keys(payload, {"schema", "version", "generated_at", "binding", "evaluation", "stability", "prospective"})
    if payload["schema"] != CLAIM_EVIDENCE_SCHEMA or payload["version"] != 1:
        raise SnapshotValidationError("claim_evidence_schema_invalid")
    generated_at = _aware_datetime(payload["generated_at"], "claim_evidence_generated_at_invalid")

    binding = _mapping(payload["binding"], "claim_evidence_binding_invalid")
    _exact_keys(
        binding,
        {"report_id", "simulation_id", "run_id", "config_sha256", "input_sha256", "baseline_snapshot_sha256"},
    )
    expected_binding = {
        "report_id": expected_report_id,
        "simulation_id": expected_simulation_id,
        "run_id": expected_run_id,
        "config_sha256": expected_config_sha256,
        "input_sha256": expected_input_sha256,
        "baseline_snapshot_sha256": baseline_snapshot.sha256,
    }
    if dict(binding) != expected_binding:
        raise SnapshotValidationError("claim_evidence_binding_mismatch")

    categories = _snapshot_categories(baseline_snapshot)
    evaluation = _mapping(payload["evaluation"], "claim_evaluation_invalid")
    _exact_keys(
        evaluation,
        {"evaluation_id", "variable_id", "variable_label", "categories", "evaluated_at", "sample_ids", "observed_distribution", "predicted_distribution", "sample_sha256"},
    )
    if (
        evaluation["variable_id"] != baseline_snapshot.variable_id
        or evaluation["variable_label"] != _snapshot_variable_label(baseline_snapshot)
        or evaluation["categories"] != categories
    ):
        raise SnapshotValidationError("claim_evaluation_dimensions_unlabeled_or_mismatch")
    _nonempty_string(evaluation["evaluation_id"], "claim_evaluation_id_invalid")
    _aware_datetime(evaluation["evaluated_at"], "claim_evaluation_time_invalid")
    sample_ids = _unique_ids(
        evaluation["sample_ids"],
        minimum=MIN_EVALUATION_N,
        reason="claim_evaluation_sample_ids_invalid",
    )
    observed = validate_probability_distribution(
        evaluation["observed_distribution"],
        expected_length=len(baseline_snapshot.observed),
        reason="claim_evaluation_observed_invalid",
    )
    predicted = validate_probability_distribution(
        evaluation["predicted_distribution"],
        expected_length=len(observed),
        reason="claim_evaluation_predicted_invalid",
    )
    if observed != list(baseline_snapshot.observed):
        raise SnapshotValidationError("claim_evaluation_observed_not_baseline")
    evaluation_hash = vector_sha256(predicted)
    if evaluation.get("sample_sha256") != evaluation_hash:
        raise SnapshotValidationError("claim_evaluation_sample_hash_mismatch")

    subgroup_predictions: dict[str, tuple[float, ...]] = {}
    subgroup_sizes: dict[str, int] = {}
    stability_runs: tuple[StabilityRun, ...] = ()
    stability_raw = payload["stability"]
    if stability_raw is not None:
        stability_runs, subgroup_predictions, subgroup_sizes = _validate_stability(
            stability_raw,
            baseline_snapshot=baseline_snapshot,
            expected_config_sha256=expected_config_sha256,
            expected_input_sha256=expected_input_sha256,
            expected_report_id=expected_report_id,
            expected_simulation_id=expected_simulation_id,
            trusted_root=trusted_root,
            authorized_runs=authorized_stability_runs,
        )

    prospective = None
    if payload["prospective"] is not None:
        prospective = _validate_prospective(
            payload["prospective"],
            baseline_snapshot=baseline_snapshot,
            expected_report_id=expected_report_id,
            expected_simulation_id=expected_simulation_id,
            expected_run_id=expected_run_id,
            expected_config_sha256=expected_config_sha256,
            expected_input_sha256=expected_input_sha256,
            evidence_generated_at=generated_at,
            trusted_root=trusted_root,
            authorized_forecasts=authorized_preregistered_forecasts,
        )
    revalidate_materialized_json(materialized, reason_prefix="claim_evidence")
    return ClaimEvidence(
        sha256=materialized.sha256,
        authority_manifest_sha256=authority_manifest_sha256,
        evaluation_observed=tuple(observed),
        evaluation_predicted=tuple(predicted),
        evaluation_sample_sha256=evaluation_hash,
        evaluation_sample_ids=tuple(sample_ids),
        subgroup_predictions=subgroup_predictions,
        subgroup_sample_sizes=subgroup_sizes,
        stability_runs=stability_runs,
        prospective=prospective,
    )


def vector_sha256(values: Sequence[float]) -> str:
    return hashlib.sha256(canonical_json_bytes({"values": list(values)})).hexdigest()


def _validate_stability(
    raw: Any,
    *,
    baseline_snapshot: BaselineSnapshot,
    expected_config_sha256: str,
    expected_input_sha256: str,
    expected_report_id: str,
    expected_simulation_id: str,
    trusted_root: str,
    authorized_runs: Mapping[str, str],
) -> tuple[tuple[StabilityRun, ...], dict[str, tuple[float, ...]], dict[str, int]]:
    value = _mapping(raw, "claim_stability_invalid")
    _exact_keys(value, {"runs", "subgroups"})
    runs_raw = value["runs"]
    if not isinstance(runs_raw, list) or not MIN_STABILITY_RUNS <= len(runs_raw) <= 32:
        raise SnapshotValidationError("claim_stability_run_count_invalid")
    runs: list[StabilityRun] = []
    run_ids: set[str] = set()
    seeds: set[int] = set()
    for raw_run in runs_raw:
        run = _mapping(raw_run, "claim_stability_run_invalid")
        _exact_keys(run, {"run_id", "seed", "artifact_path", "artifact_sha256"})
        _nonempty_string(run["run_id"], "claim_stability_run_id_invalid")
        if run["run_id"] in run_ids or isinstance(run["seed"], bool) or not isinstance(run["seed"], int) or run["seed"] in seeds:
            raise SnapshotValidationError("claim_stability_run_or_seed_duplicate")
        artifact_path = run["artifact_path"]
        artifact_sha256 = run["artifact_sha256"]
        if authorized_runs.get(artifact_path) != artifact_sha256:
            raise SnapshotValidationError("claim_stability_run_not_authorized")
        materialized = load_materialized_json(
            relative_path=artifact_path,
            trusted_root=trusted_root,
            expected_sha256=artifact_sha256,
            reason_prefix="claim_stability_run",
        )
        run_payload = _mapping(materialized.payload, "claim_stability_run_artifact_invalid")
        _exact_keys(
            run_payload,
            {
                "schema", "version", "generated_at", "report_id", "simulation_id",
                "run_id", "seed", "input_sha256", "config_sha256",
                "baseline_snapshot_sha256", "variable_id", "variable_label",
                "categories", "sample_ids", "distribution", "sample_sha256",
            },
        )
        if (
            run_payload["schema"] != "mirofish.vox.stability_run.v1"
            or run_payload["version"] != 1
            or run_payload["report_id"] != expected_report_id
            or run_payload["simulation_id"] != expected_simulation_id
            or run_payload["run_id"] != run["run_id"]
            or run_payload["seed"] != run["seed"]
            or run_payload["input_sha256"] != expected_input_sha256
            or run_payload["config_sha256"] != expected_config_sha256
            or run_payload["baseline_snapshot_sha256"] != baseline_snapshot.sha256
            or run_payload["variable_id"] != baseline_snapshot.variable_id
            or run_payload["variable_label"] != _snapshot_variable_label(baseline_snapshot)
            or run_payload["categories"] != _snapshot_categories(baseline_snapshot)
        ):
            raise SnapshotValidationError("claim_stability_binding_mismatch")
        _aware_datetime(run_payload["generated_at"], "claim_stability_generated_at_invalid")
        run_sample_ids = _unique_ids(
            run_payload["sample_ids"],
            minimum=MIN_EVALUATION_N,
            reason="claim_stability_sample_ids_invalid",
        )
        distribution = validate_probability_distribution(
            run_payload["distribution"],
            expected_length=len(baseline_snapshot.observed),
            reason="claim_stability_distribution_invalid",
        )
        digest = vector_sha256(distribution)
        if run_payload["sample_sha256"] != digest:
            raise SnapshotValidationError("claim_stability_sample_hash_mismatch")
        revalidate_materialized_json(materialized, reason_prefix="claim_stability_run")
        run_ids.add(run["run_id"])
        seeds.add(run["seed"])
        runs.append(
            StabilityRun(
                run["run_id"], run["seed"], tuple(distribution), digest,
                artifact_path, artifact_sha256, tuple(run_sample_ids),
            )
        )

    subgroup_raw = _mapping(value["subgroups"], "claim_subgroups_invalid")
    expected_groups = set(baseline_snapshot.subgroup_observed)
    if len(expected_groups) < 2 or set(subgroup_raw) != expected_groups:
        raise SnapshotValidationError("claim_subgroup_set_invalid")
    predictions: dict[str, tuple[float, ...]] = {}
    sizes: dict[str, int] = {}
    for group, raw_group in subgroup_raw.items():
        item = _mapping(raw_group, "claim_subgroup_invalid")
        _exact_keys(item, {"predicted_n", "sample_ids", "observed_distribution", "predicted_distribution", "sample_sha256"})
        sample_ids = _unique_ids(
            item["sample_ids"], minimum=MIN_SUBGROUP_N,
            reason="claim_subgroup_sample_ids_invalid",
        )
        n = item["predicted_n"]
        if isinstance(n, bool) or not isinstance(n, int) or n != len(sample_ids):
            raise SnapshotValidationError("claim_subgroup_n_invalid")
        observed = validate_probability_distribution(
            item["observed_distribution"],
            expected_length=len(baseline_snapshot.subgroup_observed[group]),
            reason="claim_subgroup_observed_invalid",
        )
        predicted = validate_probability_distribution(
            item["predicted_distribution"],
            expected_length=len(observed),
            reason="claim_subgroup_predicted_invalid",
        )
        if observed != list(baseline_snapshot.subgroup_observed[group]):
            raise SnapshotValidationError("claim_subgroup_observed_not_baseline")
        digest = vector_sha256(predicted)
        if item["sample_sha256"] != digest:
            raise SnapshotValidationError("claim_subgroup_sample_hash_mismatch")
        predictions[group] = tuple(predicted)
        sizes[group] = n
    return tuple(runs), predictions, sizes


def _validate_prospective(
    raw: Any,
    *,
    baseline_snapshot: BaselineSnapshot,
    expected_report_id: str,
    expected_simulation_id: str,
    expected_run_id: str,
    expected_config_sha256: str,
    expected_input_sha256: str,
    evidence_generated_at: datetime,
    trusted_root: str,
    authorized_forecasts: Mapping[str, str],
) -> Mapping[str, Any]:
    value = _mapping(raw, "claim_prospective_invalid")
    _exact_keys(
        value,
        {"status", "mode", "preregistration_id", "preregistration_receipt_path", "preregistration_receipt_sha256", "training_cutoff", "evaluated_at", "heldout_times", "report_id", "simulation_id", "run_id", "config_sha256", "input_sha256", "baseline_snapshot_sha256", "training_ids", "heldout_ids", "observed_outcomes"},
    )
    if value["status"] != "measured" or value["mode"] != "prospective_out_of_sample":
        raise SnapshotValidationError("claim_prospective_not_measured_oos")
    _nonempty_string(value["preregistration_id"], "claim_preregistration_id_invalid")
    cutoff = _aware_datetime(value["training_cutoff"], "claim_training_cutoff_invalid")
    evaluated = _aware_datetime(value["evaluated_at"], "claim_evaluated_at_invalid")
    if not cutoff < evaluated or evidence_generated_at < evaluated:
        raise SnapshotValidationError("claim_prospective_time_order_invalid")
    if (
        value["report_id"] != expected_report_id
        or value["simulation_id"] != expected_simulation_id
        or value["run_id"] != expected_run_id
        or value["config_sha256"] != expected_config_sha256
        or value["input_sha256"] != expected_input_sha256
        or value["baseline_snapshot_sha256"] != baseline_snapshot.sha256
    ):
        raise SnapshotValidationError("claim_prospective_binding_mismatch")
    training_ids = _unique_ids(value["training_ids"], minimum=1, reason="claim_training_ids_invalid")
    heldout_ids = _unique_ids(
        value["heldout_ids"], minimum=MIN_PROSPECTIVE_N, reason="claim_heldout_ids_invalid"
    )
    if set(training_ids) & set(heldout_ids):
        raise SnapshotValidationError("claim_heldout_overlaps_training")
    heldout_times_raw = value["heldout_times"]
    if not isinstance(heldout_times_raw, list) or len(heldout_times_raw) != len(heldout_ids):
        raise SnapshotValidationError("claim_heldout_times_invalid")
    heldout_times = [
        _aware_datetime(item, "claim_heldout_times_invalid") for item in heldout_times_raw
    ]
    if any(not cutoff <= item <= evaluated for item in heldout_times):
        raise SnapshotValidationError("claim_heldout_times_outside_window")
    receipt_path = value["preregistration_receipt_path"]
    receipt_sha = value["preregistration_receipt_sha256"]
    receipt = load_preregistration_receipt(
        relative_path=receipt_path,
        expected_sha256=receipt_sha,
        expected_report_id=expected_report_id,
        expected_preregistration_id=value["preregistration_id"],
    )
    _exact_keys(
        receipt,
        {
            "schema", "version", "issued_at", "preregistration_id", "report_id",
            "simulation_id", "run_id", "config_sha256", "input_sha256",
            "baseline_snapshot_sha256", "training_cutoff", "heldout_plan_ids",
            "forecast_path", "forecast_sha256", "performance_criteria",
            "signature_algorithm", "hmac_sha256",
        },
    )
    issued_at = _aware_datetime(receipt["issued_at"], "claim_preregistration_issued_at_invalid")
    criteria = _mapping(
        receipt["performance_criteria"],
        "claim_preregistration_performance_criteria_invalid",
    )
    _exact_keys(
        criteria,
        {
            "policy_id",
            "algorithm",
            "minimum_brier_skill_score",
            "maximum_log_loss_ratio",
        },
    )
    minimum_skill = criteria["minimum_brier_skill_score"]
    maximum_ratio = criteria["maximum_log_loss_ratio"]
    if (
        criteria["policy_id"] != C4_MATERIAL_POLICY_ID
        or criteria["algorithm"] != PREREGISTERED_SCORING_ALGORITHM
        or isinstance(minimum_skill, bool)
        or not isinstance(minimum_skill, (int, float))
        or not math.isfinite(float(minimum_skill))
        or not MIN_ALLOWED_BRIER_SKILL_SCORE <= float(minimum_skill) <= 1.0
        or isinstance(maximum_ratio, bool)
        or not isinstance(maximum_ratio, (int, float))
        or not math.isfinite(float(maximum_ratio))
        or not 0.0 < float(maximum_ratio) <= MAX_ALLOWED_LOG_LOSS_RATIO
    ):
        raise SnapshotValidationError("claim_preregistration_performance_criteria_invalid")
    if (
        not issued_at < cutoff
        or receipt["preregistration_id"] != value["preregistration_id"]
        or receipt["report_id"] != expected_report_id
        or receipt["simulation_id"] != expected_simulation_id
        or receipt["run_id"] != expected_run_id
        or receipt["config_sha256"] != expected_config_sha256
        or receipt["input_sha256"] != expected_input_sha256
        or receipt["baseline_snapshot_sha256"] != baseline_snapshot.sha256
        or receipt["training_cutoff"] != value["training_cutoff"]
        or receipt["heldout_plan_ids"] != heldout_ids
    ):
        raise SnapshotValidationError("claim_preregistration_receipt_binding_invalid")
    forecast_path = receipt["forecast_path"]
    forecast_sha = receipt["forecast_sha256"]
    if authorized_forecasts.get(forecast_path) != forecast_sha:
        raise SnapshotValidationError("claim_preregistered_forecast_not_authorized")
    forecast = load_preregistered_forecast(
        relative_path=forecast_path,
        trusted_root=trusted_root,
        expected_sha256=forecast_sha,
        baseline_snapshot=baseline_snapshot,
        expected_report_id=expected_report_id,
        expected_simulation_id=expected_simulation_id,
        expected_run_id=expected_run_id,
        expected_config_sha256=expected_config_sha256,
        expected_input_sha256=expected_input_sha256,
        expected_training_cutoff=value["training_cutoff"],
    )
    if list(forecast.heldout_ids) != heldout_ids:
        raise SnapshotValidationError("claim_forecast_heldout_order_mismatch")
    outcomes = value["observed_outcomes"]
    if not isinstance(outcomes, list) or len(outcomes) != len(heldout_ids):
        raise SnapshotValidationError("claim_observed_outcomes_invalid")
    categories = _snapshot_categories(baseline_snapshot)
    counts = [0.0] * len(categories)
    observed_by_id: dict[str, str] = {}
    for expected_id, outcome in zip(heldout_ids, outcomes):
        if (
            not isinstance(outcome, Mapping)
            or set(outcome) != {"id", "value"}
            or outcome["id"] != expected_id
            or outcome["value"] not in categories
        ):
            raise SnapshotValidationError("claim_observed_outcomes_id_or_value_invalid")
        observed_by_id[expected_id] = outcome["value"]
        counts[categories.index(outcome["value"])] += 1.0
    observed = [count / len(outcomes) for count in counts]
    predicted = list(forecast.predicted_distribution)
    return {
        "status": "measured",
        "mode": "prospective_out_of_sample",
        "preregistration_id": value["preregistration_id"],
        "preregistered_at": receipt["issued_at"],
        "training_cutoff": value["training_cutoff"],
        "evaluated_at": value["evaluated_at"],
        "training_ids": tuple(training_ids),
        "heldout_ids": tuple(heldout_ids),
        "heldout_times": tuple(value["heldout_times"]),
        "preregistration_receipt_sha256": receipt_sha,
        "forecast_sha256": forecast.sha256,
        "observed_distribution": tuple(observed),
        "predicted_distribution": tuple(predicted),
        "categories": tuple(categories),
        "observed_by_id": observed_by_id,
        "predicted_by_id": dict(forecast.predicted_by_id),
        "baseline_distribution": tuple(baseline_snapshot.observed),
        "performance_criteria": dict(criteria),
        "sample_sha256": vector_sha256(predicted),
    }


def _snapshot_categories(snapshot: BaselineSnapshot) -> list[str]:
    for variable in snapshot.payload["variables"]:
        if variable["id"] == snapshot.variable_id:
            return list(variable["categories"])
    raise SnapshotValidationError("claim_snapshot_categories_missing")


def _snapshot_variable_label(snapshot: BaselineSnapshot) -> str:
    for variable in snapshot.payload["variables"]:
        if variable["id"] == snapshot.variable_id:
            return str(variable["label"])
    raise SnapshotValidationError("claim_snapshot_variable_label_missing")


def _unique_ids(value: Any, *, minimum: int, reason: str) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= MAX_IDS:
        raise SnapshotValidationError(reason)
    if any(not isinstance(item, str) or not item for item in value) or len(set(value)) != len(value):
        raise SnapshotValidationError(reason)
    return value


def _aware_datetime(value: Any, reason: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise SnapshotValidationError(reason)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotValidationError(reason) from exc
    if parsed.tzinfo is None:
        raise SnapshotValidationError(reason)
    return parsed


def _mapping(value: Any, reason: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SnapshotValidationError(reason)
    return value


def _exact_keys(value: Mapping[str, Any], required: set[str]) -> None:
    if set(value) != required:
        raise SnapshotValidationError("claim_evidence_schema_keys_mismatch")


def _nonempty_string(value: Any, reason: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotValidationError(reason)


__all__ = [
    "CLAIM_EVIDENCE_SCHEMA",
    "ClaimEvidence",
    "MIN_PROSPECTIVE_N",
    "MIN_STABILITY_RUNS",
    "load_claim_evidence",
    "vector_sha256",
]
