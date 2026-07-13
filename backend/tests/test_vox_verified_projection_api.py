from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from flask import Flask

from app.api import report_bp
from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.vox_science import build_vox_science_artifacts
from app.services.vox_science.verification import write_current_generation_anchor
from app.services.vox_science.baseline_snapshot import canonical_json_bytes
from app.services.harness_evidence_bundle import verified_vox_claim_projection
from app.config import Config


def _app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(report_bp, url_prefix="/api/report")
    return app


def _artifacts(monkeypatch, tmp_path: Path) -> dict:
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "test-only-signing-key-0123456789abcdef")
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(state.resolve()))
    artifacts = build_vox_science_artifacts(
        report_id="report_projection",
        simulation_id="sim_projection",
        graph_id="graph_projection",
        simulation_requirement="Avaliar proposta",
        quality_gate={
            "passes_gate": True,
            "metrics": {
                "profiles_count": 120,
                "total_actions_count": 240,
                "graph_nodes_count": 10,
                "diversity": {"distinct_2": 0.8, "agent_activity_entropy_norm": 0.8},
            },
            "artifacts": {"simulation_config": {"exists": True}},
        },
        evidence_audit={"passes_gate": True},
        model_name="offline-test",
    )
    write_current_generation_anchor(
        "report_projection", artifacts["harness_science_gate.json"]
    )
    return artifacts


def _blocked_artifacts(monkeypatch, tmp_path: Path) -> dict:
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "test-only-signing-key-0123456789abcdef")
    state = tmp_path / "blocked-state"
    state.mkdir(exist_ok=True)
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(state.resolve()))
    artifacts = build_vox_science_artifacts(
        report_id="report_projection",
        simulation_id="sim_projection",
        graph_id="graph_projection",
        simulation_requirement="Avaliar proposta",
        quality_gate={"passes_gate": False, "metrics": {}, "artifacts": {}},
        evidence_audit={"passes_gate": True},
        model_name="offline-test",
    )
    write_current_generation_anchor(
        "report_projection", artifacts["harness_science_gate.json"]
    )
    return artifacts


def _request(monkeypatch, payloads: dict) -> dict:
    report = Report(
        report_id="report_projection",
        simulation_id="sim_projection",
        graph_id="graph_projection",
        simulation_requirement="Avaliar proposta",
        status=ReportStatus.COMPLETED,
    )
    metadata = [{"name": name} for name in payloads]
    monkeypatch.setattr(ReportManager, "get_report", lambda _report_id: report)
    monkeypatch.setattr(ReportManager, "list_json_artifacts", lambda _report_id: metadata)
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda _report_id, name: payloads.get(name),
    )
    response = _app().test_client().get("/api/report/report_projection/artifacts")
    assert response.status_code == 200
    return response.get_json()["data"]["verified_vox_claim"]


def test_api_exposes_server_verified_claim_projection(monkeypatch, tmp_path):
    projection = _request(monkeypatch, _artifacts(monkeypatch, tmp_path))

    assert projection["verified"] is True
    assert projection["claim_level"] == "C1"
    assert projection["calibrated"] is False
    assert projection["calibration_mode"] == "synthetic_trace_only"
    assert projection["calibration_evidence"] is None


def test_api_exposes_signed_anchored_c0_as_verified_but_blocked(monkeypatch, tmp_path):
    projection = _request(monkeypatch, _blocked_artifacts(monkeypatch, tmp_path))

    assert projection["verified"] is True
    assert projection["passes_execution_gate"] is False
    assert projection["claim_level"] == "C0"
    assert projection["calibrated"] is False
    assert projection["calibration_mode"] == "unverified_no_calibration"
    assert projection["calibration_evidence"] is None
    assert "system_gate_not_passed" in projection["blockers"]


def test_tampered_signed_c0_is_unverified_without_claim(monkeypatch, tmp_path):
    payloads = _blocked_artifacts(monkeypatch, tmp_path)
    payloads["fidelity_report.json"]["overall_score"] = 999

    projection = _request(monkeypatch, payloads)

    assert projection["verified"] is False
    assert projection["passes_execution_gate"] is False
    assert projection["claim_level"] is None
    assert projection["calibration_mode"] == "unverified_no_calibration"


def test_api_raw_gate_tamper_cannot_claim_c4(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    payloads["harness_science_gate.json"]["claim_level"] = "C4"
    payloads["harness_science_gate.json"]["max_external_language"] = "calibrado"

    projection = _request(monkeypatch, payloads)
    assert projection["verified"] is False
    assert projection["claim_level"] is None
    assert projection["calibrated"] is False


def test_api_missing_gate_defaults_to_unverified_without_claim(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    payloads.pop("harness_science_gate.json")

    projection = _request(monkeypatch, payloads)
    assert projection["verification_status"] == "unverified"
    assert projection["claim_level"] is None


def test_api_stale_mixed_generation_defaults_to_unverified_without_claim(monkeypatch, tmp_path):
    payloads = deepcopy(_artifacts(monkeypatch, tmp_path))
    payloads["fidelity_report.json"]["generation_id"] = "stale-generation"

    projection = _request(monkeypatch, payloads)
    assert projection["verified"] is False
    assert projection["claim_level"] is None


def test_tamper_all_outputs_and_rehash_cannot_forge_c4(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    generation = payloads["harness_science_gate.json"]["generation_id"]
    payloads["fidelity_report.json"]["claim_eligibility"] = {
        "C2": True, "C3": True, "C4": True
    }
    payloads["claim_policy_audit.json"]["claim_level"] = "C4"
    payloads["claim_policy_audit.json"]["allowed_language"] = [
        "previsao operacional monitoravel com cenario base e tese adversaria"
    ]
    payloads["methodology_manifest.json"]["claim_target"] = "C4"
    gate = payloads["harness_science_gate.json"]
    gate["claim_level"] = "C4"
    gate["max_external_language"] = (
        "previsao operacional monitoravel com cenario base e tese adversaria"
    )
    for name, payload in payloads.items():
        if name == "harness_science_gate.json":
            continue
        payload["generation_id"] = generation
        gate["artifact_hashes"][name] = hashlib.sha256(
            canonical_json_bytes(payload)
        ).hexdigest()

    projection = _request(monkeypatch, payloads)
    assert projection["verified"] is False
    assert projection["claim_level"] is None


def test_cross_report_bundle_replay_is_rejected(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(
        ReportManager,
        "load_json_artifact",
        lambda _report_id, name: payloads.get(name),
    )
    projection = verified_vox_claim_projection("report_B", payloads)
    assert projection["verified"] is False
    assert projection["claim_level"] is None


def test_missing_or_wrong_signing_key_rejects_projection(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "")
    assert _request(monkeypatch, payloads)["verified"] is False
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "x" * 32)
    assert _request(monkeypatch, payloads)["verified"] is False


def test_missing_or_tampered_anchor_rejects_projection(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    empty = tmp_path / "empty-state"
    empty.mkdir()
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(empty.resolve()))
    assert _request(monkeypatch, payloads)["verified"] is False

    state = tmp_path / "tampered-state"
    state.mkdir()
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(state.resolve()))
    write_current_generation_anchor("report_projection", payloads["harness_science_gate.json"])
    anchor = next(state.glob("*.json"))
    anchor.write_bytes(anchor.read_bytes().replace(b"report_projection", b"report_tampered__"))
    assert _request(monkeypatch, payloads)["verified"] is False


def test_verification_state_root_symlink_is_rejected(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    real_state = Path(Config.VOX_CLAIM_VERIFICATION_STATE_ROOT)
    link = tmp_path / "state-link"
    try:
        link.symlink_to(real_state, target_is_directory=True)
    except (OSError, NotImplementedError):
        import pytest

        pytest.skip("directory symlink unavailable")
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(link))
    assert _request(monkeypatch, payloads)["verified"] is False


def test_gate_hmac_tamper_is_rejected(monkeypatch, tmp_path):
    payloads = _artifacts(monkeypatch, tmp_path)
    payloads["harness_science_gate.json"]["hmac_sha256"] = "0" * 64
    assert _request(monkeypatch, payloads)["verified"] is False


def test_old_signed_bundle_replay_rejected_by_current_anchor(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.vox_science.artifacts._now_iso",
        lambda: "2026-07-13T10:00:00Z",
    )
    old = _artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.services.vox_science.artifacts._now_iso",
        lambda: "2026-07-13T11:00:00Z",
    )
    current = _artifacts(monkeypatch, tmp_path)

    assert _request(monkeypatch, old)["verified"] is False
    assert _request(monkeypatch, current)["verified"] is True


def test_verified_projection_schema_freezes_calibration_mode_enum():
    schema_path = (
        Path(__file__).parents[1]
        / "app"
        / "services"
        / "vox_science"
        / "verified-claim-projection.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["properties"]["calibration_mode"]["enum"] == [
        "unverified_no_calibration",
        "synthetic_trace_only",
        "materialized_external_baseline",
    ]
