"""Validates the JEV Hermes skills shipped in hermes/skills/jev."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

SKILLS_ROOT = Path(__file__).resolve().parents[2] / "hermes" / "skills" / "jev"
EXPECTED = (
    "jev-evals",
    "jev-orquestracao-equipe",
    "jev-orquestracao-modelos",
    "jev-triagem",
    "jev-benchmark",
    "jev-loop-observa-decide-age",
)


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"missing frontmatter in {path}"
    fields = {}
    for line in match.group(1).splitlines():
        if re.match(r"^[a-z_]+: ", line):
            key, value = line.split(": ", 1)
            fields[key] = value
    return fields


def _load(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("skill", EXPECTED)
def test_skill_frontmatter(skill):
    fields = _frontmatter(SKILLS_ROOT / skill / "SKILL.md")
    assert fields["name"] == skill
    assert 0 < len(fields["description"]) <= 1024
    assert re.match(r"^\d+\.\d+\.\d+$", fields["version"])


def test_skill_dirs_stay_out_of_persona_catalog():
    for skill in EXPECTED:
        assert "agent" not in skill


def test_pre_gate_decisions():
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    base = {"changed_files": ["backend/app/x.py"], "tests_exit_code": 0, "build_exit_code": 0}
    assert gate.decide(base)["decision"] == "EVALUATE"
    assert gate.decide({**base, "tests_exit_code": 1})["decision"] == "RETRY"
    assert gate.decide({**base, "tests_exit_code": 1, "attempt": 3})["decision"] == "HUMAN"
    assert gate.decide({**base, "changed_files": ["Dockerfile"]})["decision"] == "HUMAN"
    assert gate.decide({**base, "changed_files": [".env"]})["decision"] == "RETRY"
    assert gate.decide({"changed_files": ["a.py"]})["decision"] == "HUMAN"


@pytest.mark.parametrize("path", [".env", ".env.local", ".env.production", "foo/.env.test", "backend/.env"])
def test_pre_gate_blocks_secret_env_variants(path):
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    evidence = {"changed_files": [path], "tests_exit_code": 0, "build_exit_code": 0}
    assert gate.decide(evidence)["decision"] == "RETRY"


@pytest.mark.parametrize("path", [".env.example", ".env.example.omniroute", "deploy/.env.sample", ".envrc.md"])
def test_pre_gate_allows_env_templates(path):
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    assert not gate._is_secret_env(path)


def test_benchmark_aggregate(tmp_path):
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    rows = [
        {"task_id": "t1", "arch": "A", "success": True, "cost_usd": 0.02, "latency_s": 10, "retries": 0, "human_interventions": 0},
        {"task_id": "t2", "arch": "A", "success": False, "cost_usd": 0.02, "latency_s": 30, "retries": 2, "human_interventions": 1},
        {"task_id": "t1", "arch": "B+JEV", "success": True, "cost_usd": 0.03, "latency_s": 12, "retries": 1, "human_interventions": 0},
        {"task_id": "t2", "arch": "B+JEV", "success": True, "cost_usd": 0.03, "latency_s": 14, "retries": 0, "human_interventions": 0},
    ]
    results = tmp_path / "results.jsonl"
    results.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    summary = agg.summarize(agg.load(str(results)))
    assert summary["A"]["success_rate"] == 0.5
    assert summary["B+JEV"]["success_rate"] == 1.0
    assert summary["A"]["cost_per_success_usd"] == pytest.approx(0.04)
    assert summary["A"]["tasks"] == 2
    assert summary["A"]["diff_vs_baseline_ci95"] is None
    assert summary["B+JEV"]["diff_vs_baseline_ci95"] is not None
    assert "B+JEV" in agg.render(summary)


def test_benchmark_bootstrap_resamples_tasks_not_runs():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    # Two tasks, one always solved and one never; many repetitions must not
    # shrink the interval as if each run were independent.
    rows = [
        {"task_id": task, "arch": "A", "success": task == "easy", "rep": rep}
        for task in ("easy", "hard")
        for rep in range(50)
    ]
    low, high = agg.summarize(rows)["A"]["success_ci95"]
    assert low == 0.0 and high == 1.0
