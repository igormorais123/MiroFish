from pathlib import Path

from backend.autoresearch.targets.ralph_method import (
    RalphMethodAsset,
    RalphMethodConstraints,
    RalphMethodEvaluator,
)
from backend.autoresearch.targets.report_delivery import (
    ReportDeliveryAsset,
    ReportDeliveryConstraints,
    ReportDeliveryEvaluator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_report_delivery_target_scores_current_contract_without_llm():
    asset = ReportDeliveryAsset(PROJECT_ROOT)
    evaluator = ReportDeliveryEvaluator(PROJECT_ROOT)

    report = evaluator.detailed_report(asset)

    assert evaluator.requires_llm is False
    assert report["applies_patch"] is False
    assert report["score"] >= 0.8
    assert {item["id"] for item in report["checks"]} >= {
        "method_checklist_gate",
        "safe_export_renderer",
        "bundle_hash_verifier",
        "path_safety",
    }


def test_report_delivery_constraints_validate_required_services():
    constraints = ReportDeliveryConstraints(PROJECT_ROOT)

    assert constraints.validate(PROJECT_ROOT / "backend" / "app" / "services" / "report_delivery_packet.py") is True


def test_ralph_method_target_scores_swarm_contract_without_llm():
    asset = RalphMethodAsset(PROJECT_ROOT)
    evaluator = RalphMethodEvaluator(PROJECT_ROOT)

    report = evaluator.detailed_report(asset)

    assert evaluator.requires_llm is False
    assert report["applies_patch"] is False
    assert report["score"] >= 0.75
    assert {item["id"] for item in report["checks"]} >= {
        "autoresearch_metrics_required",
        "method_signal_schema",
        "swarm_lanes_defined",
        "external_systems_optional",
    }


def test_ralph_method_constraints_validate_required_files():
    constraints = RalphMethodConstraints(PROJECT_ROOT)

    assert constraints.validate(PROJECT_ROOT / ".ralph" / "SWARM.md") is True
