"""Unit tests for vox_science.metrics — pure-Python statistical helpers."""

from app.services.vox_science.metrics import (
    demographic_parity_difference,
    intra_group_variance,
    kl_divergence,
    mean_absolute_error,
    temporal_stability,
    wasserstein_1d,
)


def test_wasserstein_identical_samples_is_zero():
    assert wasserstein_1d([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0


def test_wasserstein_shifted_sample_is_positive():
    distance = wasserstein_1d([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])
    assert 0.5 < distance < 1.5


def test_kl_divergence_identical_is_zero():
    assert kl_divergence([0.5, 0.5], [0.5, 0.5]) == 0.0


def test_kl_divergence_diverging_is_positive():
    assert kl_divergence([0.9, 0.1], [0.1, 0.9]) > 0.5


def test_mean_absolute_error_basic():
    assert mean_absolute_error([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0
    assert mean_absolute_error([1.0, 2.0], [2.0, 3.0]) == 1.0


def test_dpd_pairwise_and_max():
    out = demographic_parity_difference({"male": 0.30, "female": 0.50, "other": 0.20})
    # Maior diferenca eh female - other = 0.30
    assert out["__max__"]["value"] == 0.30
    pair_key = next(k for k in out if k != "__max__" and "female" in k and "other" in k)
    assert out[pair_key]["value"] == 0.30


def test_dpd_max_zero_when_all_equal():
    out = demographic_parity_difference({"a": 0.5, "b": 0.5})
    assert out["__max__"]["value"] == 0.0


def test_intra_group_variance_zero_for_constant_sample():
    out = intra_group_variance({"g1": [0.5, 0.5, 0.5]})
    assert out["g1"] == 0.0


def test_intra_group_variance_positive():
    out = intra_group_variance({"g1": [0.0, 1.0]})
    assert out["g1"] > 0.0


def test_temporal_stability_identical_is_one():
    assert temporal_stability([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0


def test_temporal_stability_decays_with_shift():
    score = temporal_stability([1.0, 2.0, 3.0], [3.0, 4.0, 5.0])
    assert 0.0 <= score < 0.9
