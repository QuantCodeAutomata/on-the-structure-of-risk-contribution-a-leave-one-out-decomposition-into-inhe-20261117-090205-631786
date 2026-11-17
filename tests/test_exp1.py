"""Tests for exp/exp_1.py: the shared ICD pipeline applied to market data.

Uses the reduced market-data fixture (tests/conftest.py); skipped automatically
when DATALOADER_API_KEY is not set.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from exp import exp_1
from src import config, icd, portfolio


@pytest.mark.market_data
def test_build_portfolio_weights_sum_properties(reduced_price_panel):
    prices, returns, meta = reduced_price_panel
    tickers = list(returns.columns)
    as_of = returns.index[-1]
    weights = exp_1.build_portfolio_weights(tickers, returns, as_of)
    assert np.isclose(weights["Eq"].sum(), config.EQ_WEIGHT * len(tickers))
    assert np.isclose(weights["IV"].sum(), 1.0)
    for name in ("LS", "Eq", "IV"):
        assert set(weights[name].index) == set(tickers)


@pytest.mark.market_data
def test_single_day_tables_additivity_on_market_data(reduced_price_panel):
    prices, returns, meta = reduced_price_panel
    tickers = list(returns.columns)
    as_of = returns.index[-1]
    weights = exp_1.build_portfolio_weights(tickers, returns, as_of)
    window = min(config.COV_WINDOW_DAYS, len(returns) - 1)
    cov_by_date = portfolio.rolling_ewm_covariance(returns, window=window, alpha=config.COV_EWMA_ALPHA)
    cov_as_of = cov_by_date[sorted(cov_by_date)[-1]]
    last_date = sorted(cov_by_date)[-1]
    table2, table3, table4 = exp_1.single_day_tables(weights, cov_as_of, returns, last_date)
    for name in ("LS", "Eq", "IV"):
        sigma_p = icd.portfolio_vol(weights[name], cov_as_of)
        assert np.isclose(table2[name]["rc"].sum(), sigma_p)
    assert "XSR_Corr" in table4.columns and "MDD_pct" in table4.columns
    assert (table4["MDD_pct"] <= 0).all()


def test_time_varying_rc_uses_fixed_weights_varying_covariance():
    """Method 1: weights fixed across dates, only the covariance input changes."""
    tickers = ["CL1 Comdty", "NG1 Comdty", "ES1 Index"]
    weights = pd.Series({t: 1.0 / 3 for t in tickers})
    rng = np.random.default_rng(0)
    cov_a = pd.DataFrame(np.eye(3) * 1.0, index=tickers, columns=tickers)
    cov_b = pd.DataFrame(np.eye(3) * 4.0, index=tickers, columns=tickers)
    cov_by_date = {pd.Timestamp("2020-01-01"): cov_a, pd.Timestamp("2020-01-02"): cov_b}
    series = exp_1.time_varying_rc(weights, cov_by_date)
    assert len(series) == 2
    # Higher variance date must show a larger total RC for every asset class present.
    first, second = series.iloc[0], series.iloc[1]
    classes = sorted(series.columns.get_level_values(0).unique())
    for cls in classes:
        assert second[(cls, "rc")] > first[(cls, "rc")]


def test_crisis_attribution_shape():
    tickers = ["CL1 Comdty", "ES1 Index", "TY1 Comdty"]
    weights = pd.Series({t: 1.0 / 3 for t in tickers})
    dates = pd.bdate_range("2006-01-01", "2023-01-01")
    rng = np.random.default_rng(1)
    cov_by_date = {}
    for d in dates[::40]:  # sparse for test speed
        sigma = np.eye(3) + 0.1 * rng.normal(size=(3, 3))
        sigma = sigma @ sigma.T
        cov_by_date[d] = pd.DataFrame(sigma, index=tickers, columns=tickers)
    series = exp_1.time_varying_rc(weights, cov_by_date)
    table5 = exp_1.crisis_attribution({"TEST": series})
    assert {"episode", "portfolio", "asset_class", "delta_inh", "delta_corr"}.issubset(table5.columns)
