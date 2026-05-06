"""AutoResearch target: report delivery intelligence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .base import Asset, Constraints, Evaluator


class ReportDeliveryConstraints(Constraints):
    """Invariantes para evoluir a fronteira de entrega de relatorios."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def to_prompt(self) -> str:
        return (
            "Otimize a inteligencia de entrega de relatorios do Mirofish sem automatizar entrega ao cliente.\n\n"
            "INVARIANTES:\n"
            "1. Report publishable, bundle verified e client deliverable continuam estados separados.\n"
            "2. Nenhuma API publica pode expor internal_path.\n"
            "3. Downloads devem usar allowlist de manifest e bloquear path traversal.\n"
            "4. Export HTML deve usar renderer seguro com metadata.\n"
            "5. AutoResearch recomenda melhorias; nao aplica patch de producao automaticamente.\n"
        )

    def validate(self, asset_path: Path) -> bool:
        required = [
            self.project_root / "backend" / "app" / "services" / "decision_readiness.py",
            self.project_root / "backend" / "app" / "services" / "report_delivery_packet.py",
            self.project_root / "backend" / "app" / "services" / "report_method_checklist.py",
            self.project_root / "backend" / "app" / "services" / "report_exporter.py",
            self.project_root / "backend" / "app" / "services" / "report_bundle_verifier.py",
        ]
        return all(path.exists() for path in required)


class ReportDeliveryAsset(Asset):
    """Asset read-only que resume os pontos de decisao de entrega."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._path = project_root / "backend" / "app" / "services" / "report_delivery_packet.py"

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        files = [
            "backend/app/services/decision_readiness.py",
            "backend/app/services/report_delivery_packet.py",
            "backend/app/services/report_method_checklist.py",
            "backend/app/services/report_exporter.py",
            "backend/app/services/report_bundle_verifier.py",
            "backend/app/api/report.py",
        ]
        parts = []
        for rel_path in files:
            path = self.project_root / rel_path
            if path.exists():
                parts.append(f"## {rel_path}\n{path.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)

    def write(self, content: str) -> None:
        raise RuntimeError("ReportDeliveryAsset is read-only; AutoResearch must propose patches, not apply them.")

    def editable_sections(self) -> Dict[str, str]:
        content = self.read()
        return {"report_delivery_contract": content[:6000]}


class ReportDeliveryEvaluator(Evaluator):
    """Score deterministico da fronteira de entrega cliente."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.last_report: dict[str, Any] = {}

    @property
    def requires_llm(self) -> bool:
        return False

    def metric_name(self) -> str:
        return "Report delivery readiness score"

    def measure(self, asset: Asset) -> float:
        checks = self.detailed_report(asset)["checks"]
        passed = sum(1 for item in checks if item["passes"])
        return round(passed / max(len(checks), 1), 4)

    def detailed_report(self, asset: Asset) -> dict[str, Any]:
        content = asset.read()
        checks = [
            self._check("decision_readiness_service", "evaluate_decision_readiness" in content),
            self._check("delivery_packet_service", "build_report_delivery_packet" in content),
            self._check("method_checklist_gate", "evaluate_report_method_checklist" in content),
            self._check("safe_export_renderer", "render_safe_markdown" in content),
            self._check("bundle_hash_verifier", "hashes_match" in content and "sha256" in content),
            self._check("path_safety", "ReportExportInvalidPath" in content and "allowed_export_file_path" in content),
            self._check("no_public_internal_path", "_public_export_manifest" in content and "internal_path" in content),
            self._check("repair_conflict_409", "ReportFinalizationConflict" in content and "), 409" in content),
            self._check("export_conflict_409", "ReportExportConflict" in content and "), 409" in content),
            self._check("client_deliverable_separated", "client_deliverable = report_publishable and bundle_verified and method_checks_pass" in content),
        ]
        recommendations = [
            item["recommendation"] for item in checks if not item["passes"] and item.get("recommendation")
        ]
        report = {
            "target": "report_delivery",
            "score": round(sum(1 for item in checks if item["passes"]) / max(len(checks), 1), 4),
            "requires_llm": False,
            "applies_patch": False,
            "checks": checks,
            "recommendations": recommendations,
        }
        self.last_report = report
        return report

    def _check(self, check_id: str, passes: bool) -> dict[str, Any]:
        recommendations = {
            "decision_readiness_service": "Adicionar readiness antes da geracao do relatorio.",
            "delivery_packet_service": "Centralizar estado de entrega em delivery packet.",
            "method_checklist_gate": "Bloquear entrega quando hard checks metodologicos falham.",
            "safe_export_renderer": "Usar renderer seguro com metadata para HTML.",
            "bundle_hash_verifier": "Verificar hashes do bundle antes de cliente.",
            "path_safety": "Bloquear download fora do allowlist do manifest.",
            "no_public_internal_path": "Remover internal_path de respostas publicas.",
            "repair_conflict_409": "Retornar 409 para reparo durante geracao.",
            "export_conflict_409": "Retornar 409 para export bloqueado.",
            "client_deliverable_separated": "Manter publishable, bundle_verified e client_deliverable separados.",
        }
        return {
            "id": check_id,
            "passes": passes,
            "recommendation": "" if passes else recommendations.get(check_id, "Revisar contrato."),
        }
