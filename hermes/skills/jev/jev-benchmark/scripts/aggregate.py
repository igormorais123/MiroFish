#!/usr/bin/env python3
"""Aggregate JEV benchmark results per architecture.

Input: JSONL with task_id, arch, rep, success, cost_usd, latency_s, retries,
human_interventions. Output: a markdown table plus a 95% bootstrap interval for
the success rate of each architecture, and paired intervals for the difference
against the baseline (the first architecture in the file, or the one passed as
second argument). Rows missing a metric, and grids where some (arch, task_id)
cell lacks a repetition or repeats one, are rejected instead of averaged.

The bootstrap resamples tasks, not individual runs: repetitions of one task are
averaged first, and the same resampled task ids are used for every architecture
(paired design). Resampling runs would treat repetitions as independent and
produce artificially narrow intervals. Standard library only.
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
from collections import defaultdict

BOOTSTRAP_SAMPLES = 2000


def load(path: str) -> list[dict]:
    """Read JSONL; malformed lines raise ValueError naming the line number."""
    rows = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"line {number}: invalid JSON ({error.msg})") from None
    return rows


def _task_success(items: list[dict]) -> dict[str, float]:
    """Mean success per task_id, averaging repetitions within the task."""
    per_task: dict[str, list[int]] = defaultdict(list)
    for item in items:
        per_task[item["task_id"]].append(1 if item["success"] else 0)
    return {task: sum(values) / len(values) for task, values in per_task.items()}


def _percentile_interval(samples: list[float]) -> tuple[float, float]:
    ordered = sorted(samples)
    return ordered[int(0.025 * len(ordered))], ordered[int(0.975 * len(ordered)) - 1]


def paired_bootstrap(
    task_rates: dict[str, dict[str, float]], seed: int = 42
) -> dict[str, list[float]]:
    """Resample shared task ids and return, per architecture, the bootstrap means."""
    shared = sorted(next(iter(task_rates.values())))
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {arch: [] for arch in task_rates}
    for _ in range(BOOTSTRAP_SAMPLES):
        drawn = [rng.choice(shared) for _ in shared]
        for arch, rates in task_rates.items():
            samples[arch].append(sum(rates[task] for task in drawn) / len(drawn))
    return samples


REQUIRED_FIELDS = (
    "task_id",
    "arch",
    "rep",
    "success",
    "cost_usd",
    "latency_s",
    "retries",
    "human_interventions",
)
COUNT_FIELDS = ("retries", "human_interventions")
MEASURE_FIELDS = ("cost_usd", "latency_s")


def _is_number(value) -> bool:
    """Finite int or float; bool, NaN and infinities are not measurements."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_rows(rows: list[dict]) -> None:
    """Refuse partial or malformed runs instead of silently averaging them.

    Every row must carry every metric (a missing cost is not a zero cost), and
    every (arch, task_id) cell must hold the same set of repetitions with no
    duplicates, so each architecture is measured on the full, identical grid.
    """
    errors: list[str] = []
    cells: dict[tuple[str, str], list] = defaultdict(list)
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"row {index}: must be a JSON object, got {type(row).__name__}")
            continue
        missing = [field for field in REQUIRED_FIELDS if row.get(field) is None]
        if missing:
            errors.append(f"row {index}: missing {', '.join(missing)}")
            continue
        # Identifiers are validated, never coerced: task_id 1 and "1" must not merge.
        row_errors = [
            f"row {index}: {field} must be a non-empty string"
            for field in ("task_id", "arch")
            if not isinstance(row[field], str) or not row[field].strip()
        ]
        if not isinstance(row["rep"], int) or isinstance(row["rep"], bool) or row["rep"] < 0:
            row_errors.append(f"row {index}: rep must be a non-negative integer")
        errors.extend(row_errors)
        if not isinstance(row["success"], bool):
            errors.append(f"row {index}: success must be true or false")
        for field in MEASURE_FIELDS:
            if not _is_number(row[field]) or row[field] < 0:
                errors.append(f"row {index}: {field} must be a finite non-negative number")
        for field in COUNT_FIELDS:
            if not isinstance(row[field], int) or isinstance(row[field], bool) or row[field] < 0:
                errors.append(f"row {index}: {field} must be a non-negative integer")
        if not row_errors:  # invalid identifiers may be unhashable (lists, objects)
            cells[(row["arch"], row["task_id"])].append(row["rep"])
    if errors:
        raise ValueError("invalid rows: " + "; ".join(errors))

    # The expected grid is the union of everything seen, so the short cell is
    # the one reported, regardless of which row happens to come first.
    archs = sorted({arch for arch, _ in cells})
    tasks = sorted({task for _, task in cells})
    expected_reps = {rep for reps in cells.values() for rep in reps}
    problems: list[str] = []
    for arch in archs:
        for task in tasks:
            reps = cells.get((arch, task), [])
            if not reps:
                problems.append(f"{arch} missing task {task}")
                continue
            duplicates = sorted({rep for rep in reps if reps.count(rep) > 1})
            if duplicates:
                problems.append(f"{arch}/{task} duplicate rep {', '.join(map(str, duplicates))}")
            absent = sorted(expected_reps - set(reps))
            if absent:
                problems.append(f"{arch}/{task} missing rep {', '.join(map(str, absent))}")
    if problems:
        raise ValueError("incomplete benchmark grid: " + "; ".join(problems))


def summarize(rows: list[dict], baseline: str | None = None) -> dict[str, dict]:
    """Summarize per architecture, keeping the order in which they first appear.

    The baseline defaults to the first architecture in the file (the control),
    never to alphabetical order.
    """
    validate_rows(rows)
    by_arch: dict[str, list[dict]] = {}
    for row in rows:
        by_arch.setdefault(row["arch"], []).append(row)

    if baseline is None:
        baseline = next(iter(by_arch))
    if baseline not in by_arch:
        raise ValueError(f"baseline {baseline!r} not found; available: {', '.join(by_arch)}")
    ordered = [baseline] + [arch for arch in by_arch if arch != baseline]

    task_rates = {arch: _task_success(by_arch[arch]) for arch in ordered}
    boot = paired_bootstrap(task_rates)

    summary = {}
    for arch in ordered:
        items = by_arch[arch]
        successes = sum(1 for item in items if item["success"])
        total_cost = sum(float(item["cost_usd"]) for item in items)
        rates = task_rates[arch]
        ci = _percentile_interval(boot[arch])
        diff_ci = None
        if arch != baseline:
            diff_ci = _percentile_interval([b - a for a, b in zip(boot[baseline], boot[arch])])
        summary[arch] = {
            "runs": len(items),
            "tasks": len(rates),
            "success_rate": sum(rates.values()) / len(rates),
            "success_ci95": ci,
            "diff_vs_baseline_ci95": diff_ci,
            "mean_cost_usd": total_cost / len(items),
            "cost_per_success_usd": total_cost / successes if successes else None,
            "median_latency_s": statistics.median(float(item["latency_s"]) for item in items),
            "mean_retries": statistics.mean(float(item["retries"]) for item in items),
            "human_interventions": sum(int(item["human_interventions"]) for item in items),
        }
    return summary


def render(summary: dict[str, dict]) -> str:
    lines = [
        "| arquitetura | tarefas | execuções | sucesso | IC 95% | diferença vs base (IC 95% pareado) | custo médio | custo por sucesso | latência mediana | retentativas | intervenções humanas |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arch, s in summary.items():
        cps = f"US$ {s['cost_per_success_usd']:.4f}" if s["cost_per_success_usd"] is not None else "sem sucesso"
        diff = s["diff_vs_baseline_ci95"]
        diff_text = f"{diff[0]:+.1%} a {diff[1]:+.1%}" if diff else "base"
        lines.append(
            f"| {arch} | {s['tasks']} | {s['runs']} | {s['success_rate']:.1%} | "
            f"{s['success_ci95'][0]:.1%}–{s['success_ci95'][1]:.1%} | {diff_text} | "
            f"US$ {s['mean_cost_usd']:.4f} | {cps} | "
            f"{s['median_latency_s']:.1f} s | {s['mean_retries']:.2f} | {s['human_interventions']} |"
        )
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: aggregate.py results.jsonl [baseline_arch]", file=sys.stderr)
        return 2
    # Every input problem ends in a one-line error and exit 1, never a traceback.
    try:
        rows = load(sys.argv[1])
        if not rows:
            print("no results", file=sys.stderr)
            return 1
        summary = summarize(rows, baseline=sys.argv[2] if len(sys.argv) == 3 else None)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
