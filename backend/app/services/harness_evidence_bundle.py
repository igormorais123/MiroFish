"""Contrato de evidencias do harness MiroFish para consumidores internos."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote, urljoin

from .report_agent import Report, ReportManager, ReportStatus
from .vox_science.authority import resolve_authorized_evidence
from .vox_science.baseline_snapshot import SnapshotValidationError, load_baseline_snapshot
from .vox_science.claim_evidence import load_claim_evidence
from .vox_science.verification import (
    verify_current_generation_anchor,
    verify_gate_hmac,
)


class HarnessEvidenceBundleNotFound(ValueError):
    """Levantado quando nao existe relatorio para a simulacao solicitada."""


SCIENCE_ARTIFACTS = {
    "methodology_manifest.json": "Manifesto metodologico e escopo da simulacao.",
    "baseline_registry.json": "Registro de bases publicas usadas como ancoragem.",
    "public_data_anchors.json": "Mapeamento das variaveis ancoradas em dados externos.",
    "prompt_registry.json": "Registro versionado de prompts, parafrases e ordem de itens.",
    "model_run_registry.json": "Registro de modelo, temperatura, seed e execucoes.",
    "synthetic_interviews_manifest.json": "Manifesto das entrevistas sinteticas executadas.",
    "fidelity_report.json": "Metricas de fidelidade, robustez e dispersao.",
    "pimmur_audit.json": "Auditoria Profile, Interaction, Memory, Minimal-Control, Unawareness e Realism.",
    "compost_audit.json": "Auditoria de contaminacao e desenho comparativo.",
    "claim_policy_audit.json": "Auditoria de forca de alegacao e linguagem de entrega.",
    "harness_science_gate.json": "Gate cientifico final do harness Vox.",
}

REQUIRED_SCIENCE_ARTIFACTS = (
    "methodology_manifest.json",
    "baseline_registry.json",
    "prompt_registry.json",
    "model_run_registry.json",
    "harness_science_gate.json",
)

CALIBRATION_MODES = {
    "unverified_no_calibration",
    "synthetic_trace_only",
    "materialized_external_baseline",
}


def build_harness_evidence_bundle(simulation_id: str, base_url: str) -> Dict[str, Any]:
    """Monta o bundle estavel que sistemas internos usam como evidencia MiroFish."""
    report = ReportManager.get_report_by_simulation(simulation_id)
    if not report:
        raise HarnessEvidenceBundleNotFound(
            f"Relatorio MiroFish nao encontrado para simulacao {simulation_id}"
        )

    artifacts = _safe_artifacts(report.report_id)
    artifact_names = [item["name"] for item in artifacts if item.get("name")]
    forecast_ledger = ReportManager.load_json_artifact(report.report_id, "forecast_ledger.json") or {}
    decision_packet = ReportManager.load_json_artifact(report.report_id, "decision_packet.json") or {}
    science_payloads = _load_science_payloads(report.report_id, artifact_names)
    verified_claim = _verified_vox_claim_projection_from_payloads(
        report.report_id, science_payloads
    )
    science_verified = verified_claim["verified"] is True

    return {
        "id": f"mirofish_bundle_{simulation_id}",
        "missionId": simulation_id,
        "title": _bundle_title(report),
        "source": "mirofish",
        "generatedAt": _now_iso(),
        "evidence": _build_evidence(report, artifacts, base_url, decision_packet),
        "graph": _build_graph(report, artifact_names, decision_packet),
        "forecasts": _build_forecasts(forecast_ledger),
        "methodology": _build_methodology(
            artifact_names, science_payloads, verified_claim
        ),
        "qualityGates": _build_quality_gates(science_payloads, science_verified),
        "limitations": _build_limitations(report, artifact_names, forecast_ledger),
    }


def _safe_artifacts(report_id: str) -> List[Dict[str, Any]]:
    try:
        return ReportManager.list_json_artifacts(report_id) or []
    except Exception:
        return []


def _load_science_payloads(report_id: str, artifact_names: Iterable[str]) -> Dict[str, Any]:
    available = set(artifact_names)
    payloads: Dict[str, Any] = {}
    for name in SCIENCE_ARTIFACTS:
        if name not in available:
            payloads[name] = None
            continue
        payloads[name] = ReportManager.load_json_artifact(report_id, name)
    return payloads


def verified_vox_claim_projection(
    report_id: str, artifact_names: Iterable[str] | None = None
) -> Dict[str, Any]:
    """Single server-verified claim projection; raw JSON is never authority."""

    if artifact_names is not None:
        names = list(artifact_names)
    else:
        names = [
            name
            for item in _safe_artifacts(report_id)
            if isinstance((name := item.get("name")), str) and name
        ]
    payloads = _load_science_payloads(report_id, names)
    return _verified_vox_claim_projection_from_payloads(report_id, payloads)


def _verified_vox_claim_projection_from_payloads(
    report_id: str, payloads: Dict[str, Any]
) -> Dict[str, Any]:
    """Project only fields validated against the current host anchor."""

    gate = payloads.get("harness_science_gate.json")
    if not _valid_science_generation(payloads, report_id) or not isinstance(gate, dict):
        return {
            "verified": False,
            "verification_status": "unverified",
            "passes_execution_gate": False,
            "claim_level": None,
            "calibrated": False,
            "calibration_mode": "unverified_no_calibration",
            "calibration_evidence": None,
            "new_human_collection": None,
            "prospective_validation": None,
            "max_external_language": None,
            "generation_id": None,
            "blockers": ["science_generation_authenticity_unverified"],
        }
    claim_level = gate.get("claim_level")
    passes_execution = gate.get("passes_execution_gate") is True
    calibrated = passes_execution and claim_level in {"C2", "C3", "C4"}
    calibration_mode = (
        "materialized_external_baseline"
        if calibrated
        else "synthetic_trace_only"
        if passes_execution and claim_level == "C1"
        else "unverified_no_calibration"
    )
    calibration_evidence = None
    if calibrated:
        calibration_evidence = {
            "baseline_snapshot_sha256": gate["baseline_snapshot_sha256"],
            "claim_evidence_sha256": gate["claim_evidence_sha256"],
            "authority_manifest_sha256": gate["authority_manifest_sha256"],
        }
    prospective_validation = None
    if claim_level == "C4":
        raw_prospective = gate.get("prospective_validation")
        if isinstance(raw_prospective, dict):
            prospective_validation = {
                "status": raw_prospective.get("status"),
                "heldout_count": raw_prospective.get("heldout_count"),
                "metrics": raw_prospective.get("metrics"),
                "per_id_scoring": raw_prospective.get("per_id_scoring"),
            }
    return {
        "verified": True,
        "verification_status": "verified",
        "passes_execution_gate": passes_execution,
        "claim_level": claim_level,
        "calibrated": calibrated,
        "calibration_mode": calibration_mode,
        "calibration_evidence": calibration_evidence,
        "new_human_collection": False,
        "prospective_validation": prospective_validation,
        "max_external_language": str(
            gate.get("max_external_language")
            or "simulacao sintetica exploratoria com rastreabilidade metodologica"
        ),
        "generation_id": gate.get("generation_id"),
        "blockers": [str(item) for item in gate.get("blockers", [])],
    }


def _bundle_title(report: Report) -> str:
    if report.outline and report.outline.title:
        return report.outline.title
    requirement = _compact_text(report.simulation_requirement, limit=90)
    if requirement:
        return requirement
    return f"Pacote de evidencias MiroFish {report.simulation_id}"


def _build_evidence(
    report: Report,
    artifacts: List[Dict[str, Any]],
    base_url: str,
    decision_packet: Dict[str, Any],
) -> List[Dict[str, Any]]:
    collected_at = _normalize_iso_datetime(report.completed_at or report.created_at)
    delivery_status = report.delivery_status()
    report_confidence = _report_confidence(report, decision_packet)
    primary_evidence = {
        "id": f"{report.report_id}:report",
        "title": f"Relatorio MiroFish {report.report_id}",
        "sourceUri": _absolute_api_url(base_url, f"/api/report/{report.report_id}"),
        "claim": _primary_claim(report),
        "confidence": report_confidence,
        "collectedAt": collected_at,
        "tags": ["mirofish", "report", delivery_status],
    }
    quote = _compact_text(report.markdown_content, limit=280)
    if quote:
        primary_evidence["quote"] = quote
    evidence = [primary_evidence]

    for artifact in artifacts:
        name = artifact.get("name")
        if not name:
            continue
        evidence.append(
            {
                "id": f"{report.report_id}:artifact:{name}",
                "title": f"Artefato MiroFish {name}",
                "sourceUri": _artifact_url(base_url, report.report_id, name),
                "claim": f"Artefato {name} gerado pelo harness MiroFish para auditoria da missao.",
                "confidence": round(max(0.55, report_confidence - 0.12), 4),
                "collectedAt": collected_at,
                "tags": ["mirofish", "artifact", _artifact_tag(name)],
            }
        )

    return evidence


def _build_graph(
    report: Report,
    artifact_names: Iterable[str],
    decision_packet: Dict[str, Any],
) -> Dict[str, Any]:
    report_confidence = _report_confidence(report, decision_packet)
    nodes = [
        {"id": report.simulation_id, "label": f"Simulacao {report.simulation_id}", "type": "simulation"},
        {"id": report.report_id, "label": f"Relatorio {report.report_id}", "type": "report"},
    ]
    edges = [
        {
            "source": report.simulation_id,
            "target": report.report_id,
            "relation": "generated_report",
            "weight": 1.0,
        }
    ]

    if report.graph_id:
        nodes.append({"id": report.graph_id, "label": f"Grafo {report.graph_id}", "type": "knowledge_graph"})
        edges.append(
            {
                "source": report.graph_id,
                "target": report.report_id,
                "relation": "supports",
                "weight": report_confidence,
            }
        )

    for name in artifact_names:
        artifact_id = f"{report.report_id}:{name}"
        nodes.append({"id": artifact_id, "label": name, "type": "artifact"})
        edges.append(
            {
                "source": report.report_id,
                "target": artifact_id,
                "relation": "contains_artifact",
                "weight": round(max(0.5, report_confidence - 0.2), 4),
            }
        )

    return {"nodes": nodes, "edges": edges}


def _build_forecasts(forecast_ledger: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_forecasts = forecast_ledger.get("forecasts") or forecast_ledger.get("previsoes") or []
    forecasts = []

    for item in raw_forecasts:
        if not isinstance(item, dict):
            continue
        forecast_text = (
            item.get("forecast")
            or item.get("previsao")
            or item.get("descricao")
            or item.get("titulo")
            or "Previsao MiroFish sem descricao textual"
        )
        assumptions = item.get("assumptions") or item.get("premissas") or item.get("premises") or []
        forecasts.append(
            {
                "horizon": str(item.get("horizon") or item.get("horizonte") or "sem horizonte declarado"),
                "forecast": _compact_text(str(forecast_text), limit=360),
                "probability": _coerce_probability(item.get("probability") or item.get("probabilidade")),
                "uncertainty": _coerce_uncertainty(item.get("uncertainty") or item.get("incerteza")),
                "assumptions": _string_list(assumptions),
            }
        )

    return forecasts


def _build_methodology(
    artifact_names: List[str],
    science_payloads: Dict[str, Any],
    verified_claim: Dict[str, Any],
) -> Dict[str, Any]:
    present = [name for name in SCIENCE_ARTIFACTS if name in artifact_names]
    missing = [name for name in SCIENCE_ARTIFACTS if name not in artifact_names]
    science_verified = verified_claim.get("verified") is True
    calibration_mode = str(
        verified_claim.get("calibration_mode") or "unverified_no_calibration"
    )
    if calibration_mode not in CALIBRATION_MODES:
        calibration_mode = "unverified_no_calibration"

    return {
        "contractVersion": "mirofish.vox_science.v1",
        "mode": "public_data_grounded_synthetic_harness",
        "verificationStatus": verified_claim.get("verification_status", "unverified"),
        "claimLevel": verified_claim.get("claim_level") if science_verified else None,
        "passesExecutionGate": verified_claim.get("passes_execution_gate") is True,
        "calibrationMode": calibration_mode,
        "calibrationEvidence": verified_claim.get("calibration_evidence"),
        "authority": {
            "status": "server_verified" if science_verified else "diagnostic_only",
            "verified": science_verified,
            "claimLevel": verified_claim.get("claim_level") if science_verified else None,
            "passesExecutionGate": verified_claim.get("passes_execution_gate") is True,
        },
        "newHumanCollection": verified_claim.get("new_human_collection"),
        "readiness": _science_readiness(science_payloads, present, science_verified),
        "availableArtifacts": present,
        "recommendedMissingArtifacts": missing,
        "population": None,
        "publicDataAnchors": [],
        "robustness": None,
    }


def _build_quality_gates(
    science_payloads: Dict[str, Any], science_verified: bool
) -> List[Dict[str, Any]]:
    gates = []
    for name in (
        "harness_science_gate.json",
        "fidelity_report.json",
        "pimmur_audit.json",
        "compost_audit.json",
        "claim_policy_audit.json",
    ):
        payload = science_payloads.get(name)
        if not science_verified:
            status = "review"
        elif name == "harness_science_gate.json":
            status = (
                "passed"
                if isinstance(payload, dict)
                and payload.get("passes_execution_gate") is True
                else "blocked"
            )
        else:
            status = _gate_status(payload)
        gates.append(
            {
                "id": _artifact_tag(name),
                "artifact": name,
                "status": status,
                "authority": "server_verified" if science_verified else "diagnostic_only",
                "description": SCIENCE_ARTIFACTS[name],
            }
        )
    return gates


def _science_readiness(
    science_payloads: Dict[str, Any], present: List[str], science_verified: bool
) -> str:
    science_gate = science_payloads.get("harness_science_gate.json")
    if science_verified:
        return (
            "passed"
            if isinstance(science_gate, dict)
            and science_gate.get("passes_execution_gate") is True
            else "blocked"
        )
    if isinstance(science_gate, dict):
        return "blocked"
    if all(name in present for name in REQUIRED_SCIENCE_ARTIFACTS):
        return "ready_for_science_gate"
    if present:
        return "partial"
    return "legacy"


def _valid_science_generation(
    science_payloads: Dict[str, Any], report_id: str | None = None
) -> bool:
    """Verify host authenticity, currentness, bindings and materialized authority."""

    gate = science_payloads.get("harness_science_gate.json")
    if not isinstance(gate, dict):
        return False
    if (
        gate.get("schema") != "mirofish.vox.harness_science_gate.v2"
        or not isinstance(gate.get("passes_execution_gate"), bool)
        or gate.get("new_human_collection") is not False
        or not isinstance(gate.get("generation_id"), str)
        or not gate.get("generation_id")
        or not isinstance(gate.get("artifact_hashes"), dict)
    ):
        return False
    expected_report_id = report_id or gate.get("report_id")
    if (
        not isinstance(expected_report_id, str)
        or not expected_report_id
        or gate.get("report_id") != expected_report_id
        or not verify_gate_hmac(gate)
        or not verify_current_generation_anchor(expected_report_id, gate)
    ):
        return False
    generation_id = gate["generation_id"]
    hashes = gate["artifact_hashes"]
    expected_names = set(SCIENCE_ARTIFACTS) - {"harness_science_gate.json"}
    if set(hashes) != expected_names:
        return False
    for name in expected_names:
        payload = science_payloads.get(name)
        expected_hash = hashes.get(name)
        if (
            not isinstance(payload, dict)
            or payload.get("generation_id") != generation_id
            or not isinstance(expected_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
        ):
            return False
        try:
            canonical = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError):
            return False
        if hashlib.sha256(canonical).hexdigest() != expected_hash:
            return False
    fidelity = science_payloads.get("fidelity_report.json")
    claim_policy = science_payloads.get("claim_policy_audit.json")
    methodology = science_payloads.get("methodology_manifest.json")
    model = science_payloads.get("model_run_registry.json")
    if (
        not isinstance(fidelity, dict)
        or not isinstance(claim_policy, dict)
        or not isinstance(methodology, dict)
        or not isinstance(model, dict)
    ):
        return False
    if (
        gate.get("simulation_id") != model.get("simulation_id")
        or gate.get("report_id") != model.get("report_id")
        or gate.get("run_id") != model.get("run_id")
        or gate.get("config_sha256") != model.get("config_sha256")
        or gate.get("input_sha256") != model.get("prompt_registry_hash")
        or methodology.get("report_id") != gate.get("report_id")
        or methodology.get("simulation_id") != gate.get("simulation_id")
    ):
        return False
    passes_execution = gate.get("passes_execution_gate") is True
    if fidelity.get("passes_execution_gate") is not passes_execution:
        return False
    eligibility = fidelity.get("claim_eligibility")
    if not isinstance(eligibility, dict):
        return False
    policy_blockers = claim_policy.get("blocked_claims")
    passes_policy = claim_policy.get("passes_claim_policy")
    if (
        not isinstance(policy_blockers, list)
        or not isinstance(passes_policy, bool)
        or claim_policy.get("passes_gate") is not passes_policy
        or passes_policy is bool(policy_blockers)
    ):
        return False
    fidelity_ceiling = next(
        (level for level in ("C4", "C3", "C2") if eligibility.get(level) is True),
        "C1",
    )
    expected_claim = (
        "C0"
        if not passes_execution
        else "C1"
        if not passes_policy
        else fidelity_ceiling
    )
    if (
        gate.get("claim_level") != expected_claim
        or claim_policy.get("claim_level") != expected_claim
        or methodology.get("claim_target") != expected_claim
        or gate.get("max_external_language") != _claim_language(expected_claim)
        or claim_policy.get("allowed_language") != [_claim_language(expected_claim)]
    ):
        return False
    if expected_claim in {"C2", "C3", "C4"}:
        binding = fidelity.get("evidence_binding")
        calibration = fidelity.get("calibration_evidence")
        if (
            not isinstance(binding, dict)
            or not isinstance(calibration, dict)
            or calibration.get("status") != "measured"
            or any(
                not isinstance(binding.get(key), str)
                or not re.fullmatch(r"[0-9a-f]{64}", binding[key])
                for key in (
                    "baseline_snapshot_sha256",
                    "sample_sha256",
                    "claim_evidence_sha256",
                    "authority_manifest_sha256",
                )
            )
        ):
            return False
        if expected_claim == "C4":
            prospective = fidelity.get("prospective_evidence")
            if (
                gate.get("prospective_validation") != prospective
                or not isinstance(prospective, dict)
                or prospective.get("status") != "measured"
                or not isinstance(prospective.get("per_id_scoring"), dict)
                or prospective["per_id_scoring"].get("algorithm")
                != "multiclass_brier_log_loss_per_id.v1"
                or prospective["per_id_scoring"].get("passes_thresholds") is not True
            ):
                return False
        required_top_level = {
            "baseline_snapshot_sha256",
            "claim_evidence_sha256",
            "authority_manifest_sha256",
        }
        if any(gate.get(name) != binding.get(name) for name in required_top_level):
            return False
        if (
            gate.get("baseline_snapshot_path") != binding.get("baseline_snapshot_path")
            or gate.get("claim_evidence_path") != binding.get("claim_evidence_path")
        ):
            return False
        try:
            authority = resolve_authorized_evidence(
                baseline_path=str(gate["baseline_snapshot_path"]),
                claim_evidence_path=str(gate["claim_evidence_path"]),
            )
            if (
                authority.baseline_sha256 != gate["baseline_snapshot_sha256"]
                or authority.claim_evidence_sha256 != gate["claim_evidence_sha256"]
                or authority.authority_manifest_sha256 != gate["authority_manifest_sha256"]
            ):
                return False
            snapshot_summary = calibration.get("snapshot")
            if not isinstance(snapshot_summary, dict):
                return False
            snapshot = load_baseline_snapshot(
                relative_path=authority.baseline_path,
                trusted_root=authority.trusted_root,
                expected_sha256=authority.baseline_sha256,
                target_variable=snapshot_summary.get("variable_id"),
            )
            evidence = load_claim_evidence(
                relative_path=authority.claim_evidence_path,
                trusted_root=authority.trusted_root,
                expected_sha256=authority.claim_evidence_sha256,
                authority_manifest_sha256=authority.authority_manifest_sha256,
                baseline_snapshot=snapshot,
                expected_report_id=expected_report_id,
                expected_simulation_id=str(gate["simulation_id"]),
                expected_run_id=str(gate["run_id"]),
                expected_config_sha256=str(gate["config_sha256"]),
                expected_input_sha256=str(gate["input_sha256"]),
                authorized_stability_runs=authority.stability_runs,
                authorized_preregistered_forecasts=authority.preregistered_forecasts,
            )
            if evidence.sha256 != gate["claim_evidence_sha256"]:
                return False
        except (KeyError, SnapshotValidationError, TypeError, ValueError):
            return False
    return True


def _claim_language(level: str) -> str:
    return {
        "C0": "mapa qualitativo de sinais e friccoes sinteticas",
        "C1": "simulacao sintetica exploratoria com rastreabilidade metodologica",
        "C2": "simulacao sintetica calibrada por dados publicos e robustez auditada",
        "C3": "estimativa sintetica calibrada por baseline publico comparavel",
        "C4": "previsao operacional monitoravel com cenario base e tese adversaria",
    }.get(level, "simulacao sintetica exploratoria com rastreabilidade metodologica")


def _artifact_gate_passes(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return bool(
        payload.get("passes_gate") is True
        or payload.get("passes") is True
        or payload.get("bundle_verified") is True
        or payload.get("status") == "passed"
    )


def _gate_status(payload: Any) -> str:
    if payload is None:
        return "missing"
    if _artifact_gate_passes(payload):
        return "passed"
    return "review"


def _public_data_anchor_names(payload: Any) -> List[str]:
    if not isinstance(payload, dict):
        return []
    anchors = payload.get("anchors") or payload.get("baselines") or payload.get("sources") or []
    names = []
    for item in anchors:
        if isinstance(item, dict):
            name = item.get("name") or item.get("source") or item.get("dataset")
            if name:
                names.append(str(name))
        elif str(item).strip():
            names.append(str(item).strip())
    return names


def _robustness_summary(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {
        key: payload[key]
        for key in (
            "overall_score",
            "seed_dispersion",
            "paraphrase_dispersion",
            "variance_ratio",
            "subgroup_max_error_pp",
            "passes_gate",
        )
        if key in payload
    }


def _first_present(*values: Any) -> Optional[Any]:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _build_limitations(report: Report, artifact_names: List[str], forecast_ledger: Dict[str, Any]) -> List[str]:
    limitations = [
        f"delivery_status={report.delivery_status()}; publishable={str(report.is_publishable()).lower()}",
    ]

    if report.status != ReportStatus.COMPLETED:
        limitations.append(f"Relatorio ainda nao concluido: status={report.status.value}")
    if not report.is_publishable():
        limitations.append("Consumidores devem tratar o bundle como diagnostico ou apoio interno, nao entrega final.")
    if "forecast_ledger.json" not in artifact_names and not forecast_ledger:
        limitations.append("Forecast ledger nao encontrado; previsoes estruturadas podem estar ausentes.")
    if not artifact_names:
        limitations.append("Nenhum artefato JSON adicional foi encontrado para auditoria expandida.")

    return limitations


def _primary_claim(report: Report) -> str:
    if report.markdown_content:
        return _compact_text(report.markdown_content, limit=320)
    if report.simulation_requirement:
        return _compact_text(report.simulation_requirement, limit=320)
    return "Relatorio MiroFish disponivel para a simulacao solicitada."


def _report_confidence(report: Report, decision_packet: Optional[Dict[str, Any]] = None) -> float:
    if isinstance(decision_packet, dict):
        try:
            conviction_raw = decision_packet.get("conviction_operational")
            if conviction_raw is None:
                raise ValueError("conviction_missing")
            conviction = float(conviction_raw)
            if 0 <= conviction <= 1:
                return round(conviction, 4)
        except (TypeError, ValueError):
            pass
    if report.is_publishable():
        return 0.9
    if report.status == ReportStatus.COMPLETED:
        return 0.76
    return 0.55


def _artifact_url(base_url: str, report_id: str, name: str) -> str:
    path = f"/api/report/{report_id}/artifacts/{quote(name, safe='')}"
    return _absolute_api_url(base_url, path)


def _absolute_api_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def _compact_text(value: Optional[str], limit: int) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    text = re.sub(r"^#+\s*", "", text).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _coerce_probability(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip().replace("%", "")
        try:
            number = float(text)
        except ValueError:
            return None
    if number > 1:
        number = number / 100
    return max(0.0, min(1.0, number))


def _coerce_uncertainty(value: Any) -> float:
    labels = {
        "baixa": 0.25,
        "baixo": 0.25,
        "low": 0.25,
        "media": 0.5,
        "medio": 0.5,
        "média": 0.5,
        "médio": 0.5,
        "medium": 0.5,
        "alta": 0.75,
        "alto": 0.75,
        "high": 0.75,
        "indefinida": 0.6,
        "unknown": 0.6,
    }
    if value is None or value == "":
        return 0.6
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in labels:
            return labels[normalized]
    probability = _coerce_probability(value)
    return 0.6 if probability is None else probability


def _string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _artifact_tag(name: str) -> str:
    return name.replace(".json", "").replace("_", "-")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _normalize_iso_datetime(value: Optional[str]) -> str:
    text = (value or "").strip()
    if not text:
        return _now_iso()
    if text.endswith("Z"):
        return text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return _now_iso()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
