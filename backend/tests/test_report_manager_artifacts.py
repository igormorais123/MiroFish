"""Testes dos artefatos auditaveis do ReportManager."""
from __future__ import annotations

import math
import os

import pytest

from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.vox_science.verification import (
    sign_gate,
    verify_current_generation_anchor,
)
from app.config import Config


def _signed_gate(report_id: str, generation_id: str) -> dict:
    gate = {
        "schema": "mirofish.vox.harness_science_gate.v2",
        "report_id": report_id,
        "simulation_id": "sim-1",
        "generation_id": generation_id,
        "passes_execution_gate": True,
        "claim_level": "C1",
        "artifact_hashes": {},
        "signature_algorithm": "hmac-sha256",
        "hmac_sha256": None,
    }
    assert sign_gate(gate) is True
    return gate


def test_report_manager_salva_lista_e_carrega_artefato_json(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))

    ReportManager.save_json_artifact("report_1", "system_gate.json", {
        "passes_gate": True,
        "metrics": {"total_actions_count": 12},
    })
    ReportManager.save_json_artifact("report_1", "progress.json", {"progress": 50})

    artifacts = ReportManager.list_json_artifacts("report_1")
    loaded = ReportManager.load_json_artifact("report_1", "system_gate")

    assert [item["name"] for item in artifacts] == ["system_gate.json"]
    assert loaded["passes_gate"] is True
    assert loaded["metrics"]["total_actions_count"] == 12


def test_report_manager_nao_carrega_artefato_inexistente(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))

    assert ReportManager.load_json_artifact("report_ausente", "system_gate") is None
    assert ReportManager.list_json_artifacts("report_ausente") == []


def test_report_manager_rejeita_nan_sem_corromper_artefato_anterior(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    ReportManager.save_json_artifact("report_1", "gate.json", {"value": 1.0})

    with pytest.raises(ValueError):
        ReportManager.save_json_artifact("report_1", "gate.json", {"value": math.nan})

    assert ReportManager.load_json_artifact("report_1", "gate.json") == {"value": 1.0}


def test_report_manager_promove_gate_do_bundle_por_ultimo(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    real_replace = os.replace
    promoted = []

    def tracking_replace(source, target):
        promoted.append(os.path.basename(target))
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", tracking_replace)
    ReportManager.save_json_artifact_bundle(
        "report_1",
        {
            "fidelity_report.json": {"generation_id": "g1"},
            "harness_science_gate.json": {"generation_id": "g1", "passes_execution_gate": True},
        },
    )

    assert promoted == ["fidelity_report.json", "harness_science_gate.json"]
    assert ReportManager.load_json_artifact("report_1", "harness_science_gate.json")[
        "generation_id"
    ] == "g1"


def test_failure_before_gate_promotion_preserves_old_current_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "test-only-signing-key-0123456789abcdef")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(state.resolve()))
    old = _signed_gate("report_1", "old-generation")
    ReportManager.save_json_artifact_bundle("report_1", {"harness_science_gate.json": old})

    real_replace = os.replace
    new = _signed_gate("report_1", "new-generation")

    def fail_gate_replace(source, target):
        if os.path.basename(target) == "harness_science_gate.json":
            raise OSError("injected gate promotion failure")
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", fail_gate_replace)
    with pytest.raises(OSError):
        ReportManager.save_json_artifact_bundle(
            "report_1", {"fidelity_report.json": {"generation_id": "new-generation"}, "harness_science_gate.json": new}
        )

    assert verify_current_generation_anchor("report_1", old) is True
    assert verify_current_generation_anchor("report_1", new) is False
    assert ReportManager.load_json_artifact("report_1", "harness_science_gate.json")["generation_id"] == "old-generation"


def test_failure_after_gate_before_anchor_cannot_verify_new_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setattr(Config, "VOX_CLAIM_SIGNING_KEY", "test-only-signing-key-0123456789abcdef")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(Config, "VOX_CLAIM_VERIFICATION_STATE_ROOT", str(state.resolve()))
    old = _signed_gate("report_1", "old-generation")
    ReportManager.save_json_artifact_bundle("report_1", {"harness_science_gate.json": old})
    new = _signed_gate("report_1", "new-generation")

    monkeypatch.setattr(
        "app.services.vox_science.verification.write_current_generation_anchor",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("injected anchor failure")),
    )
    with pytest.raises(OSError):
        ReportManager.save_json_artifact_bundle(
            "report_1", {"harness_science_gate.json": new}
        )

    assert ReportManager.load_json_artifact("report_1", "harness_science_gate.json")["generation_id"] == "new-generation"
    assert verify_current_generation_anchor("report_1", old) is True
    assert verify_current_generation_anchor("report_1", new) is False


def test_report_delivery_status_exige_gate_e_auditoria():
    report = Report(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="testar cenario",
        status=ReportStatus.COMPLETED,
    )

    assert report.delivery_status() == "legacy_unverified"
    assert report.is_publishable() is False

    report.quality_gate = {"passes_gate": True}
    report.evidence_audit = {"passes_gate": True}

    payload = report.to_dict()
    assert payload["delivery_status"] == "publishable"
    assert payload["publishable"] is True

    report.quality_gate = {
        "passes_gate": True,
        "metrics": {
            "delivery_mode": "demo",
            "delivery_publishable_mode": False,
            "diagnostic_only": True,
        },
    }

    payload = report.to_dict()
    assert payload["delivery_status"] == "diagnostic_only"
    assert payload["publishable"] is False
