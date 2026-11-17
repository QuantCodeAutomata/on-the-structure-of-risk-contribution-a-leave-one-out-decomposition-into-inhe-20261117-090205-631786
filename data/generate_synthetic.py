"""Synthetic Gaussian returns for the RC convergence simulation (Appendix B).

Generates i.i.d. multivariate-normal daily returns r_t ~ N(0, Sigma) for the
five-asset simulation with diagonal 1 and off-diagonal 0.5 (Appendix B).
"""
from __future__ import annotations

import numpy as np

from src import config


def build_covariance(n_assets: int = config.N_ASSETS, diag: float = config.COV_DIAG,
                      offdiag: float = config.COV_OFFDIAG) -> np.ndarray:
    """Sigma with ``diag`` on the diagonal and ``offdiag`` elsewhere (Appendix B)."""
    sigma = np.full((n_assets, n_assets), offdiag)
    np.fill_diagonal(sigma, diag)
    return sigma


def simulate_returns(
    n_obs: int, sigma: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Draw ``n_obs`` i.i.d. observations from N(0, Sigma) (Appendix B)."""
    mean = np.zeros(sigma.shape[0])
    return rng.multivariate_normal(mean, sigma, size=n_obs)
