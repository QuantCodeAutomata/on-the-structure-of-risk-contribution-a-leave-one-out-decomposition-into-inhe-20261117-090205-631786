"""Tests for exp/exp_2.py: convergence simulation on synthetic data."""
from __future__ import annotations

import numpy as np
import pytest

from data.generate_synthetic import build_covariance, simulate_returns
from exp import exp_2


def test_build_covariance_shape_and_values():
    sigma = build_covariance(n_assets=5, diag=1.0, offdiag=0.5)
    assert sigma.shape == (5, 5)
    assert np.allclose(np.diag(sigma), 1.0)
    off_mask = ~np.eye(5, dtype=bool)
    assert np.allclose(sigma[off_mask], 0.5)


def test_population_targets_match_analytic_formula():
    sigma = build_covariance(5, 1.0, 0.5)
    weights = np.ones(5)
    targets = exp_2.population_targets(sigma, weights)
    sigma_p = float(np.sqrt(weights @ sigma @ weights))
    assert np.isclose(targets["total_rc"], sigma_p)
    assert np.isclose(targets["total_inh"] + targets["total_corr"], sigma_p)
    assert targets["total_inh"] >= 0


def test_expanding_window_estimates_no_lookahead_and_length():
    """The T-th estimate must only depend on the first T observations."""
    rng = np.random.default_rng(1)
    sigma = build_covariance(5, 1.0, 0.5)
    returns = simulate_returns(60, sigma, rng)
    weights = np.ones(5)
    estimates = exp_2.expanding_window_estimates(returns, weights, min_window=5)
    assert list(estimates.index) == list(range(5, 61))

    returns_perturbed = returns.copy()
    returns_perturbed[30:] += 1000.0  # perturb only observations after T=10
    estimates_perturbed = exp_2.expanding_window_estimates(returns_perturbed, weights, min_window=5)
    assert np.isclose(estimates.loc[10, "total_rc"], estimates_perturbed.loc[10, "total_rc"])


def test_expanding_window_matches_naive_sample_covariance():
    """Cross-check the running-sum estimator against numpy's direct sample covariance."""
    rng = np.random.default_rng(2)
    sigma = build_covariance(5, 1.0, 0.5)
    returns = simulate_returns(30, sigma, rng)
    weights = np.ones(5)
    estimates = exp_2.expanding_window_estimates(returns, weights, min_window=10)
    for t in (10, 20, 30):
        naive_cov = np.cov(returns[:t], rowvar=False, ddof=1)
        sigma_p = float(np.sqrt(weights @ naive_cov @ weights))
        assert np.isclose(estimates.loc[t, "total_rc"], sigma_p)


def test_run_bootstrap_shapes_and_convergence_narrows():
    """Confidence bands must narrow (not widen) from a short to a long window,
    reflecting convergence of the expanding-window estimator (Appendix B)."""
    sigma = build_covariance(5, 1.0, 0.5)
    weights = np.ones(5)
    draws = exp_2.run_bootstrap(
        n_bootstrap=30, max_sample=150, min_window=5, sigma=sigma, weights=weights, seed=0
    )
    assert set(draws.keys()) == {"total_rc", "total_inh", "total_corr"}
    summary = exp_2.summarize(draws["total_rc"])
    band_short = summary.loc[5, "p95"] - summary.loc[5, "p05"]
    band_long = summary.loc[150, "p95"] - summary.loc[150, "p05"]
    assert band_long < band_short


@pytest.mark.parametrize("metric", ["total_rc", "total_inh", "total_corr"])
def test_summarize_median_within_percentile_band(metric):
    sigma = build_covariance(5, 1.0, 0.5)
    weights = np.ones(5)
    draws = exp_2.run_bootstrap(n_bootstrap=20, max_sample=40, min_window=5, sigma=sigma, weights=weights, seed=3)
    summary = exp_2.summarize(draws[metric])
    assert (summary["p05"] <= summary["median"]).all()
    assert (summary["median"] <= summary["p95"]).all()
