"""Host-authenticated Vox gates and per-report current-generation anchors."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import stat
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ...config import Config
from .baseline_snapshot import SnapshotValidationError, canonical_json_bytes


GATE_HMAC_ALGORITHM = "hmac-sha256"
ANCHOR_SCHEMA = "mirofish.vox.current_generation_anchor.v1"
PREREGISTRATION_SCHEMA = "mirofish.vox.preregistration_receipt.v1"
PREREGISTERED_SCORING_ALGORITHM = "multiclass_brier_log_loss_per_id.v1"
C4_MATERIAL_POLICY_ID = "vox-c4-material-v1"
DEFAULT_MINIMUM_BRIER_SKILL_SCORE = 0.05
DEFAULT_MAXIMUM_LOG_LOSS_RATIO = 0.99
MIN_ALLOWED_BRIER_SKILL_SCORE = DEFAULT_MINIMUM_BRIER_SKILL_SCORE
MAX_ALLOWED_LOG_LOSS_RATIO = DEFAULT_MAXIMUM_LOG_LOSS_RATIO
MIN_SIGNING_KEY_BYTES = 32
MAX_ANCHOR_BYTES = 32_768
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REPARSE_POINT = 0x400


@dataclass(frozen=True)
class IssuedPreregistrationReceipt:
    relative_path: str
    sha256: str
    payload: Mapping[str, Any]


def signing_key() -> bytes | None:
    raw = getattr(Config, "VOX_CLAIM_SIGNING_KEY", "")
    if not isinstance(raw, str):
        return None
    value = raw.encode("utf-8")
    return value if len(value) >= MIN_SIGNING_KEY_BYTES else None


def sign_gate(gate: dict[str, Any]) -> bool:
    """Sign the complete gate in place, excluding only the signature value."""

    gate["signature_algorithm"] = GATE_HMAC_ALGORITHM
    gate["hmac_sha256"] = None
    key = signing_key()
    if key is None:
        return False
    gate["hmac_sha256"] = _hmac_payload(gate, key, excluded={"hmac_sha256"})
    return True


def verify_gate_hmac(gate: Mapping[str, Any]) -> bool:
    key = signing_key()
    signature = gate.get("hmac_sha256")
    if (
        key is None
        or gate.get("signature_algorithm") != GATE_HMAC_ALGORITHM
        or not isinstance(signature, str)
        or not _SHA256_RE.fullmatch(signature)
    ):
        return False
    expected = _hmac_payload(gate, key, excluded={"hmac_sha256"})
    return hmac.compare_digest(signature, expected)


def verify_preregistration_receipt(receipt: Mapping[str, Any]) -> bool:
    key = signing_key()
    signature = receipt.get("hmac_sha256")
    if (
        key is None
        or receipt.get("schema") != PREREGISTRATION_SCHEMA
        or receipt.get("signature_algorithm") != GATE_HMAC_ALGORITHM
        or not isinstance(signature, str)
        or not _SHA256_RE.fullmatch(signature)
    ):
        return False
    expected = _hmac_payload(receipt, key, excluded={"hmac_sha256"})
    return hmac.compare_digest(signature, expected)


def issue_preregistration_receipt(
    *,
    preregistration_id: str,
    report_id: str,
    simulation_id: str,
    run_id: str,
    config_sha256: str,
    input_sha256: str,
    baseline_snapshot_path: str,
    baseline_snapshot_sha256: str,
    forecast_path: str,
    forecast_sha256: str,
    training_cutoff: str,
    target_variable: str | None = None,
    minimum_brier_skill_score: float = DEFAULT_MINIMUM_BRIER_SKILL_SCORE,
    maximum_log_loss_ratio: float = DEFAULT_MAXIMUM_LOG_LOSS_RATIO,
    policy_id: str = C4_MATERIAL_POLICY_ID,
) -> IssuedPreregistrationReceipt:
    """Commit a forecast plan using only the host clock and fixed trust roots."""

    key = signing_key()
    if key is None:
        raise SnapshotValidationError("vox_signing_key_unavailable")
    if not isinstance(preregistration_id, str) or not preregistration_id:
        raise SnapshotValidationError("vox_preregistration_id_invalid")
    if (
        policy_id != C4_MATERIAL_POLICY_ID
        or isinstance(minimum_brier_skill_score, bool)
        or not isinstance(minimum_brier_skill_score, (int, float))
        or not math.isfinite(float(minimum_brier_skill_score))
        or not MIN_ALLOWED_BRIER_SKILL_SCORE <= float(minimum_brier_skill_score) <= 1.0
        or isinstance(maximum_log_loss_ratio, bool)
        or not isinstance(maximum_log_loss_ratio, (int, float))
        or not math.isfinite(float(maximum_log_loss_ratio))
        or not 0.0 < float(maximum_log_loss_ratio) <= MAX_ALLOWED_LOG_LOSS_RATIO
    ):
        raise SnapshotValidationError("vox_preregistration_performance_criteria_invalid")
    from .baseline_snapshot import load_baseline_snapshot
    from .preregistered_forecast import load_preregistered_forecast

    trusted_root = str(getattr(Config, "VOX_CLAIM_EVIDENCE_ROOT", "") or "").strip()
    baseline = load_baseline_snapshot(
        relative_path=baseline_snapshot_path,
        trusted_root=trusted_root,
        expected_sha256=baseline_snapshot_sha256,
        target_variable=target_variable,
    )
    forecast = load_preregistered_forecast(
        relative_path=forecast_path,
        trusted_root=trusted_root,
        expected_sha256=forecast_sha256,
        baseline_snapshot=baseline,
        expected_report_id=report_id,
        expected_simulation_id=simulation_id,
        expected_run_id=run_id,
        expected_config_sha256=config_sha256,
        expected_input_sha256=input_sha256,
        expected_training_cutoff=training_cutoff,
    )
    issued_at = _utc_now()
    cutoff = _aware_datetime(training_cutoff, "vox_preregistration_cutoff_invalid")
    if forecast.generated_at > issued_at or not issued_at < cutoff:
        raise SnapshotValidationError("vox_preregistration_not_issued_before_cutoff")
    payload: dict[str, Any] = {
        "schema": PREREGISTRATION_SCHEMA,
        "version": 1,
        "issued_at": _datetime_iso(issued_at),
        "preregistration_id": preregistration_id,
        "report_id": report_id,
        "simulation_id": simulation_id,
        "run_id": run_id,
        "config_sha256": config_sha256,
        "input_sha256": input_sha256,
        "baseline_snapshot_sha256": baseline_snapshot_sha256,
        "training_cutoff": training_cutoff,
        "heldout_plan_ids": list(forecast.heldout_ids),
        "forecast_path": forecast_path,
        "forecast_sha256": forecast_sha256,
        "performance_criteria": {
            "policy_id": policy_id,
            "algorithm": PREREGISTERED_SCORING_ALGORITHM,
            "minimum_brier_skill_score": float(minimum_brier_skill_score),
            "maximum_log_loss_ratio": float(maximum_log_loss_ratio),
        },
        "signature_algorithm": GATE_HMAC_ALGORITHM,
        "hmac_sha256": None,
    }
    payload["hmac_sha256"] = _hmac_payload(payload, key, excluded={"hmac_sha256"})
    raw = canonical_json_bytes(payload)
    relative_path = _preregistration_name(report_id, preregistration_id)
    _atomic_write_once(_trusted_state_root(), relative_path, raw)
    return IssuedPreregistrationReceipt(
        relative_path=relative_path,
        sha256=hashlib.sha256(raw).hexdigest(),
        payload=payload,
    )


def load_preregistration_receipt(
    *,
    relative_path: str,
    expected_sha256: str,
    expected_report_id: str,
    expected_preregistration_id: str,
) -> Mapping[str, Any]:
    if relative_path != _preregistration_name(
        expected_report_id, expected_preregistration_id
    ):
        raise SnapshotValidationError("vox_preregistration_receipt_path_invalid")
    try:
        payload = _safe_read(_trusted_state_root(), relative_path)
    except OSError as exc:
        raise SnapshotValidationError("vox_preregistration_receipt_missing") from exc
    raw = canonical_json_bytes(dict(payload))
    if (
        not _SHA256_RE.fullmatch(expected_sha256)
        or hashlib.sha256(raw).hexdigest() != expected_sha256
        or not verify_preregistration_receipt(payload)
    ):
        raise SnapshotValidationError("vox_preregistration_receipt_invalid")
    return payload


def gate_sha256(gate: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(gate))).hexdigest()


def write_current_generation_anchor(report_id: str, gate: Mapping[str, Any]) -> None:
    """Atomically make a signed gate current only after its artifact commit."""

    key = signing_key()
    if key is None or not verify_gate_hmac(gate):
        raise SnapshotValidationError("vox_signing_key_unavailable_or_gate_unsigned")
    if gate.get("report_id") != report_id:
        raise SnapshotValidationError("vox_anchor_report_binding_mismatch")
    generation_id = gate.get("generation_id")
    if not isinstance(generation_id, str) or not generation_id:
        raise SnapshotValidationError("vox_anchor_generation_missing")
    root = _trusted_state_root()
    payload: dict[str, Any] = {
        "schema": ANCHOR_SCHEMA,
        "version": 1,
        "report_id": report_id,
        "generation_id": generation_id,
        "gate_sha256": gate_sha256(gate),
        "signature_algorithm": GATE_HMAC_ALGORITHM,
        "hmac_sha256": None,
    }
    payload["hmac_sha256"] = _hmac_payload(payload, key, excluded={"hmac_sha256"})
    _atomic_write(root, _anchor_name(report_id), canonical_json_bytes(payload))


def verify_current_generation_anchor(report_id: str, gate: Mapping[str, Any]) -> bool:
    key = signing_key()
    if key is None:
        return False
    try:
        root = _trusted_state_root()
        payload = _safe_read(root, _anchor_name(report_id))
    except (OSError, SnapshotValidationError, ValueError, TypeError):
        return False
    if set(payload) != {
        "schema", "version", "report_id", "generation_id", "gate_sha256",
        "signature_algorithm", "hmac_sha256",
    }:
        return False
    signature = payload.get("hmac_sha256")
    if (
        payload.get("schema") != ANCHOR_SCHEMA
        or payload.get("version") != 1
        or payload.get("report_id") != report_id
        or payload.get("generation_id") != gate.get("generation_id")
        or payload.get("gate_sha256") != gate_sha256(gate)
        or payload.get("signature_algorithm") != GATE_HMAC_ALGORITHM
        or not isinstance(signature, str)
        or not _SHA256_RE.fullmatch(signature)
    ):
        return False
    expected = _hmac_payload(payload, key, excluded={"hmac_sha256"})
    return hmac.compare_digest(signature, expected)


def _hmac_payload(payload: Mapping[str, Any], key: bytes, *, excluded: set[str]) -> str:
    unsigned = {name: value for name, value in payload.items() if name not in excluded}
    return hmac.new(key, canonical_json_bytes(unsigned), hashlib.sha256).hexdigest()


def _anchor_name(report_id: str) -> str:
    return f"{hashlib.sha256(report_id.encode('utf-8')).hexdigest()}.json"


def _preregistration_name(report_id: str, preregistration_id: str) -> str:
    report_hash = hashlib.sha256(report_id.encode("utf-8")).hexdigest()
    prereg_hash = hashlib.sha256(preregistration_id.encode("utf-8")).hexdigest()
    return f"prereg-{report_hash}-{prereg_hash}.json"


def _trusted_state_root() -> Path:
    raw = str(getattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", "") or "").strip()
    root = Path(raw)
    if not raw or not root.is_absolute():
        raise SnapshotValidationError("vox_verification_state_root_not_configured")
    _reject_link_or_reparse_components(root)
    try:
        resolved = root.resolve(strict=True)
        info = os.lstat(root)
    except OSError as exc:
        raise SnapshotValidationError("vox_verification_state_root_unavailable") from exc
    if not stat.S_ISDIR(info.st_mode) or _stat_is_reparse(info):
        raise SnapshotValidationError("vox_verification_state_root_invalid")
    return resolved


def _reject_link_or_reparse_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if not current.exists():
            continue
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode) or _stat_is_reparse(info):
            raise SnapshotValidationError("vox_verification_state_link_rejected")


def _atomic_write(root: Path, name: str, raw: bytes) -> None:
    target = root / name
    if target.exists():
        info = os.lstat(target)
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or _stat_is_reparse(info):
            raise SnapshotValidationError("vox_anchor_target_invalid")
    temporary = root / f".{name}.tmp-{os.getpid()}-{time.time_ns()}"
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(temporary, flags, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temporary, target)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _atomic_write_once(root: Path, name: str, raw: bytes) -> None:
    """Publish immutable bytes atomically; an existing prereg ID is final."""

    target = root / name
    temporary = root / f".{name}.tmp-{os.getpid()}-{time.time_ns()}"
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(temporary, flags, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise SnapshotValidationError("vox_preregistration_id_already_issued") from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


def _datetime_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _safe_read(root: Path, name: str) -> Mapping[str, Any]:
    path = root / name
    info = os.lstat(path)
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or _stat_is_reparse(info)
        or info.st_nlink != 1
        or not 0 < info.st_size <= MAX_ANCHOR_BYTES
    ):
        raise SnapshotValidationError("vox_anchor_file_invalid")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
            info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
        ):
            raise SnapshotValidationError("vox_anchor_changed_during_read")
        raw = os.read(fd, MAX_ANCHOR_BYTES + 1)
        if os.read(fd, 1) or len(raw) > MAX_ANCHOR_BYTES:
            raise SnapshotValidationError("vox_anchor_size_invalid")
    finally:
        os.close(fd)
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise SnapshotValidationError("vox_anchor_not_canonical")
    return payload


def _stat_is_reparse(value: os.stat_result) -> bool:
    return bool(getattr(value, "st_file_attributes", 0) & _REPARSE_POINT)


__all__ = [
    "C4_MATERIAL_POLICY_ID",
    "DEFAULT_MAXIMUM_LOG_LOSS_RATIO",
    "DEFAULT_MINIMUM_BRIER_SKILL_SCORE",
    "gate_sha256",
    "issue_preregistration_receipt",
    "IssuedPreregistrationReceipt",
    "load_preregistration_receipt",
    "MIN_ALLOWED_BRIER_SKILL_SCORE",
    "MAX_ALLOWED_LOG_LOSS_RATIO",
    "PREREGISTERED_SCORING_ALGORITHM",
    "sign_gate",
    "signing_key",
    "verify_current_generation_anchor",
    "verify_gate_hmac",
    "verify_preregistration_receipt",
    "write_current_generation_anchor",
]
