"""Statistical distance and fairness metrics for Vox Science fidelity reports.

Pure-Python implementations of:

- 1D Wasserstein (earth mover's) distance
- KL divergence (with smoothing to avoid log(0))
- Mean Absolute Error
- Demographic Parity Difference between subgroups
- Intra-group variance
- Temporal stability (Pearson-like on paired observations)

The module deliberately avoids depending on ``scipy``/``numpy``: the harness
must run in restricted environments (VPS container) where heavy stacks are
unavailable. If ``scipy`` is later installed, callers may import from there;
the contract on these helpers is the result shape.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def wasserstein_1d(sample_a: Sequence[float], sample_b: Sequence[float]) -> float:
    """Approximate 1D Wasserstein distance via sorted-sample CDF gap.

    Returns ``0.0`` if either sample is empty (signalling "no comparison
    possible" rather than raising — the harness uses ``None`` upstream for
    that case).
    """

    if not sample_a or not sample_b:
        return 0.0
    a = sorted(float(x) for x in sample_a)
    b = sorted(float(x) for x in sample_b)
    n = max(len(a), len(b))
    # Resample both to a common grid of length n by linear position.
    grid = [i / (n - 1) if n > 1 else 0.0 for i in range(n)]
    a_resampled = [_quantile(a, q) for q in grid]
    b_resampled = [_quantile(b, q) for q in grid]
    return sum(abs(x - y) for x, y in zip(a_resampled, b_resampled)) / n


def kl_divergence(
    p: Sequence[float],
    q: Sequence[float],
    *,
    epsilon: float = 1e-9,
) -> float:
    """KL(p || q) over discrete distributions, with Laplace smoothing."""

    if len(p) != len(q) or not p:
        return 0.0
    p_norm = _normalize(p, epsilon)
    q_norm = _normalize(q, epsilon)
    return sum(pi * math.log(pi / qi) for pi, qi in zip(p_norm, q_norm))


def mean_absolute_error(observed: Sequence[float], expected: Sequence[float]) -> float:
    if not observed or len(observed) != len(expected):
        return 0.0
    return sum(abs(o - e) for o, e in zip(observed, expected)) / len(observed)


def demographic_parity_difference(
    rates_by_group: Mapping[str, float],
) -> dict[str, dict[str, float]]:
    """Pairwise DPD between subgroups.

    Output: ``{"male__vs__female": {"value": 0.08, "groups": ["male", "female"]}}``.
    Maximum absolute difference is also exposed under key ``"__max__"``.
    """

    groups = sorted(rates_by_group.keys())
    out: dict[str, dict[str, float]] = {}
    max_value = 0.0
    for i, g1 in enumerate(groups):
        for g2 in groups[i + 1 :]:
            delta = abs(float(rates_by_group[g1]) - float(rates_by_group[g2]))
            key = f"{g1}__vs__{g2}"
            out[key] = {
                "value": round(delta, 6),
                "groups": [g1, g2],
            }
            max_value = max(max_value, delta)
    out["__max__"] = {"value": round(max_value, 6), "groups": []}
    return out


def intra_group_variance(
    samples_by_group: Mapping[str, Sequence[float]],
) -> dict[str, float]:
    out: dict[str, float] = {}
    for group, samples in samples_by_group.items():
        if not samples:
            out[group] = 0.0
            continue
        mean = sum(samples) / len(samples)
        out[group] = round(
            sum((float(x) - mean) ** 2 for x in samples) / len(samples), 6
        )
    return out


def temporal_stability(
    observations_t0: Sequence[float],
    observations_t1: Sequence[float],
) -> float:
    """Stability score in [0, 1] where 1 = identical distributions.

    Uses ``1 - normalized_wasserstein`` as a robust proxy when paired Pearson
    is not feasible (different lengths).
    """

    if not observations_t0 or not observations_t1:
        return 1.0
    w = wasserstein_1d(observations_t0, observations_t1)
    a_range = max(observations_t0 + observations_t1) - min(
        observations_t0 + observations_t1
    )
    if a_range <= 0:
        return 1.0
    return max(0.0, 1.0 - w / a_range)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _quantile(sorted_sample: Sequence[float], q: float) -> float:
    if not sorted_sample:
        return 0.0
    if q <= 0:
        return float(sorted_sample[0])
    if q >= 1:
        return float(sorted_sample[-1])
    idx = q * (len(sorted_sample) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return float(sorted_sample[lo])
    frac = idx - lo
    return float(sorted_sample[lo]) * (1 - frac) + float(sorted_sample[hi]) * frac


def _normalize(values: Iterable[float], epsilon: float) -> list[float]:
    smoothed = [max(float(v), 0.0) + epsilon for v in values]
    total = sum(smoothed)
    return [s / total for s in smoothed]


__all__ = [
    "wasserstein_1d",
    "kl_divergence",
    "mean_absolute_error",
    "demographic_parity_difference",
    "intra_group_variance",
    "temporal_stability",
]
