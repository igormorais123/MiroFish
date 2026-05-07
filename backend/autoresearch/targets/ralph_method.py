"""AutoResearch target: Ralph loop method quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .base import Asset, Constraints, Evaluator


class RalphMethodConstraints(Constraints):
    """Invariantes do metodo Ralph aplicado ao Mirofish."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def to_prompt(self) -> str:
        return (
            "Otimize o metodo RalphLoop do Mirofish como melhoria operacional, nao como mudanca de produto.\n\n"
            "INVARIANTES:\n"
            "1. Uma unidade pequena por run.\n"
            "2. Verificacao real antes de done.\n"
            "3. METRICS.json sempre inclui autoresearch.\n"
            "4. AutoResearch recomenda patch, mas nao aplica automaticamente.\n"
            "5. OpenSwarm/Helena/Vox entram como aprendizado, nao runtime obrigatorio.\n"
        )

    def validate(self, asset_path: Path) -> bool:
        ralph_dir = self.project_root / ".ralph"
        return all((ralph_dir / name).exists() for name in [
            "RALPH.md",
            "LOOP.md",
            "VERIFY.md",
            "AUTORESEARCH.md",
            "METRICS.schema.json",
            "SWARM.md",
        ])


class RalphMethodAsset(Asset):
    """Asset read-only que agrega os arquivos de metodo Ralph."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ralph_dir = project_root / ".ralph"
        self._path = self.ralph_dir / "SWARM.md"

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        files = ["RALPH.md", "LOOP.md", "VERIFY.md", "AUTORESEARCH.md", "METRICS.schema.json", "SWARM.md"]
        parts = []
        for filename in files:
            path = self.ralph_dir / filename
            if path.exists():
                parts.append(f"## .ralph/{filename}\n{path.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)

    def write(self, content: str) -> None:
        raise RuntimeError("RalphMethodAsset is read-only; AutoResearch must propose patches, not apply them.")

    def editable_sections(self) -> Dict[str, str]:
        return {"ralph_method_contract": self.read()[:6000]}


class RalphMethodEvaluator(Evaluator):
    """Score deterministico da disciplina Ralph + Swarm + AutoResearch."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.last_report: dict[str, Any] = {}

    @property
    def requires_llm(self) -> bool:
        return False

    def metric_name(self) -> str:
        return "Ralph method readiness score"

    def measure(self, asset: Asset) -> float:
        report = self.detailed_report(asset)
        return report["score"]

    def detailed_report(self, asset: Asset) -> dict[str, Any]:
        content = asset.read()
        schema = self._load_metrics_schema()
        checks = [
            self._check("one_unit_per_run", "Exactly one unit" in content or "uma unidade" in content.lower()),
            self._check("verification_before_done", "verify" in content.lower() and "passed" in content.lower()),
            self._check("autoresearch_metrics_required", "autoresearch" in schema.get("required", [])),
            self._check("method_signal_schema", "method_signal" in json.dumps(schema, ensure_ascii=False)),
            self._check("no_auto_patch_contract", "Do not apply" in content or "não aplica" in content.lower() or "nao aplica" in content.lower()),
            self._check("swarm_lanes_defined", all(token in content for token in [
                "research_intake",
                "method_mapper",
                "evaluator_designer",
                "patch_writer",
                "red_team",
            ])),
            self._check("external_systems_optional", "OpenSwarm" in content and "Helena" in content and "Vox" in content),
            self._check("github_branch_pr_contract", "branch" in content.lower() and "PR" in content),
        ]
        recommendations = [item["recommendation"] for item in checks if not item["passes"]]
        report = {
            "target": "ralph_method",
            "score": round(sum(1 for item in checks if item["passes"]) / max(len(checks), 1), 4),
            "requires_llm": False,
            "applies_patch": False,
            "checks": checks,
            "recommendations": recommendations,
        }
        self.last_report = report
        return report

    def _load_metrics_schema(self) -> dict[str, Any]:
        path = self.project_root / ".ralph" / "METRICS.schema.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _check(self, check_id: str, passes: bool) -> dict[str, Any]:
        recommendations = {
            "one_unit_per_run": "Reforcar limite de uma unidade por run.",
            "verification_before_done": "Exigir evidencia de verificacao antes de done.",
            "autoresearch_metrics_required": "Tornar autoresearch obrigatorio no METRICS.schema.json.",
            "method_signal_schema": "Registrar method_signal para evolucao de metodo.",
            "no_auto_patch_contract": "Declarar que AutoResearch recomenda, mas nao aplica patch automaticamente.",
            "swarm_lanes_defined": "Definir lanes especialistas leves em .ralph/SWARM.md.",
            "external_systems_optional": "Documentar OpenSwarm/Helena/Vox como aprendizado opcional, nao runtime.",
            "github_branch_pr_contract": "Reforcar trabalho em branch e PR, com GitHub como fonte de verdade.",
        }
        return {
            "id": check_id,
            "passes": passes,
            "recommendation": "" if passes else recommendations[check_id],
        }
