"""Contrato de evidencias do harness MiroFish para consumidores internos."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote, urljoin

from .report_agent import Report, ReportManager, ReportStatus


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

    return {
        "id": f"mirofish_bundle_{simulation_id}",
        "missionId": simulation_id,
        "title": _bundle_title(report),
        "source": "mirofish",
        "generatedAt": _now_iso(),
        "evidence": _build_evidence(report, artifacts, base_url, decision_packet),
        "graph": _build_graph(report, artifact_names, decision_packet),
        "forecasts": _build_forecasts(forecast_ledger),
        "methodology": _build_methodology(artifact_names, science_payloads),
        "qualityGates": _build_quality_gates(science_payloads),
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
) -> Dict[str, Any]:
    present = [name for name in SCIENCE_ARTIFACTS if name in artifact_names]
    missing = [name for name in SCIENCE_ARTIFACTS if name not in artifact_names]
    methodology_manifest = science_payloads.get("methodology_manifest.json") or {}
    baseline_registry = science_payloads.get("baseline_registry.json") or {}
    fidelity_report = science_payloads.get("fidelity_report.json") or {}

    return {
        "contractVersion": "mirofish.vox_science.v1",
        "mode": "public_data_grounded_synthetic_harness",
        "calibrationMode": "public_data_and_existing_assets",
        "newHumanCollection": False,
        "readiness": _science_readiness(science_payloads, present),
        "availableArtifacts": present,
        "recommendedMissingArtifacts": missing,
        "population": _first_present(
            methodology_manifest.get("population"),
            methodology_manifest.get("target_population"),
            baseline_registry.get("population"),
        ),
        "publicDataAnchors": _public_data_anchor_names(baseline_registry),
        "robustness": _robustness_summary(fidelity_report),
    }


def _build_quality_gates(science_payloads: Dict[str, Any]) -> List[Dict[str, Any]]:
    gates = []
    for name in (
        "harness_science_gate.json",
        "fidelity_report.json",
        "pimmur_audit.json",
        "compost_audit.json",
        "claim_policy_audit.json",
    ):
        payload = science_payloads.get(name)
        gates.append(
            {
                "id": _artifact_tag(name),
                "artifact": name,
                "status": _gate_status(payload),
                "description": SCIENCE_ARTIFACTS[name],
            }
        )
    return gates


def _science_readiness(science_payloads: Dict[str, Any], present: List[str]) -> str:
    science_gate = science_payloads.get("harness_science_gate.json")
    if _artifact_gate_passes(science_gate):
        return "passed"
    if all(name in present for name in REQUIRED_SCIENCE_ARTIFACTS):
        return "ready_for_science_gate"
    if present:
        return "partial"
    return "legacy"


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
            conviction = float(decision_packet.get("conviction_operational"))
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
