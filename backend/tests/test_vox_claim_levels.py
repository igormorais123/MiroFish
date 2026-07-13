from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from pathlib import Path
from datetime import datetime, timezone

import pytest

from app.services.vox_science import build_vox_science_artifacts
from app.services.vox_science.artifacts import _passes_preregistered_performance
from app.services.vox_science.baseline_snapshot import (
    SnapshotValidationError,
    canonical_json_bytes,
    load_baseline_snapshot,
    load_materialized_json,
)
from app.services.vox_science.claim_evidence import vector_sha256
from app.services.vox_science.verification import (
    issue_preregistration_receipt,
    sign_gate,
    write_current_generation_anchor,
)
from app.services.harness_evidence_bundle import (
    _valid_science_generation,
    verified_vox_claim_projection,
)
from app.services.report_agent import ReportManager
from app.config import Config


def _gate() -> dict:
    return {
        "passes_gate": True,
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


def _snapshot_payload() -> dict:
    return {
        "schema": "mirofish.vox.baseline_snapshot.v1",
        "version": 1,
        "generated_at": "2026-07-13T12:00:00Z",
        "domain": "test_domain",
        "population": "test population",
        "period": "2026-Q3",
        "source": {
            "id": "public-test-v1",
            "name": "Public Test Baseline",
            "kind": "public_microdata",
            "uri": "https://example.invalid/public-test-v1",
            "captured_at": "2026-07-13T11:00:00Z",
        },
        "provenance": {
            "collector": "offline-test-fixture",
            "method": "published aggregate extraction",
            "license": "CC0-1.0",
        },
        "variables": [
            {
                "id": "outcome_x",
                "label": "Outcome X",
                "unit": "share",
                "categories": ["yes", "no"],
            }
        ],
        "subgroups": ["group_a", "group_b"],
        "data": {
            "kind": "distributions",
            "distributions": {"outcome_x": [0.6, 0.4]},
            "subgroup_distributions": {
                "group_a": {"outcome_x": [0.65, 0.35]},
                "group_b": {"outcome_x": [0.55, 0.45]},
            },
            "subgroup_sample_sizes": {"group_a": 80, "group_b": 75},
        },
    }


def _materialize_snapshot(root: Path, payload: dict | None = None) -> tuple[str, str]:
    raw = canonical_json_bytes(payload or _snapshot_payload())
    path = root / "baseline.json"
    path.write_bytes(raw)
    return path.name, hashlib.sha256(raw).hexdigest()


def _build(**extra) -> dict:
    kwargs = {
        "report_id": "report_claim_test",
        "simulation_id": "sim_claim_test",
        "graph_id": "graph_claim_test",
        "simulation_requirement": "Avaliar proposta sem declarar o desfecho",
        "quality_gate": _gate(),
        "evidence_audit": {"passes_gate": True},
        "decision_packet": {},
        "forecast_ledger": {"previsoes": [{"status": "planned"}]},
        "model_name": "offline-test-model",
        "target_variable": "outcome_x",
    }
    kwargs.update(extra)
    return build_vox_science_artifacts(**kwargs)


def _with_snapshot(root: Path, **extra) -> dict:
    name, digest = _materialize_snapshot(root)
    return _build(
        baseline_snapshot_path=name,
        baseline_snapshot_root=str(root),
        baseline_snapshot_sha256=digest,
        sample_distribution=[0.55, 0.45],
        **extra,
    )


def _claim_payload(
    binding: dict,
    *,
    level: str = "C2",
    run_refs: list[dict] | None = None,
    receipt_ref: tuple[str, str] | None = None,
) -> dict:
    payload = {
        "schema": "mirofish.vox.claim_evidence_bundle.v1",
        "version": 1,
        "generated_at": "2026-07-16T12:00:00Z" if level == "C4" else "2026-07-14T12:00:00Z",
        "binding": binding,
        "evaluation": {
            "evaluation_id": "eval-1",
            "variable_id": "outcome_x",
            "variable_label": "Outcome X",
            "categories": ["yes", "no"],
            "evaluated_at": "2026-07-14T12:00:00Z",
            "sample_ids": [f"eval-{index}" for index in range(40)],
            "observed_distribution": [0.6, 0.4],
            "predicted_distribution": [0.55, 0.45],
            "sample_sha256": vector_sha256([0.55, 0.45]),
        },
        "stability": None,
        "prospective": None,
    }
    if level in {"C3", "C4"}:
        payload["stability"] = {
            "runs": run_refs,
            "subgroups": {
                "group_a": {
                    "predicted_n": 40,
                    "sample_ids": [f"group-a-{index}" for index in range(40)],
                    "observed_distribution": [0.65, 0.35],
                    "predicted_distribution": [0.62, 0.38],
                    "sample_sha256": vector_sha256([0.62, 0.38]),
                },
                "group_b": {
                    "predicted_n": 40,
                    "sample_ids": [f"group-b-{index}" for index in range(40)],
                    "observed_distribution": [0.55, 0.45],
                    "predicted_distribution": [0.53, 0.47],
                    "sample_sha256": vector_sha256([0.53, 0.47]),
                },
            },
        }
    if level == "C4":
        assert receipt_ref is not None
        payload["prospective"] = {
            "status": "measured",
            "mode": "prospective_out_of_sample",
            "preregistration_id": "prereg-2026-001",
            "preregistration_receipt_path": receipt_ref[0],
            "preregistration_receipt_sha256": receipt_ref[1],
            "training_cutoff": "2026-07-14T09:00:00Z",
            "evaluated_at": "2026-07-15T12:00:00Z",
            "report_id": binding["report_id"],
            "simulation_id": binding["simulation_id"],
            "run_id": binding["run_id"],
            "config_sha256": binding["config_sha256"],
            "input_sha256": binding["input_sha256"],
            "baseline_snapshot_sha256": binding["baseline_snapshot_sha256"],
            "training_ids": [f"train-{index}" for index in range(30)],
            "heldout_ids": [f"holdout-{index}" for index in range(30)],
            "heldout_times": ["2026-07-15T10:00:00Z" for _ in range(30)],
            "observed_outcomes": [
                {"id": f"holdout-{index}", "value": "yes" if index < 16 else "no"}
                for index in range(30)
            ],
        }
    return payload


def _with_authorized_evidence(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    level: str = "C2",
    mutate=None,
    tamper_after_authorization=None,
    forecast_mutate=None,
    issuer_time: datetime | None = None,
    reported_correlations: dict[str, float] | None = None,
    run_distribution_transform=None,
    minimum_brier_skill_score: float = 0.05,
    maximum_log_loss_ratio: float = 0.99,
    snapshot_payload: dict | None = None,
    policy_id: str = "vox-c4-material-v1",
) -> dict:
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "test-only-signing-key-0123456789abcdef")
    state_root = root / "verification-state"
    state_root.mkdir()
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(state_root.resolve()))
    monkeypatch.setattr(Config, "VOX_CLAIM_EVIDENCE_ROOT", str(root.resolve()))
    baseline_name, baseline_digest = _materialize_snapshot(root, snapshot_payload)
    bootstrap = _build()
    model = bootstrap["model_run_registry.json"]
    binding = {
        "report_id": "report_claim_test",
        "simulation_id": "sim_claim_test",
        "run_id": model["run_id"],
        "config_sha256": model["config_sha256"],
        "input_sha256": model["prompt_registry_hash"],
        "baseline_snapshot_sha256": baseline_digest,
    }
    run_registry: dict[str, str] = {}
    run_refs: list[dict] = []
    if level in {"C3", "C4"}:
        for index, distribution in enumerate(
            ([0.55, 0.45], [0.54, 0.46], [0.56, 0.44]), start=1
        ):
            if run_distribution_transform is not None:
                distribution = run_distribution_transform(index, list(distribution))
            run_payload = {
                "schema": "mirofish.vox.stability_run.v1",
                "version": 1,
                "generated_at": f"2026-07-14T10:0{index}:00Z",
                "report_id": binding["report_id"],
                "simulation_id": binding["simulation_id"],
                "run_id": f"stability-run-{index}",
                "seed": index,
                "input_sha256": binding["input_sha256"],
                "config_sha256": binding["config_sha256"],
                "baseline_snapshot_sha256": binding["baseline_snapshot_sha256"],
                "variable_id": "outcome_x",
                "variable_label": "Outcome X",
                "categories": ["yes", "no"],
                "sample_ids": [f"run-{index}-sample-{item}" for item in range(40)],
                "distribution": list(distribution),
                "sample_sha256": vector_sha256(distribution),
            }
            raw = canonical_json_bytes(run_payload)
            name = f"stability-run-{index}.json"
            digest = hashlib.sha256(raw).hexdigest()
            (root / name).write_bytes(raw)
            run_registry[name] = digest
            run_refs.append(
                {"run_id": f"stability-run-{index}", "seed": index, "artifact_path": name, "artifact_sha256": digest}
            )
    forecast_registry: dict[str, str] = {}
    receipt_ref = None
    if level == "C4":
        forecast = {
            "schema": "mirofish.vox.preregistered_forecast.v1", "version": 1,
            "generated_at": "2026-07-14T08:00:00Z",
            "training_cutoff": "2026-07-14T09:00:00Z",
            "report_id": binding["report_id"], "simulation_id": binding["simulation_id"],
            "run_id": binding["run_id"], "config_sha256": binding["config_sha256"],
            "input_sha256": binding["input_sha256"], "baseline_snapshot_sha256": baseline_digest,
            "variable_id": "outcome_x", "variable_label": "Outcome X", "unit": "share",
            "categories": ["yes", "no"],
            "heldout_predictions": [
                {
                    "id": f"holdout-{index}",
                    "distribution": [0.9, 0.1] if index < 16 else [0.1, 0.9],
                }
                for index in range(30)
            ],
        }
        if forecast_mutate is not None:
            forecast_mutate(forecast)
        raw = canonical_json_bytes(forecast)
        forecast_name = "preregistered-forecast.json"
        forecast_digest = hashlib.sha256(raw).hexdigest()
        (root / forecast_name).write_bytes(raw)
        forecast_registry[forecast_name] = forecast_digest
        fixed_time = issuer_time or datetime(2026, 7, 14, 8, 30, tzinfo=timezone.utc)
        monkeypatch.setattr(
            "app.services.vox_science.verification._utc_now", lambda: fixed_time
        )
        issued = issue_preregistration_receipt(
            preregistration_id="prereg-2026-001",
            report_id=binding["report_id"], simulation_id=binding["simulation_id"],
            run_id=binding["run_id"], config_sha256=binding["config_sha256"],
            input_sha256=binding["input_sha256"], baseline_snapshot_path=baseline_name,
            baseline_snapshot_sha256=baseline_digest, forecast_path=forecast_name,
            forecast_sha256=forecast_digest, training_cutoff="2026-07-14T09:00:00Z",
            target_variable="outcome_x",
            minimum_brier_skill_score=minimum_brier_skill_score,
            maximum_log_loss_ratio=maximum_log_loss_ratio,
            policy_id=policy_id,
        )
        receipt_ref = (issued.relative_path, issued.sha256)
    evidence = _claim_payload(
        binding, level=level, run_refs=run_refs or None, receipt_ref=receipt_ref
    )
    if mutate is not None:
        mutate(evidence)
    evidence_raw = canonical_json_bytes(evidence)
    evidence_name = "claim-evidence.json"
    (root / evidence_name).write_bytes(evidence_raw)
    evidence_digest = hashlib.sha256(evidence_raw).hexdigest()
    manifest = {
        "schema": "mirofish.vox.claim_evidence_authority.v1",
        "version": 1,
        "generated_at": "2026-07-14T12:00:00Z",
        "baselines": {baseline_name: baseline_digest},
        "claim_evidence": {evidence_name: evidence_digest},
        "stability_runs": run_registry,
        "preregistered_forecasts": forecast_registry,
    }
    manifest_raw = canonical_json_bytes(manifest)
    (root / "authority-manifest.json").write_bytes(manifest_raw)
    monkeypatch.setattr(
        Config,
        "VOX_CLAIM_AUTHORITY_MANIFEST_SHA256",
        hashlib.sha256(manifest_raw).hexdigest(),
    )
    if tamper_after_authorization is not None:
        tamper_after_authorization(evidence)
        (root / evidence_name).write_bytes(canonical_json_bytes(evidence))
    return _build(
        authorized_baseline_snapshot_path=baseline_name,
        claim_evidence_path=evidence_name,
        reported_correlations=reported_correlations,
    )


def _reauthorize_claim(
    root: Path, monkeypatch: pytest.MonkeyPatch, evidence: dict
) -> None:
    raw = canonical_json_bytes(evidence)
    (root / "claim-evidence.json").write_bytes(raw)
    manifest = json.loads((root / "authority-manifest.json").read_text(encoding="utf-8"))
    manifest["claim_evidence"]["claim-evidence.json"] = hashlib.sha256(raw).hexdigest()
    manifest_raw = canonical_json_bytes(manifest)
    (root / "authority-manifest.json").write_bytes(manifest_raw)
    monkeypatch.setattr(
        Config,
        "VOX_CLAIM_AUTHORITY_MANIFEST_SHA256",
        hashlib.sha256(manifest_raw).hexdigest(),
    )


def _rehash_resign_and_anchor(artifacts: dict) -> None:
    gate = artifacts["harness_science_gate.json"]
    for name, payload in artifacts.items():
        if name != "harness_science_gate.json":
            gate["artifact_hashes"][name] = hashlib.sha256(
                canonical_json_bytes(payload)
            ).hexdigest()
    sign_gate(gate)
    write_current_generation_anchor("report_claim_test", gate)


def test_c2_requires_materialized_baseline_snapshot():
    artifacts = _build(baseline_distribution=[0.6, 0.4], sample_distribution=[0.55, 0.45])

    assert artifacts["harness_science_gate.json"]["passes_execution_gate"] is True
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"
    assert artifacts["baseline_registry.json"]["loaded_baseline"] is False


def test_c2_requires_mae_kl_and_wasserstein(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.services.vox_science.artifacts.mean_absolute_error", lambda *_: math.nan
    )
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C2")

    fidelity = artifacts["fidelity_report.json"]
    assert fidelity["claim_eligibility"]["C2"] is False
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"
    assert "calibration_metrics_unavailable_or_invalid" in fidelity["claim_blockers"]


def test_url_catalog_is_not_a_calibration_baseline():
    registry = _build()["baseline_registry.json"]

    assert registry["anchors"]
    assert registry["catalog_semantics"] == "metadata_only_not_a_loaded_calibration_baseline"
    assert all(anchor["loaded_baseline"] is False for anchor in registry["anchors"])
    assert registry["loaded_baseline"] is False


def test_missing_external_error_caps_claim_at_c1():
    artifacts = _build()

    assert artifacts["fidelity_report.json"]["mean_absolute_error_pp"] is None
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_valid_snapshot_and_three_computed_metrics_reach_c2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C2")

    fidelity = artifacts["fidelity_report.json"]
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C2"
    assert fidelity["calibration_evidence"]["status"] == "measured"
    for metric in ("mae", "kl", "wasserstein"):
        assert fidelity["calibration_evidence"]["metrics"][metric]["status"] == "computed"
        assert math.isfinite(fidelity["calibration_evidence"]["metrics"][metric]["value"])


def test_categorical_mass_reversal_has_nonzero_w1_and_blocks_c2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def reverse_mass(payload: dict) -> None:
        predicted = [0.4, 0.6]
        payload["evaluation"]["predicted_distribution"] = predicted
        payload["evaluation"]["sample_sha256"] = vector_sha256(predicted)

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C2", mutate=reverse_mass
    )

    assert artifacts["fidelity_report.json"]["multi_metric"]["wasserstein_distance"] == 0.2
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"
    assert "c2_calibration_thresholds_not_met" in artifacts["fidelity_report.json"]["claim_blockers"]


@pytest.mark.parametrize("invalid_key", ["", "too-short"])
def test_missing_or_short_host_key_cannot_emit_c2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_key: str,
):
    _with_authorized_evidence(tmp_path, monkeypatch)
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", invalid_key)
    artifacts = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    gate = artifacts["harness_science_gate.json"]
    assert gate["claim_level"] == "C1"
    assert gate["hmac_sha256"] is None
    assert "host_signing_key_unavailable" in gate["claim_blockers"]


def test_consumer_accepts_only_complete_same_generation_hash_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch)
    write_current_generation_anchor(
        "report_claim_test", artifacts["harness_science_gate.json"]
    )
    assert _valid_science_generation(artifacts, "report_claim_test") is True

    artifacts["fidelity_report.json"]["overall_score"] = 999
    assert _valid_science_generation(artifacts, "report_claim_test") is False


@pytest.mark.parametrize("level", ["C2", "C3", "C4"])
def test_projection_accepts_authentic_materialized_calibration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, level: str
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level=level)
    write_current_generation_anchor(
        "report_claim_test", artifacts["harness_science_gate.json"]
    )
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda _report_id, name: artifacts.get(name),
    )

    projection = verified_vox_claim_projection("report_claim_test", artifacts)

    assert projection["verified"] is True
    assert projection["passes_execution_gate"] is True
    assert projection["claim_level"] == level
    assert projection["calibrated"] is True
    assert projection["calibration_mode"] == "materialized_external_baseline"
    assert set(projection["calibration_evidence"]) == {
        "baseline_snapshot_sha256",
        "claim_evidence_sha256",
        "authority_manifest_sha256",
    }
    if level == "C4":
        assert projection["prospective_validation"]["per_id_scoring"]["algorithm"] == (
            "multiclass_brier_log_loss_per_id.v1"
        )


def test_signed_policy_downgrade_from_c2_projects_verified_c1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C2",
        reported_correlations={"latent_construct": 0.9},
    )
    write_current_generation_anchor(
        "report_claim_test", artifacts["harness_science_gate.json"]
    )
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda _report_id, name: artifacts.get(name),
    )

    projection = verified_vox_claim_projection("report_claim_test", artifacts)

    assert artifacts["fidelity_report.json"]["claim_eligibility"]["C2"] is True
    assert artifacts["claim_policy_audit.json"]["passes_claim_policy"] is False
    assert projection["verified"] is True
    assert projection["claim_level"] == "C1"
    assert projection["calibrated"] is False
    assert projection["calibration_mode"] == "synthetic_trace_only"
    assert projection["calibration_evidence"] is None


def test_signed_semantically_fake_policy_downgrade_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C2")
    artifacts["claim_policy_audit.json"]["claim_level"] = "C1"
    artifacts["claim_policy_audit.json"]["allowed_language"] = [
        "simulacao sintetica exploratoria com rastreabilidade metodologica"
    ]
    artifacts["methodology_manifest.json"]["claim_target"] = "C1"
    artifacts["harness_science_gate.json"]["claim_level"] = "C1"
    artifacts["harness_science_gate.json"]["max_external_language"] = (
        "simulacao sintetica exploratoria com rastreabilidade metodologica"
    )
    _rehash_resign_and_anchor(artifacts)
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda _report_id, name: artifacts.get(name),
    )

    projection = verified_vox_claim_projection("report_claim_test", artifacts)

    assert projection["verified"] is False
    assert projection["claim_level"] is None


def test_signed_semantically_fake_policy_upgrade_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C2",
        reported_correlations={"latent_construct": 0.9},
    )
    artifacts["harness_science_gate.json"]["claim_level"] = "C2"
    artifacts["harness_science_gate.json"]["max_external_language"] = (
        "simulacao sintetica calibrada por dados publicos e robustez auditada"
    )
    sign_gate(artifacts["harness_science_gate.json"])
    write_current_generation_anchor(
        "report_claim_test", artifacts["harness_science_gate.json"]
    )
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda _report_id, name: artifacts.get(name),
    )

    projection = verified_vox_claim_projection("report_claim_test", artifacts)

    assert projection["verified"] is False
    assert projection["claim_level"] is None


def test_snapshot_tamper_downgrades_to_c1(tmp_path: Path):
    name, digest = _materialize_snapshot(tmp_path)
    tampered = _snapshot_payload()
    tampered["data"]["distributions"]["outcome_x"] = [0.7, 0.3]
    (tmp_path / name).write_bytes(canonical_json_bytes(tampered))

    artifacts = _build(
        baseline_snapshot_path=name,
        baseline_snapshot_root=str(tmp_path),
        baseline_snapshot_sha256=digest,
        sample_distribution=[0.55, 0.45],
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"
    assert "snapshot_sha256_mismatch" in artifacts["harness_science_gate.json"]["claim_blockers"]


def test_stale_snapshot_hash_downgrades_to_c1(tmp_path: Path):
    name, _ = _materialize_snapshot(tmp_path)
    artifacts = _build(
        baseline_snapshot_path=name,
        baseline_snapshot_root=str(tmp_path),
        baseline_snapshot_sha256="0" * 64,
        sample_distribution=[0.55, 0.45],
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c3_requires_computed_subgroup_error_and_stability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C3")
    fidelity = artifacts["fidelity_report.json"]

    assert artifacts["harness_science_gate.json"]["claim_level"] == "C3"
    assert fidelity["subgroup_evidence"]["status"] == "computed"
    assert fidelity["stability_evidence"]["status"] == "computed"


def test_c3_reversed_category_runs_fail_declared_order_stability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C3",
        run_distribution_transform=lambda index, _distribution: (
            [0.9, 0.1] if index % 2 else [0.1, 0.9]
        ),
    )

    stability = artifacts["fidelity_report.json"]["stability_evidence"]
    assert stability["algorithm"] == "declared_category_order_adjacent_run_stability.v2"
    assert stability["minimum_score"] < 0.7
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C2"


def test_c4_requires_measured_prospective_heldout_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C4")

    assert artifacts["harness_science_gate.json"]["claim_level"] == "C4"
    measured = artifacts["fidelity_report.json"]["prospective_evidence"]
    assert measured["status"] == "measured"
    assert len(measured["heldout_ids"]) == 30
    assert set(measured["metrics"]) == {
        "mae", "kl", "wasserstein", "brier_score", "log_loss"
    }
    assert measured["per_id_scoring"]["algorithm"] == (
        "multiclass_brier_log_loss_per_id.v1"
    )
    assert measured["per_id_scoring"]["brier_skill_score"] > 0
    assert measured["per_id_scoring"]["passes_thresholds"] is True


def test_c4_balanced_marginal_with_every_per_id_prediction_swapped_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def swap_every_prediction(forecast: dict) -> None:
        for index, item in enumerate(forecast["heldout_predictions"]):
            item["distribution"] = [0.1, 0.9] if index < 16 else [0.9, 0.1]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", forecast_mutate=swap_every_prediction
    )
    prospective = artifacts["fidelity_report.json"]["prospective_evidence"]

    assert prospective["per_id_scoring"]["passes_thresholds"] is False
    assert prospective["per_id_scoring"]["brier_skill_score"] < 0
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C3"


def test_c4_correct_confident_per_id_predictions_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def correct_predictions(forecast: dict) -> None:
        for index, item in enumerate(forecast["heldout_predictions"]):
            item["distribution"] = [0.9, 0.1] if index < 16 else [0.1, 0.9]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", forecast_mutate=correct_predictions
    )
    scoring = artifacts["fidelity_report.json"]["prospective_evidence"]["per_id_scoring"]

    assert scoring["brier_skill_score"] > 0
    assert scoring["log_loss"] <= scoring["baseline_log_loss"]
    assert scoring["passes_thresholds"] is True
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C4"


def test_preregistered_performance_criteria_exact_boundary_below_and_above():
    criteria = {
        "policy_id": "vox-c4-material-v1",
        "algorithm": "multiclass_brier_log_loss_per_id.v1",
        "minimum_brier_skill_score": 0.05,
        "maximum_log_loss_ratio": 0.99,
    }
    assert _passes_preregistered_performance(
        brier_skill=0.05,
        log_loss=0.99,
        baseline_log_loss=1.0,
        criteria=criteria,
    )
    assert not _passes_preregistered_performance(
        brier_skill=0.049999,
        log_loss=0.98,
        baseline_log_loss=1.0,
        criteria=criteria,
    )
    assert not _passes_preregistered_performance(
        brier_skill=0.06,
        log_loss=0.990001,
        baseline_log_loss=1.0,
        criteria=criteria,
    )


def test_c4_epsilon_improvement_below_preregistered_floor_caps_c3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def epsilon_forecast(forecast: dict) -> None:
        for item in forecast["heldout_predictions"]:
            item["distribution"] = [0.51, 0.49]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", forecast_mutate=epsilon_forecast
    )
    scoring = artifacts["fidelity_report.json"]["prospective_evidence"]["per_id_scoring"]

    assert 0 < scoring["brier_skill_score"] < 0.05
    assert scoring["passes_thresholds"] is False
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C3"


def test_receipt_performance_criteria_tamper_and_posthoc_override_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    state_root = tmp_path / "verification-state"
    receipt_path = next(state_root.glob("prereg-*.json"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["performance_criteria"]["minimum_brier_skill_score"] = 0.01
    receipt_path.write_bytes(canonical_json_bytes(receipt))

    tampered = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert tampered["harness_science_gate.json"]["claim_level"] == "C1"

    fresh_root = tmp_path / "fresh"
    fresh_root.mkdir()
    posthoc = _with_authorized_evidence(
        fresh_root,
        monkeypatch,
        level="C4",
        mutate=lambda payload: payload["prospective"].update(
            {"performance_criteria": {"minimum_brier_skill_score": 0.0}}
        ),
    )
    assert posthoc["harness_science_gate.json"]["claim_level"] == "C1"


@pytest.mark.parametrize("attack", ["relaxed", "unknown_policy"])
def test_even_validly_signed_relaxed_or_unknown_material_policy_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    evidence = json.loads((tmp_path / "claim-evidence.json").read_text(encoding="utf-8"))
    receipt_path = (
        tmp_path
        / "verification-state"
        / evidence["prospective"]["preregistration_receipt_path"]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if attack == "relaxed":
        receipt["performance_criteria"]["minimum_brier_skill_score"] = 0.01
        receipt["performance_criteria"]["maximum_log_loss_ratio"] = 1.0
    else:
        receipt["performance_criteria"]["policy_id"] = "unknown-policy"
    unsigned = {key: value for key, value in receipt.items() if key != "hmac_sha256"}
    receipt["hmac_sha256"] = hmac.new(
        Config.VOX_CLAIM_SIGNING_KEY.encode("utf-8"),
        canonical_json_bytes(unsigned),
        hashlib.sha256,
    ).hexdigest()
    raw = canonical_json_bytes(receipt)
    receipt_path.write_bytes(raw)
    evidence["prospective"]["preregistration_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    _reauthorize_claim(tmp_path, monkeypatch, evidence)

    rejected = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )

    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"
    assert "claim_preregistration_performance_criteria_invalid" in (
        rejected["harness_science_gate.json"]["claim_blockers"]
    )


@pytest.mark.parametrize(
    ("minimum_skill", "maximum_ratio"),
    [(0.01, 0.99), (0.05, 1.0)],
)
def test_preregistration_rejects_relaxed_material_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    minimum_skill: float,
    maximum_ratio: float,
):
    with pytest.raises(SnapshotValidationError, match="performance_criteria"):
        _with_authorized_evidence(
            tmp_path,
            monkeypatch,
            level="C4",
            minimum_brier_skill_score=minimum_skill,
            maximum_log_loss_ratio=maximum_ratio,
        )


def test_preregistration_accepts_exact_default_and_stricter_material_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    default = _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    assert default["harness_science_gate.json"]["claim_level"] == "C4"
    assert default["fidelity_report.json"]["prospective_evidence"]["per_id_scoring"][
        "preregistered_criteria"
    ] == {
        "policy_id": "vox-c4-material-v1",
        "algorithm": "multiclass_brier_log_loss_per_id.v1",
        "minimum_brier_skill_score": 0.05,
        "maximum_log_loss_ratio": 0.99,
    }

    stricter_root = tmp_path / "stricter"
    stricter_root.mkdir()
    stricter = _with_authorized_evidence(
        stricter_root,
        monkeypatch,
        level="C4",
        minimum_brier_skill_score=0.1,
        maximum_log_loss_ratio=0.95,
    )
    assert stricter["harness_science_gate.json"]["claim_level"] == "C4"


def test_c4_constant_baseline_forecast_has_zero_skill_and_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def baseline_forecast(forecast: dict) -> None:
        for item in forecast["heldout_predictions"]:
            item["distribution"] = [0.6, 0.4]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", forecast_mutate=baseline_forecast
    )
    scoring = artifacts["fidelity_report.json"]["prospective_evidence"]["per_id_scoring"]

    assert scoring["brier_skill_score"] == 0.0
    assert scoring["passes_thresholds"] is False
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C3"


@pytest.mark.parametrize(
    "outcome_mutation",
    [
        lambda outcomes: outcomes[0].update({"value": "unknown"}),
        lambda outcomes: outcomes[0].update({"id": "wrong-id"}),
    ],
)
def test_c4_rejects_unknown_label_or_id_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome_mutation
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C4",
        mutate=lambda payload: outcome_mutation(payload["prospective"]["observed_outcomes"]),
    )

    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


@pytest.mark.parametrize("distribution", [[60.0, 40.0], [6.0, 4.0], [0.0, 0.0]])
def test_baseline_probability_scale_ambiguity_is_rejected(
    tmp_path: Path, distribution: list[float]
):
    payload = _snapshot_payload()
    payload["data"]["distributions"]["outcome_x"] = distribution
    name, digest = _materialize_snapshot(tmp_path, payload)

    with pytest.raises(SnapshotValidationError):
        load_baseline_snapshot(
            relative_path=name,
            trusted_root=str(tmp_path),
            expected_sha256=digest,
            target_variable="outcome_x",
        )


def test_probability_sum_tolerance_accepts_near_one(
    tmp_path: Path,
):
    payload = _snapshot_payload()
    payload["data"]["distributions"]["outcome_x"] = [0.6000004, 0.3999997]
    name, digest = _materialize_snapshot(tmp_path, payload)

    snapshot = load_baseline_snapshot(
        relative_path=name,
        trusted_root=str(tmp_path),
        expected_sha256=digest,
        target_variable="outcome_x",
    )
    assert snapshot.observed == pytest.approx((0.6000004, 0.3999997))


def test_claim_distribution_sum_and_category_label_mismatch_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def invalid_claim(payload: dict) -> None:
        payload["evaluation"]["categories"] = ["no", "yes"]
        payload["evaluation"]["predicted_distribution"] = [6.0, 4.0]
        payload["evaluation"]["sample_sha256"] = vector_sha256([6.0, 4.0])

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C2", mutate=invalid_claim
    )

    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_rows_baseline_is_valid_input_but_explicitly_capped_at_c1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    payload = _snapshot_payload()
    payload["data"] = {
        "kind": "rows",
        "rows": [
            {
                "id": f"row-{index}",
                "subgroup": "group_a" if index % 2 == 0 else "group_b",
                "observed_at": "2026-07-13T11:00:00Z",
                "values": {"outcome_x": 1.0 if index < 24 else 0.0},
            }
            for index in range(40)
        ],
    }
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C2",
        snapshot_payload=payload,
    )

    assert artifacts["baseline_registry.json"]["loaded_baseline"] is True
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"
    assert "row_baseline_probability_metrics_not_implemented" in (
        artifacts["fidelity_report.json"]["claim_blockers"]
    )


def test_planned_forecast_cannot_self_assert_c4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C3")
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C3"


def test_self_declared_prospective_dict_cannot_self_assert_c4():
    artifacts = _build(
        prospective_evidence={"status": "measured", "heldout_ids": ["fake"]},
        sample_distribution=[0.55, 0.45],
        stability_runs=[[0.55, 0.45], [0.54, 0.46], [0.56, 0.44]],
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_cross_run_materialized_evidence_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        mutate=lambda payload: payload["binding"].update(run_id="different-run"),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


@pytest.mark.parametrize(
    "binding_field",
    ["config_sha256", "baseline_snapshot_sha256"],
)
def test_cross_binding_materialized_evidence_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    binding_field: str,
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        mutate=lambda payload: payload["binding"].update(
            {binding_field: "0" * 64}
        ),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c2_rejects_evaluation_n_below_30(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        mutate=lambda payload: payload["evaluation"].update(sample_ids=["only-one"]),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c3_rejects_subgroup_n_below_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C3",
        mutate=lambda payload: payload["stability"]["subgroups"]["group_a"].update(
            predicted_n=29
        ),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c3_rejects_subgroup_prediction_ids_below_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def shrink(payload):
        subgroup = payload["stability"]["subgroups"]["group_a"]
        subgroup["sample_ids"] = subgroup["sample_ids"][:29]
        subgroup["predicted_n"] = 29

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C3", mutate=shrink
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c3_rejects_unapproved_run_artifact_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C3",
        mutate=lambda payload: payload["stability"]["runs"][0].update(
            artifact_sha256="0" * 64
        ),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c3_rejects_duplicate_stability_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def duplicate_seed(payload):
        payload["stability"]["runs"][1]["seed"] = payload["stability"]["runs"][0]["seed"]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C3", mutate=duplicate_seed
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_preregistration_after_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    with pytest.raises(SnapshotValidationError):
        _with_authorized_evidence(
            tmp_path,
            monkeypatch,
            level="C4",
            issuer_time=datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc),
        )


def test_c4_rejects_heldout_overlap_with_training(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def overlap(payload):
        payload["prospective"]["heldout_ids"][0] = payload["prospective"]["training_ids"][0]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", mutate=overlap
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_missing_authorized_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C4",
        mutate=lambda payload: payload["prospective"].update(
            preregistration_receipt_sha256="0" * 64
        ),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_missing_stored_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C4"
    next((tmp_path / "verification-state").glob("prereg-*.json")).unlink()
    rejected = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_tampered_stored_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    receipt_path = next((tmp_path / "verification-state").glob("prereg-*.json"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["issued_at"] = "2000-01-01T00:00:00Z"
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    rejected = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"


def test_retrodated_legacy_signed_receipt_outside_state_root_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    evidence = json.loads((tmp_path / "claim-evidence.json").read_text(encoding="utf-8"))
    forecast_sha = hashlib.sha256((tmp_path / "preregistered-forecast.json").read_bytes()).hexdigest()
    forged = {
        "schema": "mirofish.vox.preregistration_receipt.v1", "version": 1,
        "issued_at": "2000-01-01T00:00:00Z", "preregistration_id": "prereg-2026-001",
        "report_id": "report_claim_test", "simulation_id": "sim_claim_test",
        "run_id": evidence["binding"]["run_id"], "config_sha256": evidence["binding"]["config_sha256"],
        "input_sha256": evidence["binding"]["input_sha256"],
        "baseline_snapshot_sha256": evidence["binding"]["baseline_snapshot_sha256"],
        "training_cutoff": "2026-07-14T09:00:00Z",
        "heldout_plan_ids": [f"holdout-{index}" for index in range(30)],
        "forecast_path": "preregistered-forecast.json", "forecast_sha256": forecast_sha,
        "signature_algorithm": "hmac-sha256", "hmac_sha256": None,
    }
    unsigned = {key: value for key, value in forged.items() if key != "hmac_sha256"}
    forged["hmac_sha256"] = hmac.new(
        Config.VOX_CLAIM_SIGNING_KEY.encode("utf-8"),
        canonical_json_bytes(unsigned),
        hashlib.sha256,
    ).hexdigest()
    forged_raw = canonical_json_bytes(forged)
    (tmp_path / "legacy-receipt.json").write_bytes(forged_raw)
    evidence["prospective"]["preregistration_receipt_path"] = "legacy-receipt.json"
    evidence["prospective"]["preregistration_receipt_sha256"] = hashlib.sha256(forged_raw).hexdigest()
    _reauthorize_claim(tmp_path, monkeypatch, evidence)
    rejected = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"


def test_preregistration_id_cannot_be_issued_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    model = _build()["model_run_registry.json"]
    with pytest.raises(SnapshotValidationError, match="already_issued"):
        issue_preregistration_receipt(
            preregistration_id="prereg-2026-001",
            report_id="report_claim_test", simulation_id="sim_claim_test",
            run_id=model["run_id"], config_sha256=model["config_sha256"],
            input_sha256=model["prompt_registry_hash"], baseline_snapshot_path="baseline.json",
            baseline_snapshot_sha256=hashlib.sha256((tmp_path / "baseline.json").read_bytes()).hexdigest(),
            forecast_path="preregistered-forecast.json",
            forecast_sha256=hashlib.sha256((tmp_path / "preregistered-forecast.json").read_bytes()).hexdigest(),
            training_cutoff="2026-07-14T09:00:00Z", target_variable="outcome_x",
        )


def test_c4_rejects_missing_or_tampered_precommitted_forecast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    (tmp_path / "preregistered-forecast.json").write_bytes(b'{"tampered":true}')
    rejected = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"


@pytest.mark.parametrize("attack", ["order", "duplicate"])
def test_c4_rejects_heldout_id_order_or_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
):
    def mutate(payload):
        ids = payload["prospective"]["heldout_ids"]
        if attack == "order":
            ids[0], ids[1] = ids[1], ids[0]
        else:
            ids[1] = ids[0]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", mutate=mutate
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_posthoc_predicted_distribution_in_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C4",
        mutate=lambda payload: payload["prospective"].update(
            predicted_distribution=[0.53, 0.47]
        ),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_forecast_generated_after_cutoff_cannot_be_issued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    with pytest.raises(SnapshotValidationError):
        _with_authorized_evidence(
            tmp_path,
            monkeypatch,
            level="C4",
            forecast_mutate=lambda forecast: forecast.update(
                generated_at="2026-07-14T10:00:00Z"
            ),
        )


def test_c4_cross_report_replay_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _with_authorized_evidence(tmp_path, monkeypatch, level="C4")
    rejected = _build(
        report_id="other-report",
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_evidence_authored_before_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        level="C4",
        mutate=lambda payload: payload.update(generated_at="2026-07-15T11:00:00Z"),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_rejects_heldout_time_before_cutoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def early_heldout(payload):
        payload["prospective"]["heldout_times"][0] = "2026-07-14T08:30:00Z"

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", mutate=early_heldout
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_c4_metrics_over_threshold_cap_at_c3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def high_error(payload):
        payload["prospective"]["observed_outcomes"] = [
            {"id": f"holdout-{index}", "value": "no"} for index in range(30)
        ]

    artifacts = _with_authorized_evidence(
        tmp_path, monkeypatch, level="C4", mutate=high_error
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C3"


def test_claim_evidence_tamper_after_authorization_caps_at_c1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    artifacts = _with_authorized_evidence(
        tmp_path,
        monkeypatch,
        tamper_after_authorization=lambda payload: payload["evaluation"].update(
            predicted_distribution=[0.51, 0.49]
        ),
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_nan_cannot_be_materialized_as_canonical_claim_evidence():
    payload = {"values": [math.nan]}
    with pytest.raises(ValueError):
        canonical_json_bytes(payload)


@pytest.mark.parametrize(
    "invalid_sample",
    ([math.nan, 0.5], [math.inf, 0.5], [True, 0.5], ["0.5", 0.5], [0.0, 0.0]),
)
def test_nonfinite_bool_string_and_zero_mass_cap_claim_at_c1(
    tmp_path: Path, invalid_sample: list[object]
):
    name, digest = _materialize_snapshot(tmp_path)
    artifacts = _build(
        baseline_snapshot_path=name,
        baseline_snapshot_root=str(tmp_path),
        baseline_snapshot_sha256=digest,
        sample_distribution=invalid_sample,
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_snapshot_path_escape_and_absolute_path_are_rejected(tmp_path: Path):
    name, digest = _materialize_snapshot(tmp_path)
    for unsafe in ("../baseline.json", str((tmp_path / name).resolve())):
        artifacts = _build(
            baseline_snapshot_path=unsafe,
            baseline_snapshot_root=str(tmp_path),
            baseline_snapshot_sha256=digest,
            sample_distribution=[0.55, 0.45],
        )
        assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_snapshot_symlink_is_rejected_when_supported(tmp_path: Path):
    name, digest = _materialize_snapshot(tmp_path)
    link = tmp_path / "linked.json"
    try:
        os.symlink(tmp_path / name, link)
    except OSError:
        pytest.skip("symlink creation is not available for this Windows account")
    artifacts = _build(
        baseline_snapshot_path=link.name,
        baseline_snapshot_root=str(tmp_path),
        baseline_snapshot_sha256=digest,
        sample_distribution=[0.55, 0.45],
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_snapshot_size_budget_caps_claim_at_c1(tmp_path: Path):
    path = tmp_path / "oversized.json"
    raw = b" " * 1_000_001
    path.write_bytes(raw)
    artifacts = _build(
        baseline_snapshot_path=path.name,
        baseline_snapshot_root=str(tmp_path),
        baseline_snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        sample_distribution=[0.55, 0.45],
    )
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C1"


def test_authority_root_symlink_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    real = tmp_path / "real"
    real.mkdir()
    artifacts = _with_authorized_evidence(real, monkeypatch)
    assert artifacts["harness_science_gate.json"]["claim_level"] == "C2"
    link = tmp_path / "authority-link"
    try:
        os.symlink(real, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink unavailable")
    monkeypatch.setattr(Config, "VOX_CLAIM_EVIDENCE_ROOT", str(link))
    rejected = _build(
        authorized_baseline_snapshot_path="baseline.json",
        claim_evidence_path="claim-evidence.json",
    )
    assert rejected["harness_science_gate.json"]["claim_level"] == "C1"


def test_extreme_json_depth_is_rejected_without_recursion_escape(tmp_path: Path):
    raw = (b'{"a":' * 20_000) + b"0" + (b"}" * 20_000)
    path = tmp_path / "deep.json"
    path.write_bytes(raw)
    with pytest.raises(SnapshotValidationError):
        load_materialized_json(
            relative_path=path.name,
            trusted_root=str(tmp_path.resolve()),
            expected_sha256=hashlib.sha256(raw).hexdigest(),
            reason_prefix="deep_test",
        )
