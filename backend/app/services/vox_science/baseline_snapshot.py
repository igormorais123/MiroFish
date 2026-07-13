"""Fail-closed loader for materialized Vox calibration baselines."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


SNAPSHOT_SCHEMA = "mirofish.vox.baseline_snapshot.v1"
MAX_SNAPSHOT_BYTES = 1_000_000
MAX_VARIABLES = 128
MAX_SUBGROUPS = 256
MAX_ROWS = 10_000
MAX_VALUES = 100_000
PROBABILITY_SUM_TOLERANCE = 1e-6
MAX_VECTOR_LENGTH = 10_000
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 100_000
MAX_JSON_STRING_LENGTH = 100_000
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REPARSE_POINT = 0x400


class SnapshotValidationError(ValueError):
    """A baseline snapshot cannot be trusted for a measured claim."""


@dataclass(frozen=True)
class BaselineSnapshot:
    payload: Mapping[str, Any]
    sha256: str
    canonical_bytes: bytes
    observed: tuple[float, ...]
    subgroup_observed: Mapping[str, tuple[float, ...]]
    subgroup_sample_sizes: Mapping[str, int]
    variable_id: str

    def public_summary(self) -> dict[str, Any]:
        return {
            "status": "measured",
            "schema": SNAPSHOT_SCHEMA,
            "version": self.payload["version"],
            "sha256": self.sha256,
            "canonical_bytes": len(self.canonical_bytes),
            "source_id": self.payload["source"]["id"],
            "variable_id": self.variable_id,
            "observations": len(self.observed),
            "subgroups": sorted(self.subgroup_observed),
            "subgroup_sample_sizes": dict(self.subgroup_sample_sizes),
        }


@dataclass(frozen=True)
class MaterializedJson:
    payload: Mapping[str, Any]
    sha256: str
    canonical_bytes: bytes
    resolved_path: Path
    identity: os.stat_result


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize the contract representation; NaN/Infinity are forbidden."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def load_baseline_snapshot(
    *,
    relative_path: str | os.PathLike[str],
    trusted_root: str | os.PathLike[str],
    expected_sha256: str,
    target_variable: str | None,
) -> BaselineSnapshot:
    """Load once from a trusted root and validate bytes, schema and dimensions."""

    materialized = load_materialized_json(
        relative_path=relative_path,
        trusted_root=trusted_root,
        expected_sha256=expected_sha256,
        reason_prefix="snapshot",
        max_bytes=MAX_SNAPSHOT_BYTES,
    )
    payload = materialized.payload
    observed, subgroups, subgroup_sizes, variable_id = _validate_payload(payload, target_variable)
    revalidate_materialized_json(materialized, reason_prefix="snapshot")
    return BaselineSnapshot(
        payload=payload,
        sha256=materialized.sha256,
        canonical_bytes=materialized.canonical_bytes,
        observed=tuple(observed),
        subgroup_observed={key: tuple(values) for key, values in subgroups.items()},
        subgroup_sample_sizes=subgroup_sizes,
        variable_id=variable_id,
    )


def load_materialized_json(
    *,
    relative_path: str | os.PathLike[str],
    trusted_root: str | os.PathLike[str],
    expected_sha256: str,
    reason_prefix: str,
    max_bytes: int = MAX_SNAPSHOT_BYTES,
) -> MaterializedJson:
    """Shared secure loader for every local claim-authority artifact."""

    def reason(suffix: str) -> SnapshotValidationError:
        return SnapshotValidationError(f"{reason_prefix}_{suffix}")

    if not isinstance(expected_sha256, str) or not _SHA256_RE.fullmatch(expected_sha256):
        raise reason("expected_sha256_invalid")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise reason("path_must_be_relative")

    root = Path(trusted_root)
    if not root.is_absolute():
        raise reason("trusted_root_must_be_absolute")
    _reject_root_components(root)
    try:
        root_resolved = root.resolve(strict=True)
    except OSError as exc:
        raise reason("trusted_root_unavailable") from exc
    if not root_resolved.is_dir() or _is_reparse(root_resolved):
        raise reason("trusted_root_invalid")

    candidate = root_resolved.joinpath(relative)
    _reject_link_components(root_resolved, candidate)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root_resolved)
    except (OSError, ValueError) as exc:
        raise reason("path_escape_or_missing") from exc

    before = os.lstat(resolved)
    if not stat.S_ISREG(before.st_mode) or _stat_is_reparse(before) or before.st_nlink != 1:
        raise reason("not_unique_regular_file")
    if before.st_size <= 0 or before.st_size > max_bytes:
        raise reason("size_budget_exceeded")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(resolved, flags)
    try:
        opened = os.fstat(fd)
        _assert_same_file(before, opened)
        raw = os.read(fd, max_bytes + 1)
        if os.read(fd, 1) or len(raw) > max_bytes:
            raise reason("size_budget_exceeded")
        after = os.fstat(fd)
        _assert_same_file(opened, after)
    finally:
        os.close(fd)

    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise reason("sha256_mismatch")
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, SnapshotValidationError, RecursionError) as exc:
        if isinstance(exc, SnapshotValidationError):
            raise
        raise reason("json_invalid") from exc
    if not isinstance(payload, dict):
        raise reason("root_must_be_object")
    try:
        _validate_json_budgets(payload)
        canonical = canonical_json_bytes(payload)
    except (TypeError, ValueError, RecursionError) as exc:
        raise reason("non_finite_or_non_json_value") from exc
    if raw != canonical:
        raise reason("bytes_not_canonical")
    return MaterializedJson(
        payload=payload,
        sha256=actual_sha256,
        canonical_bytes=canonical,
        resolved_path=resolved,
        identity=before,
    )


def revalidate_materialized_json(value: MaterializedJson, *, reason_prefix: str) -> None:
    try:
        final = os.lstat(value.resolved_path)
        _assert_same_file(value.identity, final)
    except (OSError, SnapshotValidationError) as exc:
        raise SnapshotValidationError(f"{reason_prefix}_changed_during_validation") from exc


def _validate_payload(
    payload: Mapping[str, Any], target_variable: str | None
) -> tuple[list[float], dict[str, list[float]], dict[str, int], str]:
    _exact_keys(
        payload,
        required={
            "schema", "version", "generated_at", "domain", "population", "period",
            "source", "provenance", "variables", "subgroups", "data",
        },
    )
    if payload["schema"] != SNAPSHOT_SCHEMA or payload["version"] != 1:
        raise SnapshotValidationError("snapshot_schema_or_version_unsupported")
    for key in ("generated_at", "domain", "population", "period"):
        _nonempty_string(payload[key], f"snapshot_{key}_invalid")
    _parse_datetime(payload["generated_at"], "snapshot_generated_at_invalid")

    source = _mapping(payload["source"], "snapshot_source_invalid")
    _exact_keys(source, required={"id", "name", "kind", "uri", "captured_at"})
    for key in ("id", "name", "kind", "uri", "captured_at"):
        _nonempty_string(source[key], f"snapshot_source_{key}_invalid")
    _parse_datetime(source["captured_at"], "snapshot_source_captured_at_invalid")

    provenance = _mapping(payload["provenance"], "snapshot_provenance_invalid")
    _exact_keys(provenance, required={"collector", "method", "license"})
    for key in ("collector", "method", "license"):
        _nonempty_string(provenance[key], f"snapshot_provenance_{key}_invalid")

    variables = payload["variables"]
    if not isinstance(variables, list) or not 1 <= len(variables) <= MAX_VARIABLES:
        raise SnapshotValidationError("snapshot_variables_budget_or_type_invalid")
    variable_ids: list[str] = []
    categories_by_variable: dict[str, list[str]] = {}
    for variable in variables:
        item = _mapping(variable, "snapshot_variable_invalid")
        _exact_keys(item, required={"id", "label", "unit", "categories"})
        for key in ("id", "label", "unit"):
            _nonempty_string(item[key], f"snapshot_variable_{key}_invalid")
        categories = item["categories"]
        if not isinstance(categories, list) or not categories:
            raise SnapshotValidationError("snapshot_variable_categories_invalid")
        if any(not isinstance(value, str) or not value for value in categories):
            raise SnapshotValidationError("snapshot_variable_categories_invalid")
        if len(set(categories)) != len(categories):
            raise SnapshotValidationError("snapshot_variable_categories_duplicate")
        variable_ids.append(item["id"])
        categories_by_variable[item["id"]] = categories
    if len(set(variable_ids)) != len(variable_ids):
        raise SnapshotValidationError("snapshot_variable_ids_duplicate")

    subgroups = payload["subgroups"]
    if not isinstance(subgroups, list) or len(subgroups) > MAX_SUBGROUPS:
        raise SnapshotValidationError("snapshot_subgroups_budget_or_type_invalid")
    if any(not isinstance(group, str) or not group for group in subgroups):
        raise SnapshotValidationError("snapshot_subgroup_invalid")
    if len(set(subgroups)) != len(subgroups):
        raise SnapshotValidationError("snapshot_subgroups_duplicate")

    selected = target_variable or (variable_ids[0] if len(variable_ids) == 1 else None)
    if not selected or selected not in categories_by_variable:
        raise SnapshotValidationError("snapshot_target_variable_missing_or_unknown")
    data = _mapping(payload["data"], "snapshot_data_invalid")
    kind = data.get("kind")
    if kind == "distributions":
        _exact_keys(
            data,
            required={"kind", "distributions", "subgroup_distributions", "subgroup_sample_sizes"},
        )
        distributions = _mapping(data["distributions"], "snapshot_distributions_invalid")
        _require_exact_dynamic_keys(distributions, set(variable_ids), "snapshot_distribution_variables_mismatch")
        observed = _validate_vector(
            distributions[selected], categories_by_variable[selected], "snapshot_distribution_invalid"
        )
        subgroup_payload = _mapping(
            data["subgroup_distributions"], "snapshot_subgroup_distributions_invalid"
        )
        _require_exact_dynamic_keys(
            subgroup_payload, set(subgroups), "snapshot_subgroup_set_mismatch"
        )
        subgroup_values: dict[str, list[float]] = {}
        for group, group_distributions_raw in subgroup_payload.items():
            group_distributions = _mapping(
                group_distributions_raw, "snapshot_subgroup_distribution_invalid"
            )
            _require_exact_dynamic_keys(
                group_distributions, set(variable_ids), "snapshot_subgroup_variables_mismatch"
            )
            subgroup_values[group] = _validate_vector(
                group_distributions[selected],
                categories_by_variable[selected],
                "snapshot_subgroup_distribution_invalid",
            )
        size_payload = _mapping(data["subgroup_sample_sizes"], "snapshot_subgroup_sizes_invalid")
        _require_exact_dynamic_keys(size_payload, set(subgroups), "snapshot_subgroup_sizes_mismatch")
        subgroup_sizes: dict[str, int] = {}
        for group, size in size_payload.items():
            if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
                raise SnapshotValidationError("snapshot_subgroup_size_invalid")
            subgroup_sizes[group] = size
        return observed, subgroup_values, subgroup_sizes, selected
    if kind == "rows":
        _exact_keys(data, required={"kind", "rows"})
        rows = data["rows"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
            raise SnapshotValidationError("snapshot_rows_budget_or_type_invalid")
        row_observed: list[float] = []
        subgroup_values = {group: [] for group in subgroups}
        seen_ids: set[str] = set()
        for row_raw in rows:
            row = _mapping(row_raw, "snapshot_row_invalid")
            _exact_keys(row, required={"id", "subgroup", "observed_at", "values"})
            _nonempty_string(row["id"], "snapshot_row_id_invalid")
            if row["id"] in seen_ids:
                raise SnapshotValidationError("snapshot_row_id_duplicate")
            seen_ids.add(row["id"])
            if row["subgroup"] is not None and row["subgroup"] not in subgroups:
                raise SnapshotValidationError("snapshot_row_subgroup_unknown")
            _nonempty_string(row["observed_at"], "snapshot_row_observed_at_invalid")
            _parse_datetime(row["observed_at"], "snapshot_row_observed_at_invalid")
            values = _mapping(row["values"], "snapshot_row_values_invalid")
            _require_exact_dynamic_keys(values, set(variable_ids), "snapshot_row_variables_mismatch")
            value = _finite_number(values[selected], "snapshot_row_value_invalid")
            row_observed.append(value)
            if row["subgroup"] is not None:
                subgroup_values[row["subgroup"]].append(value)
        subgroup_sizes = {group: len(values) for group, values in subgroup_values.items()}
        return row_observed, subgroup_values, subgroup_sizes, selected
    raise SnapshotValidationError("snapshot_data_kind_invalid")


def _validate_vector(raw: Any, categories: Sequence[str], reason: str) -> list[float]:
    if not isinstance(raw, list) or not raw or len(raw) > MAX_VECTOR_LENGTH:
        raise SnapshotValidationError(reason)
    if len(raw) != len(categories):
        raise SnapshotValidationError("snapshot_distribution_categories_mismatch")
    values = [_finite_number(value, reason) for value in raw]
    if any(value < 0 for value in values) or sum(values) <= 0:
        raise SnapshotValidationError("snapshot_distribution_mass_invalid")
    if abs(sum(values) - 1.0) > PROBABILITY_SUM_TOLERANCE:
        raise SnapshotValidationError("snapshot_distribution_not_probability")
    if len(values) > MAX_VALUES:
        raise SnapshotValidationError("snapshot_values_budget_exceeded")
    return values


def validate_numeric_vector(
    value: Any, *, expected_length: int | None = None, reason: str = "numeric_vector_invalid"
) -> list[float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise SnapshotValidationError(reason)
    if len(value) > MAX_VECTOR_LENGTH or (expected_length is not None and len(value) != expected_length):
        raise SnapshotValidationError(reason)
    values = [_finite_number(item, reason) for item in value]
    if any(item < 0 for item in values) or sum(values) <= 0:
        raise SnapshotValidationError(reason)
    return values


def validate_probability_distribution(
    value: Any,
    *,
    expected_length: int | None = None,
    reason: str = "probability_distribution_invalid",
) -> list[float]:
    values = validate_numeric_vector(
        value, expected_length=expected_length, reason=reason
    )
    if abs(sum(values) - 1.0) > PROBABILITY_SUM_TOLERANCE:
        raise SnapshotValidationError(reason)
    return values


def _finite_number(value: Any, reason: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SnapshotValidationError(reason)
    numeric = float(value)
    if not math.isfinite(numeric):
        raise SnapshotValidationError(reason)
    return numeric


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotValidationError("snapshot_duplicate_json_key")
        result[key] = value
    return result


def _exact_keys(value: Mapping[str, Any], *, required: set[str]) -> None:
    if set(value) != required:
        raise SnapshotValidationError("snapshot_schema_keys_mismatch")


def _require_exact_dynamic_keys(value: Mapping[str, Any], expected: set[str], reason: str) -> None:
    if set(value) != expected:
        raise SnapshotValidationError(reason)


def _mapping(value: Any, reason: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SnapshotValidationError(reason)
    return value


def _nonempty_string(value: Any, reason: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotValidationError(reason)


def _parse_datetime(value: Any, reason: str) -> None:
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SnapshotValidationError(reason) from exc


def _reject_link_components(root: Path, candidate: Path) -> None:
    current = root
    for part in candidate.relative_to(root).parts:
        current = current / part
        if current.exists() and (current.is_symlink() or _is_reparse(current)):
            raise SnapshotValidationError("snapshot_symlink_or_reparse_rejected")


def _reject_root_components(root: Path) -> None:
    current = Path(root.anchor)
    for part in root.parts[1:]:
        current /= part
        if not current.exists():
            continue
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode) or _stat_is_reparse(info):
            raise SnapshotValidationError("snapshot_trusted_root_symlink_or_reparse_rejected")


def _validate_json_budgets(payload: Any) -> None:
    nodes = 0
    stack: list[tuple[Any, int]] = [(payload, 1)]
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise SnapshotValidationError("snapshot_json_structure_budget_exceeded")
        if isinstance(value, str):
            if len(value) > MAX_JSON_STRING_LENGTH:
                raise SnapshotValidationError("snapshot_json_string_budget_exceeded")
        elif isinstance(value, Mapping):
            for key, nested in value.items():
                if len(key) > MAX_JSON_STRING_LENGTH:
                    raise SnapshotValidationError("snapshot_json_string_budget_exceeded")
                stack.append((nested, depth + 1))
        elif isinstance(value, list):
            stack.extend((nested, depth + 1) for nested in value)


def _is_reparse(path: Path) -> bool:
    try:
        return _stat_is_reparse(os.lstat(path))
    except OSError:
        return False


def _stat_is_reparse(value: os.stat_result) -> bool:
    return bool(getattr(value, "st_file_attributes", 0) & _REPARSE_POINT)


def _assert_same_file(before: os.stat_result, after: os.stat_result) -> None:
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        raise SnapshotValidationError("snapshot_changed_during_validation")


__all__ = [
    "BaselineSnapshot",
    "MaterializedJson",
    "SNAPSHOT_SCHEMA",
    "SnapshotValidationError",
    "canonical_json_bytes",
    "load_baseline_snapshot",
    "load_materialized_json",
    "revalidate_materialized_json",
    "validate_numeric_vector",
    "validate_probability_distribution",
]
