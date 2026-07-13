"""Statistical distance and fairness metrics for Vox Science fidelity reports.

Pure-Python implementations of:

- 1D Wasserstein (earth mover's) distance
- KL divergence (with smoothing to avoid log(0))
- Mean Absolute Error
- Demographic Parity Difference between subgroups
- Intra-group variance
- Temporal stability (Pearson-like on paired observations)
- Declared-order categorical Wasserstein for labeled probability vectors

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

    Invalid or empty samples raise ``ValueError``; callers must report the
    metric as unavailable rather than mistaking a sentinel for a perfect fit.
    """

    a = sorted(_validated_vector(sample_a, "sample_a"))
    b = sorted(_validated_vector(sample_b, "sample_b"))
    n = max(len(a), len(b))
    # Resample both to a common grid of length n by linear position.
    grid = [i / (n - 1) if n > 1 else 0.0 for i in range(n)]
    a_resampled = [_quantile(a, q) for q in grid]
    b_resampled = [_quantile(b, q) for q in grid]
    return sum(abs(x - y) for x, y in zip(a_resampled, b_resampled)) / n


def categorical_wasserstein_1d(
    observed_mass: Sequence[float], predicted_mass: Sequence[float]
) -> float:
    """Discrete W1 over the declared category index, preserving label order.

    Inputs are probability masses aligned to the same validated category list.
    Adjacent categories have unit distance. Unlike sample Wasserstein, this must
    never sort values: reversing category masses is substantively different.
    """

    observed = _validated_vector(
        observed_mass, "observed_mass", non_negative=True, positive_mass=True
    )
    predicted = _validated_vector(
        predicted_mass, "predicted_mass", non_negative=True, positive_mass=True
    )
    if len(observed) != len(predicted):
        raise ValueError("distribution_dimensions_mismatch")
    observed = _normalize(observed, 0.0)
    predicted = _normalize(predicted, 0.0)
    observed_cdf = 0.0
    predicted_cdf = 0.0
    distance = 0.0
    for observed_value, predicted_value in zip(observed[:-1], predicted[:-1]):
        observed_cdf += observed_value
        predicted_cdf += predicted_value
        distance += abs(observed_cdf - predicted_cdf)
    return distance


def categorical_temporal_stability(
    distribution_t0: Sequence[float], distribution_t1: Sequence[float]
) -> float:
    """Stability in [0, 1] from declared-order categorical W1."""

    if len(distribution_t0) != len(distribution_t1):
        raise ValueError("distribution_dimensions_mismatch")
    max_distance = max(1, len(distribution_t0) - 1)
    distance = categorical_wasserstein_1d(distribution_t0, distribution_t1)
    return max(0.0, 1.0 - distance / max_distance)


def multiclass_brier_score(
    predictions: Sequence[Sequence[float]], observed_class_indices: Sequence[int]
) -> float:
    """Mean per-ID multiclass Brier score (lower is better)."""

    clean, observed = _validated_classification_pairs(
        predictions, observed_class_indices
    )
    total = 0.0
    for distribution, observed_index in zip(clean, observed):
        total += sum(
            (probability - (1.0 if index == observed_index else 0.0)) ** 2
            for index, probability in enumerate(distribution)
        )
    return total / len(clean)


def multiclass_log_loss(
    predictions: Sequence[Sequence[float]],
    observed_class_indices: Sequence[int],
    *,
    epsilon: float = 1e-15,
) -> float:
    """Mean per-ID multiclass log loss with finite log(0) clipping."""

    if not 0 < epsilon < 0.5:
        raise ValueError("epsilon_out_of_range")
    clean, observed = _validated_classification_pairs(
        predictions, observed_class_indices
    )
    return -sum(
        math.log(max(epsilon, distribution[observed_index]))
        for distribution, observed_index in zip(clean, observed)
    ) / len(clean)


def kl_divergence(
    p: Sequence[float],
    q: Sequence[float],
    *,
    epsilon: float = 1e-9,
) -> float:
    """KL(p || q) over discrete distributions, with Laplace smoothing."""

    p_values = _validated_vector(p, "p", non_negative=True, positive_mass=True)
    q_values = _validated_vector(q, "q", non_negative=True, positive_mass=True)
    if len(p_values) != len(q_values):
        raise ValueError("distribution_dimensions_mismatch")
    p_norm = _normalize(p_values, epsilon)
    q_norm = _normalize(q_values, epsilon)
    return sum(pi * math.log(pi / qi) for pi, qi in zip(p_norm, q_norm))


def mean_absolute_error(observed: Sequence[float], expected: Sequence[float]) -> float:
    observed_values = _validated_vector(observed, "observed")
    expected_values = _validated_vector(expected, "expected")
    if len(observed_values) != len(expected_values):
        raise ValueError("distribution_dimensions_mismatch")
    return sum(abs(o - e) for o, e in zip(observed_values, expected_values)) / len(observed_values)


def demographic_parity_difference(
    rates_by_group: Mapping[str, float],
) -> dict[str, dict[str, object]]:
    """Pairwise DPD between subgroups.

    Output: ``{"male__vs__female": {"value": 0.08, "groups": ["male", "female"]}}``.
    Maximum absolute difference is also exposed under key ``"__max__"``.
    """

    if len(rates_by_group) < 2:
        raise ValueError("at_least_two_subgroups_required")
    clean_rates: dict[str, float] = {}
    for group, value in rates_by_group.items():
        if not isinstance(group, str) or not group:
            raise ValueError("subgroup_name_invalid")
        numeric = _validated_number(value, "subgroup_rate")
        if not 0 <= numeric <= 1:
            raise ValueError("subgroup_rate_out_of_range")
        clean_rates[group] = numeric
    groups = sorted(clean_rates.keys())
    out: dict[str, dict[str, object]] = {}
    max_value = 0.0
    for i, g1 in enumerate(groups):
        for g2 in groups[i + 1 :]:
            delta = abs(clean_rates[g1] - clean_rates[g2])
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
        clean = _validated_vector(samples, f"samples_by_group[{group}]")
        mean = sum(clean) / len(clean)
        out[group] = round(
            sum((x - mean) ** 2 for x in clean) / len(clean), 6
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

    t0 = _validated_vector(observations_t0, "observations_t0")
    t1 = _validated_vector(observations_t1, "observations_t1")
    w = wasserstein_1d(t0, t1)
    combined = t0 + t1
    a_range = max(combined) - min(combined)
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


def _validated_classification_pairs(
    predictions: Sequence[Sequence[float]], observed_class_indices: Sequence[int]
) -> tuple[list[list[float]], list[int]]:
    if (
        not isinstance(predictions, Sequence)
        or isinstance(predictions, (str, bytes))
        or not predictions
        or not isinstance(observed_class_indices, Sequence)
        or isinstance(observed_class_indices, (str, bytes))
        or len(predictions) != len(observed_class_indices)
    ):
        raise ValueError("classification_pairs_invalid")
    clean: list[list[float]] = []
    dimension: int | None = None
    for distribution in predictions:
        values = _validated_vector(
            distribution, "prediction", non_negative=True, positive_mass=True
        )
        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError("prediction_not_probability")
        dimension = dimension or len(values)
        if len(values) != dimension:
            raise ValueError("distribution_dimensions_mismatch")
        clean.append(values)
    observed: list[int] = []
    for value in observed_class_indices:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or dimension is None
            or value >= dimension
        ):
            raise ValueError("observed_class_index_invalid")
        observed.append(value)
    return clean, observed


def _validated_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}_must_be_numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name}_must_be_finite")
    return numeric


def _validated_vector(
    values: Sequence[float],
    name: str,
    *,
    non_negative: bool = False,
    positive_mass: bool = False,
) -> list[float]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise ValueError(f"{name}_must_be_nonempty_sequence")
    clean = [_validated_number(value, name) for value in values]
    if non_negative and any(value < 0 for value in clean):
        raise ValueError(f"{name}_must_be_non_negative")
    if positive_mass and sum(clean) <= 0:
        raise ValueError(f"{name}_must_have_positive_mass")
    return clean


__all__ = [
    "wasserstein_1d",
    "categorical_wasserstein_1d",
    "categorical_temporal_stability",
    "multiclass_brier_score",
    "multiclass_log_loss",
    "kl_divergence",
    "mean_absolute_error",
    "demographic_parity_difference",
    "intra_group_variance",
    "temporal_stability",
]
