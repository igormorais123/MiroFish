#!/usr/bin/env python3
"""Aggregate JEV benchmark results per architecture.

Input: JSONL with task_id, arch, rep, success, cost_usd, latency_s, retries,
human_interventions. Output: a markdown table plus a 95% bootstrap interval for
the success rate of each architecture, and paired intervals for the difference
against the baseline (the first architecture in the file, or the one passed as
second argument). Every architecture must cover the same task ids.

The bootstrap resamples tasks, not individual runs: repetitions of one task are
averaged first, and the same resampled task ids are used for every architecture
(paired design). Resampling runs would treat repetitions as independent and
produce artificially narrow intervals. Standard library only.
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from collections import defaultdict

BOOTSTRAP_SAMPLES = 2000


def load(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _task_success(items: list[dict]) -> dict[str, float]:
    """Mean success per task_id, averaging repetitions within the task."""
    per_task: dict[str, list[int]] = defaultdict(list)
    for item in items:
        per_task[str(item["task_id"])].append(1 if item.get("success") else 0)
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


def _check_same_tasks(task_rates: dict[str, dict[str, float]]) -> None:
    """Refuse incomplete runs: every architecture must cover the same task ids."""
    all_tasks = set().union(*(set(rates) for rates in task_rates.values()))
    missing = {arch: sorted(all_tasks - set(rates)) for arch, rates in task_rates.items()}
    missing = {arch: tasks for arch, tasks in missing.items() if tasks}
    if missing:
        detail = "; ".join(f"{arch} missing {', '.join(tasks)}" for arch, tasks in missing.items())
        raise ValueError(f"architectures do not cover the same tasks: {detail}")


def summarize(rows: list[dict], baseline: str | None = None) -> dict[str, dict]:
    """Summarize per architecture, keeping the order in which they first appear.

    The baseline defaults to the first architecture in the file (the control),
    never to alphabetical order.
    """
    by_arch: dict[str, list[dict]] = {}
    for row in rows:
        by_arch.setdefault(row["arch"], []).append(row)

    if baseline is None:
        baseline = next(iter(by_arch))
    if baseline not in by_arch:
        raise ValueError(f"baseline {baseline!r} not found; available: {', '.join(by_arch)}")
    ordered = [baseline] + [arch for arch in by_arch if arch != baseline]

    task_rates = {arch: _task_success(by_arch[arch]) for arch in ordered}
    _check_same_tasks(task_rates)
    boot = paired_bootstrap(task_rates)

    summary = {}
    for arch in ordered:
        items = by_arch[arch]
        successes = sum(1 for item in items if item.get("success"))
        total_cost = sum(float(item.get("cost_usd", 0)) for item in items)
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
            "median_latency_s": statistics.median(float(item.get("latency_s", 0)) for item in items),
            "mean_retries": statistics.mean(float(item.get("retries", 0)) for item in items),
            "human_interventions": sum(int(item.get("human_interventions", 0)) for item in items),
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
    rows = load(sys.argv[1])
    if not rows:
        print("no results", file=sys.stderr)
        return 1
    try:
        summary = summarize(rows, baseline=sys.argv[2] if len(sys.argv) == 3 else None)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
