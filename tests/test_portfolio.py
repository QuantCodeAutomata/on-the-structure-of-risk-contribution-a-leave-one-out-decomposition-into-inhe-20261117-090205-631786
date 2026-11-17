"""Unit tests for src/portfolio.py covariance estimation and weight construction."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import config, portfolio


def test_exponential_weights_sum_to_one_and_decay():
    weights = portfolio.exponential_window_weights(10, 0.99)
    assert np.isclose(weights.sum(), 1.0)
    assert weights[0] > weights[-1]  # most recent observation (k=0) weighted highest


def test_rolling_ewm_covariance_window_length_and_no_lookahead():
    """Each covariance uses exactly `window` prior observations and no future data."""
    rng = np.random.default_rng(0)
    dates = pd.bdate_range("2020-01-01", periods=140)
    returns = pd.DataFrame(rng.normal(size=(140, 2)), index=dates, columns=["A", "B"])
    window = 126
    cov_by_date = portfolio.rolling_ewm_covariance(returns, window=window, alpha=0.99)
    assert len(cov_by_date) == 140 - window + 1
    first_date = sorted(cov_by_date)[0]
    assert first_date == dates[window - 1]
    # Perturbing a future observation must not change an earlier window's covariance.
    returns2 = returns.copy()
    returns2.iloc[window] += 1000.0
    cov_by_date2 = portfolio.rolling_ewm_covariance(returns2, window=window, alpha=0.99)
    pd.testing.assert_frame_equal(cov_by_date[first_date], cov_by_date2[first_date])


def test_inverse_volatility_weights_sum_to_one_and_rank():
    """Lower volatility gets a larger weight; weights sum to one (naive risk parity)."""
    vol_row = pd.Series({"A": 0.1, "B": 0.2, "C": 0.4})
    weights = portfolio.inverse_volatility_weights(vol_row)
    assert np.isclose(weights.sum(), 1.0)
    assert weights["A"] > weights["B"] > weights["C"]


def test_long_short_weights_apply_leverage():
    tickers = ["TY1 Comdty", "RX1 Comdty"]
    config.TABLE1_WEIGHTS["RX1 Comdty"] = config.TABLE1_WEIGHTS.get(
        "RX1 Comdty", {"asset_class": "Fixed Income", "ls_weight": -0.90}
    )
    w = portfolio.long_short_weights(tickers)
    assert np.isclose(w["TY1 Comdty"], 0.90 * config.LS_LEVERAGE)


def test_aggregate_by_asset_class_preserves_total():
    cov = pd.DataFrame(
        [[1.0, 0.1, 0.0], [0.1, 1.0, 0.0], [0.0, 0.0, 1.0]],
        index=["CL1 Comdty", "NG1 Comdty", "ES1 Index"],
        columns=["CL1 Comdty", "NG1 Comdty", "ES1 Index"],
    )
    weights = pd.Series({"CL1 Comdty": 0.3, "NG1 Comdty": 0.3, "ES1 Index": 0.4})
    from src import icd

    decomposed = icd.icd_decompose(weights, cov)
    grouped = portfolio.aggregate_by_asset_class(decomposed)
    assert np.isclose(grouped["rc"].sum(), decomposed["rc"].sum())


def test_inverse_volatility_weights_rejects_nonpositive():
    with pytest.raises(AssertionError):
        portfolio.inverse_volatility_weights(pd.Series({"A": 0.0, "B": 0.1}))
