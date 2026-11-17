"""Unit tests for src/icd.py on small synthetic fixtures."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import icd


def make_cov(values: list[list[float]], names: list[str]) -> pd.DataFrame:
    return pd.DataFrame(values, index=names, columns=names)


def test_additivity_matches_portfolio_volatility():
    """RC components must sum exactly to portfolio volatility (paper eq. 2, 10)."""
    cov = make_cov([[1.0, 0.3, 0.1], [0.3, 2.0, 0.2], [0.1, 0.2, 0.5]], ["A", "B", "C"])
    weights = pd.Series({"A": 0.5, "B": 0.3, "C": 0.2})
    decomposed = icd.icd_decompose(weights, cov)
    sigma_p = icd.portfolio_vol(weights, cov)
    assert np.isclose(decomposed["rc"].sum(), sigma_p)
    assert np.isclose((decomposed["rc_inh"] + decomposed["rc_corr"]).sum(), sigma_p)


def test_rc_inh_nonnegative_and_matches_formula():
    """RC_inh(a) = w_a^2 sigma_a^2 / sigma_p >= 0, exact formula check (eq. 10)."""
    cov = make_cov([[4.0, 0.0], [0.0, 1.0]], ["X", "Y"])
    weights = pd.Series({"X": 2.0, "Y": -1.0})
    decomposed = icd.icd_decompose(weights, cov)
    sigma_p = icd.portfolio_vol(weights, cov)
    assert (decomposed["rc_inh"] >= 0).all()
    expected_inh_x = (2.0**2 * 4.0) / sigma_p
    assert np.isclose(decomposed.loc["X", "rc_inh"], expected_inh_x)


def test_overhedged_example_matches_paper_section_4_3():
    """Reproduce the paper's over-hedge numerical example (Sec. 4.3): h=1.5 hedge of
    unit-vol asset X with perfectly anti-correlated H (sigma_H=1): RC(H)=1.5>0 but the
    discrete condition holds, while RC_inh(H)=4.5 and RC_corr(H)=-3."""
    cov = make_cov([[1.0, -1.0], [-1.0, 1.0]], ["X", "H"])
    weights = pd.Series({"X": 1.0, "H": 1.5})
    decomposed = icd.icd_decompose(weights, cov)
    sigma_p = icd.portfolio_vol(weights, cov)
    assert np.isclose(sigma_p, 0.5)
    assert np.isclose(decomposed.loc["H", "rc_inh"], 4.5)
    assert np.isclose(decomposed.loc["H", "rc_corr"], -3.0)
    assert np.isclose(decomposed.loc["H", "rc"], 1.5)
    # marginal condition RC(H) < 0 is false, but the discrete condition holds
    marginal = decomposed.loc["H", "rc"] < 0
    discrete = icd.discrete_hedge_condition(
        pd.Series({"H": decomposed.loc["H", "rc_inh"]}), pd.Series({"H": decomposed.loc["H", "rc_corr"]})
    )
    assert not marginal
    assert bool(discrete["H"])


def test_xsr_correlation_differs_from_icd_on_large_position():
    """XSR correlation uses correlation with the full portfolio (incl. self) and
    can disagree in sign/diagnosis with the ICD correlation-with-others term."""
    cov = make_cov([[1.0, -1.0], [-1.0, 1.0]], ["X", "H"])
    weights = pd.Series({"X": 1.0, "H": 1.5})
    xsr = icd.xsr_correlation(weights, cov)
    decomposed = icd.icd_decompose(weights, cov)
    assert np.isclose(xsr["H"], 1.0)
    assert decomposed.loc["H", "rc_corr"] < 0


def test_incremental_vol_is_nonadditive():
    """iVol does not sum to portfolio volatility in general (Sec. 2, Appendix A)."""
    cov = make_cov([[1.0, 0.5, 0.2], [0.5, 1.0, 0.3], [0.2, 0.3, 1.0]], ["A", "B", "C"])
    weights = pd.Series({"A": 0.4, "B": 0.4, "C": 0.4})
    ivol = icd.incremental_vol(weights, cov)
    sigma_p = icd.portfolio_vol(weights, cov)
    assert not np.isclose(ivol.sum(), sigma_p)


def test_max_drawdown_known_series():
    """A known price path gives an exactly known maximum drawdown."""
    index = pd.Series([1.0, 1.2, 0.6, 0.9, 1.5])
    mdd = icd.max_drawdown(index)
    assert np.isclose(mdd, (0.6 / 1.2 - 1) * 100)


def test_portfolio_variance_rejects_negative_definite_like_input():
    """Portfolio variance assertion fires for an invalid (negative-definite-like)
    covariance input with incompatible weights."""
    cov = make_cov([[-1.0, 0.0], [0.0, -1.0]], ["A", "B"])
    weights = pd.Series({"A": 1.0, "B": 1.0})
    with pytest.raises(AssertionError):
        icd.portfolio_variance(weights, cov)
