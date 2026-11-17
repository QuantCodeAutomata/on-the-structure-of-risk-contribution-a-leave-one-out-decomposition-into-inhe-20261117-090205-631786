"""Covariance estimation and portfolio construction (paper Sec. 5).

Custom implementation: the paper's covariance estimator combines a *fixed-length*
rolling window with exponential weights inside that window. This is not the
unbounded-history EWMA covariance produced by ``pandas.DataFrame.ewm(...).cov()``
(which never drops old observations), so it is implemented directly with numpy
as described in Section 5, "Covariance Estimation": a 126-business-day rolling
window with exponential weights (alpha = 0.99).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


def exponential_window_weights(window: int, alpha: float) -> np.ndarray:
    """Normalized exponential weights for a window of length ``window``.

    Weight of the k-th most recent observation (k=0 is the most recent) is
    proportional to alpha^k, normalized to sum to one, so more recent returns
    receive a larger weight (alpha = 0.99 close to equal weighting, Sec. 5).
    """
    assert 0 < alpha <= 1, "alpha must be in (0, 1]"
    k = np.arange(window)
    raw = alpha**k  # k=0 (most recent) -> weight 1, decaying backward
    return raw / raw.sum()


def rolling_ewm_covariance(
    returns: pd.DataFrame, window: int = config.COV_WINDOW_DAYS, alpha: float = config.COV_EWMA_ALPHA
) -> dict[pd.Timestamp, pd.DataFrame]:
    """Covariance matrix ending at each date, over the trailing ``window`` returns.

    For dates with fewer than ``window`` prior observations, no covariance is
    produced (first estimate uses exactly ``window`` returns, preventing
    look-ahead and matching "126-business-day rolling window", Sec. 5).

    Returns a dict mapping the window's *last* date to a covariance DataFrame
    indexed/columned by asset ticker. Assumes zero-mean daily returns, as in
    the paper's $r_t \\sim N(0, \\Sigma)$ formulation (Appendix B).
    """
    assert len(returns) >= window, "need at least `window` observations"
    tickers = returns.columns
    values = returns.to_numpy()
    weights = exponential_window_weights(window, alpha)[::-1]  # oldest..newest
    covariances: dict[pd.Timestamp, pd.DataFrame] = {}
    for end in range(window - 1, len(values)):
        chunk = values[end - window + 1 : end + 1]  # oldest..newest, length `window`
        weighted_chunk = chunk * weights[:, None]
        cov_matrix = weighted_chunk.T @ chunk  # zero-mean weighted covariance
        covariances[returns.index[end]] = pd.DataFrame(cov_matrix, index=tickers, columns=tickers)
    return covariances


def trailing_volatility(returns: pd.DataFrame, window: int = config.IV_VOL_WINDOW_DAYS) -> pd.DataFrame:
    """Trailing realized volatility per asset over ``window`` business days.

    Uses only past and current observations at each date (``rolling(window)``
    on a sorted index), preventing look-ahead.
    """
    return returns.rolling(window).std()


def inverse_volatility_weights(vol_row: pd.Series) -> pd.Series:
    """Naive-risk-parity weights: w_i = (1/vol_i) / sum_j(1/vol_j) (Sec. 5).

    Normalized to sum to one, long-only, matching Table 1's IV column summing
    to approximately one across the paper's twelve positions.
    """
    assert (vol_row > 0).all(), "volatilities must be strictly positive"
    inv_vol = 1.0 / vol_row
    return inv_vol / inv_vol.sum()


def long_short_weights(tickers: list[str]) -> pd.Series:
    """Long-Short portfolio weights: Table 1 pre-leverage weight times LS_LEVERAGE."""
    w = pd.Series(
        {t: config.TABLE1_WEIGHTS[t]["ls_weight"] * config.LS_LEVERAGE for t in tickers}
    )
    return w


def equal_weights(tickers: list[str]) -> pd.Series:
    """Equal-Weight portfolio weights: EQ_WEIGHT applied uniformly (Table 1)."""
    return pd.Series({t: config.EQ_WEIGHT for t in tickers})


def asset_class_of(ticker: str) -> str:
    """Asset-class label for a Bloomberg ticker, from Table 1."""
    return config.TABLE1_WEIGHTS[ticker]["asset_class"]


def aggregate_by_asset_class(icd_table: pd.DataFrame) -> pd.DataFrame:
    """Sum RC, RC_inh and RC_corr by asset class (Table 3 layout, Sec. 5.1)."""
    classes = pd.Series({t: asset_class_of(t) for t in icd_table.index}, name="asset_class")
    grouped = icd_table[["rc", "rc_inh", "rc_corr"]].groupby(classes).sum()
    return grouped
