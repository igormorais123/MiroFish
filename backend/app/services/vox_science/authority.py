"""Configured authority manifest for Vox claim evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from ...config import Config
from .baseline_snapshot import (
    SnapshotValidationError,
    load_materialized_json,
    revalidate_materialized_json,
)


AUTHORITY_SCHEMA = "mirofish.vox.claim_evidence_authority.v1"
AUTHORITY_MANIFEST_NAME = "authority-manifest.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AuthorizedEvidence:
    trusted_root: str
    baseline_path: str
    baseline_sha256: str
    claim_evidence_path: str
    claim_evidence_sha256: str
    authority_manifest_sha256: str
    stability_runs: Mapping[str, str]
    preregistered_forecasts: Mapping[str, str]


@dataclass(frozen=True)
class AuthorizedForecast:
    trusted_root: str
    baseline_path: str
    baseline_sha256: str
    forecast_path: str
    forecast_sha256: str
    authority_manifest_sha256: str


def resolve_authorized_evidence(
    *, baseline_path: str, claim_evidence_path: str
) -> AuthorizedEvidence:
    root = str(getattr(Config, "VOX_CLAIM_EVIDENCE_ROOT", "") or "").strip()
    manifest_sha = str(
        getattr(Config, "VOX_CLAIM_AUTHORITY_MANIFEST_SHA256", "") or ""
    ).strip().lower()
    if not root or not Path(root).is_absolute():
        raise SnapshotValidationError("claim_authority_root_not_configured")
    if not _SHA256_RE.fullmatch(manifest_sha):
        raise SnapshotValidationError("claim_authority_manifest_hash_not_configured")
    manifest = load_materialized_json(
        relative_path=AUTHORITY_MANIFEST_NAME,
        trusted_root=root,
        expected_sha256=manifest_sha,
        reason_prefix="claim_authority_manifest",
    )
    payload = manifest.payload
    _exact_keys(
        payload,
        {
            "schema", "version", "generated_at", "baselines", "claim_evidence",
            "stability_runs", "preregistered_forecasts",
        },
    )
    if payload["schema"] != AUTHORITY_SCHEMA or payload["version"] != 1:
        raise SnapshotValidationError("claim_authority_schema_invalid")
    if not isinstance(payload["generated_at"], str) or not payload["generated_at"]:
        raise SnapshotValidationError("claim_authority_generated_at_invalid")
    try:
        generated_at = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotValidationError("claim_authority_generated_at_invalid") from exc
    if generated_at.tzinfo is None:
        raise SnapshotValidationError("claim_authority_generated_at_invalid")
    baselines = _hash_registry(payload["baselines"], "claim_authority_baselines_invalid")
    evidence = _hash_registry(payload["claim_evidence"], "claim_authority_evidence_invalid")
    stability = _hash_registry(
        payload["stability_runs"],
        "claim_authority_stability_runs_invalid",
        allow_empty=True,
    )
    forecasts = _hash_registry(
        payload["preregistered_forecasts"],
        "claim_authority_preregistered_forecasts_invalid",
        allow_empty=True,
    )
    baseline_sha = baselines.get(baseline_path)
    evidence_sha = evidence.get(claim_evidence_path)
    if baseline_sha is None or evidence_sha is None:
        raise SnapshotValidationError("claim_artifact_not_authorized")
    revalidate_materialized_json(manifest, reason_prefix="claim_authority_manifest")
    return AuthorizedEvidence(
        trusted_root=root,
        baseline_path=baseline_path,
        baseline_sha256=baseline_sha,
        claim_evidence_path=claim_evidence_path,
        claim_evidence_sha256=evidence_sha,
        authority_manifest_sha256=manifest_sha,
        stability_runs=stability,
        preregistered_forecasts=forecasts,
    )


def resolve_authorized_forecast(
    *, baseline_path: str, forecast_path: str
) -> AuthorizedForecast:
    root, manifest_sha, payload, manifest = _load_manifest()
    baselines = _hash_registry(payload["baselines"], "claim_authority_baselines_invalid")
    forecasts = _hash_registry(
        payload["preregistered_forecasts"],
        "claim_authority_preregistered_forecasts_invalid",
        allow_empty=True,
    )
    baseline_sha = baselines.get(baseline_path)
    forecast_sha = forecasts.get(forecast_path)
    if baseline_sha is None or forecast_sha is None:
        raise SnapshotValidationError("claim_forecast_not_authorized")
    revalidate_materialized_json(manifest, reason_prefix="claim_authority_manifest")
    return AuthorizedForecast(
        trusted_root=root,
        baseline_path=baseline_path,
        baseline_sha256=baseline_sha,
        forecast_path=forecast_path,
        forecast_sha256=forecast_sha,
        authority_manifest_sha256=manifest_sha,
    )


def _load_manifest() -> tuple[str, str, Any, Any]:
    root = str(getattr(Config, "VOX_CLAIM_EVIDENCE_ROOT", "") or "").strip()
    manifest_sha = str(
        getattr(Config, "VOX_CLAIM_AUTHORITY_MANIFEST_SHA256", "") or ""
    ).strip().lower()
    if not root or not Path(root).is_absolute():
        raise SnapshotValidationError("claim_authority_root_not_configured")
    if not _SHA256_RE.fullmatch(manifest_sha):
        raise SnapshotValidationError("claim_authority_manifest_hash_not_configured")
    manifest = load_materialized_json(
        relative_path=AUTHORITY_MANIFEST_NAME,
        trusted_root=root,
        expected_sha256=manifest_sha,
        reason_prefix="claim_authority_manifest",
    )
    payload = manifest.payload
    _exact_keys(
        payload,
        {
            "schema", "version", "generated_at", "baselines", "claim_evidence",
            "stability_runs", "preregistered_forecasts",
        },
    )
    if payload["schema"] != AUTHORITY_SCHEMA or payload["version"] != 1:
        raise SnapshotValidationError("claim_authority_schema_invalid")
    return root, manifest_sha, payload, manifest


def _hash_registry(
    value: Any, reason: str, *, allow_empty: bool = False
) -> dict[str, str]:
    if (
        not isinstance(value, Mapping)
        or (not value and not allow_empty)
        or len(value) > 256
    ):
        raise SnapshotValidationError(reason)
    out: dict[str, str] = {}
    for path, digest in value.items():
        if (
            not isinstance(path, str)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or not isinstance(digest, str)
            or not _SHA256_RE.fullmatch(digest)
        ):
            raise SnapshotValidationError(reason)
        out[path] = digest
    return out


def _exact_keys(value: Mapping[str, Any], required: set[str]) -> None:
    if set(value) != required:
        raise SnapshotValidationError("claim_authority_schema_keys_mismatch")


__all__ = [
    "AUTHORITY_SCHEMA",
    "AuthorizedEvidence",
    "AuthorizedForecast",
    "resolve_authorized_evidence",
    "resolve_authorized_forecast",
]
