"""Strict pre-outcome forecast committed for Vox C4 evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .baseline_snapshot import (
    BaselineSnapshot,
    SnapshotValidationError,
    load_materialized_json,
    revalidate_materialized_json,
    validate_probability_distribution,
)


FORECAST_SCHEMA = "mirofish.vox.preregistered_forecast.v1"
MIN_FORECAST_N = 30
MAX_FORECAST_N = 10_000


@dataclass(frozen=True)
class PreregisteredForecast:
    sha256: str
    generated_at: datetime
    heldout_ids: tuple[str, ...]
    predicted_by_id: Mapping[str, tuple[float, ...]]
    predicted_distribution: tuple[float, ...]


def load_preregistered_forecast(
    *,
    relative_path: str,
    trusted_root: str,
    expected_sha256: str,
    baseline_snapshot: BaselineSnapshot,
    expected_report_id: str,
    expected_simulation_id: str,
    expected_run_id: str,
    expected_config_sha256: str,
    expected_input_sha256: str,
    expected_training_cutoff: str,
) -> PreregisteredForecast:
    materialized = load_materialized_json(
        relative_path=relative_path,
        trusted_root=trusted_root,
        expected_sha256=expected_sha256,
        reason_prefix="preregistered_forecast",
    )
    payload = materialized.payload
    required = {
        "schema", "version", "generated_at", "training_cutoff", "report_id",
        "simulation_id", "run_id", "config_sha256", "input_sha256",
        "baseline_snapshot_sha256", "variable_id", "variable_label", "unit",
        "categories", "heldout_predictions",
    }
    if set(payload) != required:
        raise SnapshotValidationError("preregistered_forecast_schema_keys_mismatch")
    if payload["schema"] != FORECAST_SCHEMA or payload["version"] != 1:
        raise SnapshotValidationError("preregistered_forecast_schema_invalid")
    generated_at = _aware_datetime(
        payload["generated_at"], "preregistered_forecast_generated_at_invalid"
    )
    cutoff = _aware_datetime(
        payload["training_cutoff"], "preregistered_forecast_cutoff_invalid"
    )
    if payload["training_cutoff"] != expected_training_cutoff or not generated_at < cutoff:
        raise SnapshotValidationError("preregistered_forecast_not_before_cutoff")
    if (
        payload["report_id"] != expected_report_id
        or payload["simulation_id"] != expected_simulation_id
        or payload["run_id"] != expected_run_id
        or payload["config_sha256"] != expected_config_sha256
        or payload["input_sha256"] != expected_input_sha256
        or payload["baseline_snapshot_sha256"] != baseline_snapshot.sha256
    ):
        raise SnapshotValidationError("preregistered_forecast_binding_mismatch")
    variable = _baseline_variable(baseline_snapshot)
    if (
        payload["variable_id"] != variable["id"]
        or payload["variable_label"] != variable["label"]
        or payload["unit"] != variable["unit"]
        or payload["categories"] != variable["categories"]
    ):
        raise SnapshotValidationError("preregistered_forecast_labels_mismatch")
    items = payload["heldout_predictions"]
    if not isinstance(items, list) or not MIN_FORECAST_N <= len(items) <= MAX_FORECAST_N:
        raise SnapshotValidationError("preregistered_forecast_size_invalid")
    predicted: dict[str, tuple[float, ...]] = {}
    ordered_ids: list[str] = []
    totals = [0.0] * len(variable["categories"])
    for item in items:
        if not isinstance(item, Mapping) or set(item) != {"id", "distribution"}:
            raise SnapshotValidationError("preregistered_forecast_item_invalid")
        sample_id = item["id"]
        if not isinstance(sample_id, str) or not sample_id or sample_id in predicted:
            raise SnapshotValidationError("preregistered_forecast_ids_invalid")
        distribution = validate_probability_distribution(
            item["distribution"],
            expected_length=len(totals),
            reason="preregistered_forecast_distribution_invalid",
        )
        ordered_ids.append(sample_id)
        predicted[sample_id] = tuple(distribution)
        for index, value in enumerate(distribution):
            totals[index] += value
    aggregate = tuple(value / len(items) for value in totals)
    revalidate_materialized_json(materialized, reason_prefix="preregistered_forecast")
    return PreregisteredForecast(
        sha256=materialized.sha256,
        generated_at=generated_at,
        heldout_ids=tuple(ordered_ids),
        predicted_by_id=predicted,
        predicted_distribution=aggregate,
    )


def _baseline_variable(snapshot: BaselineSnapshot) -> Mapping[str, Any]:
    for variable in snapshot.payload["variables"]:
        if variable["id"] == snapshot.variable_id:
            return variable
    raise SnapshotValidationError("preregistered_forecast_variable_missing")


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


__all__ = ["FORECAST_SCHEMA", "PreregisteredForecast", "load_preregistered_forecast"]
