"""Validates the JEV Hermes skills shipped in hermes/skills/jev."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
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


def _row(task, arch, success=True, rep=1, **metrics):
    base = {"task_id": task, "arch": arch, "rep": rep, "success": success,
            "cost_usd": 0.01, "latency_s": 1.0, "retries": 0, "human_interventions": 0}
    base.update(metrics)
    return base


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
    mixed = {**base, "changed_files": [".env.local", "deploy/nginx/site.conf"]}
    assert gate.decide(mixed)["decision"] == "HUMAN"


@pytest.mark.parametrize("path", [".env", ".env.local", ".env.production", "foo/.env.test", "backend/.env"])
def test_pre_gate_blocks_secret_env_variants(path):
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    evidence = {"changed_files": [path], "tests_exit_code": 0, "build_exit_code": 0}
    assert gate.decide(evidence)["decision"] == "RETRY"


@pytest.mark.parametrize(
    "path",
    [
        "node_modules/x/index.js",
        "frontend/node_modules/x/index.js",
        "dist/app.js",
        "frontend/dist/index.html",
        "backend/uploads/projects/a.json",
        ".vercel/project.json",
        "frontend/.vercel/project.json",
        "logs/app.log",
    ],
)
def test_pre_gate_blocks_agents_md_never_commit_list(path):
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    evidence = {"changed_files": [path], "tests_exit_code": 0, "build_exit_code": 0}
    assert gate.decide(evidence)["decision"] == "RETRY"


@pytest.mark.parametrize("path", [".env.example", ".env.example.omniroute", "deploy/.env.sample", ".envrc.md"])
def test_pre_gate_allows_env_templates(path):
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    assert not gate._is_secret_env(path)


@pytest.mark.parametrize(
    "evidence",
    [
        {"changed_files": ".env", "tests_exit_code": 0},
        {"changed_files": "Dockerfile", "tests_exit_code": 0},
        {"changed_files": [".env", 3], "tests_exit_code": 0},
        {"changed_files": ["a.py"], "tests_exit_code": "0"},
        {"changed_files": ["a.py"], "tests_exit_code": 0, "attempt": "2"},
        {"changed_files": ["a.py"], "tests_exit_code": 0, "max_attempts": 0},
        ["a.py"],
    ],
)
def test_pre_gate_malformed_evidence_goes_to_human(evidence):
    gate = _load(SKILLS_ROOT / "jev-evals" / "scripts" / "pre_gate.py")
    result = gate.decide(evidence)
    assert result["decision"] == "HUMAN"
    assert result["reason"].startswith("invalid evidence")


INSTALLER = SKILLS_ROOT.parents[1] / "install_jev_skills.sh"


@pytest.mark.parametrize("args", [["--help"], ["-h"], ["--dryrun"], ["--dry-run", "extra"]])
def test_installer_never_installs_on_unknown_or_help_args(tmp_path, args):
    env = {**os.environ, "HERMES_HOME": str(tmp_path)}
    result = subprocess.run(["bash", str(INSTALLER), *args], env=env, capture_output=True, text=True)
    assert not (tmp_path / "skills").exists()
    assert result.returncode == (0 if args[0] in ("--help", "-h") else 2)


def test_installer_dry_run_and_install(tmp_path):
    env = {**os.environ, "HERMES_HOME": str(tmp_path)}
    dry = subprocess.run(["bash", str(INSTALLER), "--dry-run"], env=env, capture_output=True, text=True)
    assert dry.returncode == 0 and not (tmp_path / "skills").exists()
    real = subprocess.run(["bash", str(INSTALLER)], env=env, capture_output=True, text=True)
    assert real.returncode == 0
    assert len(list((tmp_path / "skills" / "jev").glob("*/SKILL.md"))) == len(EXPECTED)


def test_benchmark_aggregate(tmp_path):
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    rows = [
        _row("t1", "A", True, cost_usd=0.02, latency_s=10),
        _row("t2", "A", False, cost_usd=0.02, latency_s=30, retries=2, human_interventions=1),
        _row("t1", "B+JEV", True, cost_usd=0.03, latency_s=12, retries=1),
        _row("t2", "B+JEV", True, cost_usd=0.03, latency_s=14),
    ]
    results = tmp_path / "results.jsonl"
    results.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    summary = agg.summarize(agg.load(str(results)))
    assert summary["A"]["success_rate"] == 0.5
    assert summary["B+JEV"]["success_rate"] == 1.0
    assert summary["A"]["cost_per_success_usd"] == pytest.approx(0.04)
    assert summary["A"]["tasks"] == 2
    assert summary["A"]["human_interventions"] == 1
    assert summary["A"]["diff_vs_baseline_ci95"] is None
    assert summary["B+JEV"]["diff_vs_baseline_ci95"] is not None
    assert "B+JEV" in agg.render(summary)


def test_benchmark_bootstrap_resamples_tasks_not_runs():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    # Two tasks, one always solved and one never; many repetitions must not
    # shrink the interval as if each run were independent.
    rows = [_row(task, "A", task == "easy", rep=rep) for task in ("easy", "hard") for rep in range(50)]
    low, high = agg.summarize(rows)["A"]["success_ci95"]
    assert low == 0.0 and high == 1.0


def test_benchmark_rejects_incomplete_task_sets():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    rows = [_row("t1", "A"), _row("t2", "A"), _row("t1", "B+JEV")]
    with pytest.raises(ValueError, match="B\\+JEV missing task t2"):
        agg.summarize(rows)


def test_benchmark_rejects_incomplete_or_duplicate_repetitions():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    full = [_row(t, "A", rep=r) for t in ("t1", "t2") for r in (1, 2, 3)]
    partial = full + [_row(t, "B", rep=1) for t in ("t1", "t2")]
    with pytest.raises(ValueError, match="B/t1 missing rep 2, 3"):
        agg.summarize(partial)
    # The short cell is blamed even when it is the first row in the file.
    short_first = [_row("t1", "B", rep=1)] + full + [_row(t, "B", rep=r) for t in ("t2",) for r in (1, 2, 3)]
    with pytest.raises(ValueError) as error:
        agg.summarize(short_first)
    assert "B/t1 missing rep 2, 3" in str(error.value)
    assert "A/" not in str(error.value) and "unexpected" not in str(error.value)
    duplicated = full + [_row(t, "B", rep=r) for t in ("t1", "t2") for r in (1, 2, 3)] + [_row("t1", "B", rep=3)]
    with pytest.raises(ValueError, match="B/t1 duplicate rep 3"):
        agg.summarize(duplicated)


@pytest.mark.parametrize("field", ["cost_usd", "latency_s", "retries", "human_interventions", "rep", "success"])
def test_benchmark_rejects_missing_metrics(field):
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    broken = _row("t1", "A")
    del broken[field]
    with pytest.raises(ValueError, match=f"row 1: missing {field}"):
        agg.summarize([broken, _row("t2", "A")])


def test_benchmark_rejects_bad_metric_types():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    with pytest.raises(ValueError, match="cost_usd must be a finite non-negative number"):
        agg.summarize([_row("t1", "A", cost_usd=-1)])
    with pytest.raises(ValueError, match="success must be true or false"):
        agg.summarize([_row("t1", "A", success="yes")])
    with pytest.raises(ValueError, match="retries must be a non-negative integer"):
        agg.summarize([_row("t1", "A", retries=1.5)])


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_benchmark_rejects_non_finite_metrics(tmp_path, value):
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    line = json.dumps(_row("t1", "A")).replace('"latency_s": 1.0', f'"latency_s": {value}')
    results = tmp_path / "results.jsonl"
    results.write_text(line, encoding="utf-8")
    with pytest.raises(ValueError, match="latency_s must be a finite non-negative number"):
        agg.summarize(agg.load(str(results)))


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("task_id", 1, "task_id must be a non-empty string"),
        ("task_id", "  ", "task_id must be a non-empty string"),
        ("arch", 7, "arch must be a non-empty string"),
        ("rep", "1", "rep must be a non-negative integer"),
        ("rep", True, "rep must be a non-negative integer"),
        ("rep", -1, "rep must be a non-negative integer"),
    ],
)
def test_benchmark_rejects_non_text_identifiers(field, value, message):
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    with pytest.raises(ValueError, match=message):
        agg.summarize([{**_row("t1", "A"), field: value}])


def test_benchmark_does_not_merge_numeric_and_text_task_ids():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    rows = [_row("1", "A", True, rep=1), _row("1", "A", False, rep=2)]
    rows.append({**_row("x", "A", False, rep=1), "task_id": 1})
    with pytest.raises(ValueError, match="row 3: task_id must be a non-empty string"):
        agg.summarize(rows)


def test_benchmark_baseline_keeps_file_order_or_explicit_choice():
    agg = _load(SKILLS_ROOT / "jev-benchmark" / "scripts" / "aggregate.py")
    rows = [_row(t, "control", False) for t in ("t1", "t2")] + [_row(t, "B+JEV") for t in ("t1", "t2")]
    summary = agg.summarize(rows)
    assert list(summary) == ["control", "B+JEV"]
    assert summary["control"]["diff_vs_baseline_ci95"] is None
    assert summary["B+JEV"]["diff_vs_baseline_ci95"][0] > 0
    explicit = agg.summarize(rows, baseline="B+JEV")
    assert explicit["control"]["diff_vs_baseline_ci95"][1] < 0
    with pytest.raises(ValueError, match="not found"):
        agg.summarize(rows, baseline="missing")
