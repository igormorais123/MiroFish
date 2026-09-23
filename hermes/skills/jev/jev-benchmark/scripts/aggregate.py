#!/usr/bin/env python3
"""Aggregate JEV benchmark results per architecture.

Input: JSONL with task_id, arch, rep, success, cost_usd, latency_s, retries,
human_interventions. Output: a markdown table plus a bootstrap 95% interval for
the success rate of each architecture. Standard library only.
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


def bootstrap_interval(values: list[int], seed: int = 42) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(BOOTSTRAP_SAMPLES))
    return means[int(0.025 * BOOTSTRAP_SAMPLES)], means[int(0.975 * BOOTSTRAP_SAMPLES) - 1]


def summarize(rows: list[dict]) -> dict[str, dict]:
    by_arch: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_arch[row["arch"]].append(row)

    summary = {}
    for arch, items in sorted(by_arch.items()):
        successes = [1 if item.get("success") else 0 for item in items]
        total_cost = sum(float(item.get("cost_usd", 0)) for item in items)
        low, high = bootstrap_interval(successes)
        summary[arch] = {
            "runs": len(items),
            "success_rate": sum(successes) / len(items),
            "success_ci95": (low, high),
            "mean_cost_usd": total_cost / len(items),
            "cost_per_success_usd": total_cost / sum(successes) if sum(successes) else None,
            "median_latency_s": statistics.median(float(item.get("latency_s", 0)) for item in items),
            "mean_retries": statistics.mean(float(item.get("retries", 0)) for item in items),
            "human_interventions": sum(int(item.get("human_interventions", 0)) for item in items),
        }
    return summary


def render(summary: dict[str, dict]) -> str:
    lines = [
        "| arquitetura | execuções | sucesso | IC 95% | custo médio | custo por sucesso | latência mediana | retentativas | intervenções humanas |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for arch, s in summary.items():
        cps = f"US$ {s['cost_per_success_usd']:.4f}" if s["cost_per_success_usd"] is not None else "sem sucesso"
        lines.append(
            f"| {arch} | {s['runs']} | {s['success_rate']:.1%} | "
            f"{s['success_ci95'][0]:.1%}–{s['success_ci95'][1]:.1%} | US$ {s['mean_cost_usd']:.4f} | {cps} | "
            f"{s['median_latency_s']:.1f} s | {s['mean_retries']:.2f} | {s['human_interventions']} |"
        )
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: aggregate.py results.jsonl", file=sys.stderr)
        return 2
    rows = load(sys.argv[1])
    if not rows:
        print("no results", file=sys.stderr)
        return 1
    print(render(summarize(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
