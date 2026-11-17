"""Inherent and Correlation Decomposition (ICD) of Risk Contribution.

Custom implementation of the paper's Section 3-4 formulas. No portfolio-
optimization library (skfolio, pyportfolioopt) exposes a leave-one-out split
of risk contribution into an inherent (own-variance) and a correlation
(covariance-with-others) term: skfolio's ``Portfolio.contribution`` computes a
single contribution number per asset for a chosen risk or ratio measure, not
this additive decomposition, so the formulas below are implemented directly
from the paper's equations.

Notation follows the paper: for weights w and covariance matrix Sigma,
sigma_p = sqrt(w' Sigma w) is portfolio volatility, r_a is asset a's return,
r_p = sum_i w_i r_i is the portfolio return.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def portfolio_variance(weights: pd.Series, cov: pd.DataFrame) -> float:
    """Portfolio variance w' Sigma w (paper Sec. 3)."""
    w = weights.reindex(cov.index).to_numpy()
    sigma = cov.to_numpy()
    var = float(w @ sigma @ w)
    assert var >= 0, "portfolio variance must be non-negative"
    return var


def portfolio_vol(weights: pd.Series, cov: pd.DataFrame) -> float:
    """Portfolio volatility sigma_p = sqrt(w' Sigma w)."""
    return float(np.sqrt(portfolio_variance(weights, cov)))


def risk_contribution(weights: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """Standard Risk Contribution: RC(a) = w_a * cov(r_a, r_p) / sigma_p.

    Additive: sum_a RC(a) = sigma_p (Grinold & Kahn 1999; paper Sec. 2, eq. 1-2).
    """
    w = weights.reindex(cov.index)
    sigma_p = portfolio_vol(w, cov)
    cov_a_p = cov.to_numpy() @ w.to_numpy()  # cov(r_a, r_p) for every a
    rc = w.to_numpy() * cov_a_p / sigma_p
    return pd.Series(rc, index=cov.index, name="RC")


def icd_decompose(weights: pd.Series, cov: pd.DataFrame) -> pd.DataFrame:
    """Inherent and Correlation Decomposition of RC (paper eq. 10).

    For each asset a:
        RC_inh(a)  = w_a^2 * sigma_a^2 / sigma_p                      (>= 0)
        RC_corr(a) = w_a * cov(r_a, r_p - w_a * r_a) / sigma_p
        RC(a)      = RC_inh(a) + RC_corr(a)

    using cov(r_a, r_p - w_a r_a) = cov(r_a, r_p) - w_a * Var(r_a), the
    leave-one-out covariance expansion of eq. (5)-(9).

    Returns a DataFrame indexed like ``cov`` with columns
    ['weight', 'rc', 'rc_inh', 'rc_corr'].
    """
    w = weights.reindex(cov.index)
    sigma_p = portfolio_vol(w, cov)
    var_a = np.diag(cov.to_numpy())  # sigma_a^2
    cov_a_p = cov.to_numpy() @ w.to_numpy()  # cov(r_a, r_p)

    w_arr = w.to_numpy()
    rc_inh = (w_arr**2) * var_a / sigma_p
    cov_a_others = cov_a_p - w_arr * var_a  # cov(r_a, r_p - w_a r_a)
    rc_corr = w_arr * cov_a_others / sigma_p
    rc = rc_inh + rc_corr

    out = pd.DataFrame(
        {"weight": w_arr, "rc": rc, "rc_inh": rc_inh, "rc_corr": rc_corr},
        index=cov.index,
    )
    # Additivity check (paper Sec. 4.1): sum of RC equals portfolio volatility.
    assert np.isclose(out["rc"].sum(), sigma_p, atol=1e-6, rtol=1e-6)
    assert (out["rc_inh"] >= -1e-10).all(), "RC_inh must be non-negative (eq. 10)"
    return out


def leave_one_out_variance(weights: pd.Series, cov: pd.DataFrame, asset: str) -> float:
    """Var(r_p - w_a r_a): variance of the portfolio without position a (eq. 8)."""
    w = weights.reindex(cov.index)
    sigma_p2 = portfolio_variance(w, cov)
    w_a = float(w[asset])
    sigma_a2 = float(cov.loc[asset, asset])
    cov_a_p = float(cov.loc[asset].to_numpy() @ w.to_numpy())
    var = sigma_p2 + w_a**2 * sigma_a2 - 2 * w_a * cov_a_p
    return max(var, 0.0)


def incremental_vol(weights: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """iVol(a) = sigma_p - sigma_{p \\ a}: leave-one-out incremental volatility.

    Non-additive (paper Sec. 2, Appendix A); reported for comparison with RC.
    """
    sigma_p = portfolio_vol(weights, cov)
    out = {}
    for asset in cov.index:
        sigma_p_minus_a = np.sqrt(leave_one_out_variance(weights, cov, asset))
        out[asset] = sigma_p - sigma_p_minus_a
    return pd.Series(out, name="iVol")


def xsr_correlation(weights: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """X-sigma-rho correlation factor: rho(r_a, r_p) (Menchero & Davis 2011, Sec. 4.4).

    rho(r_a, r_p) = cov(r_a, r_p) / (sigma_a * sigma_p), the Pearson correlation
    of asset a's return with the *full* portfolio return (including a itself),
    unlike ICD's correlation-with-others term.
    """
    w = weights.reindex(cov.index)
    sigma_p = portfolio_vol(w, cov)
    sigma_a = np.sqrt(np.diag(cov.to_numpy()))
    cov_a_p = cov.to_numpy() @ w.to_numpy()
    rho = cov_a_p / (sigma_a * sigma_p)
    return pd.Series(rho, index=cov.index, name="XSR_Corr")


def discrete_hedge_condition(rc_inh: pd.Series, rc_corr: pd.Series) -> pd.Series:
    """Discrete hedging condition (eq. 11): RC_corr(a) < -0.5 * RC_inh(a).

    True when holding position a lowers portfolio volatility relative to not
    holding it at all (holding other positions fixed), a weaker condition than
    the marginal condition RC(a) < 0.
    """
    return rc_corr < (-0.5 * rc_inh)


def max_drawdown(cum_return_index: pd.Series) -> float:
    """Maximum drawdown (%) of a cumulative return index (back-adjusted series).

    mdd = min_t (index_t / running_max(index)_t - 1) * 100 (paper Sec. 5.1, Table 4).
    """
    running_max = cum_return_index.cummax()
    drawdown = cum_return_index / running_max - 1.0
    return float(drawdown.min() * 100.0)
