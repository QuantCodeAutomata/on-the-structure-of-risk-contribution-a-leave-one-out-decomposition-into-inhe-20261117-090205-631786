"""Experiment 1: ICD applied to three multi-asset portfolios (paper Sec. 5).

Builds the Long-Short (LS), Equal-Weight (Eq) and Inverse-Volatility (IV)
portfolios from the proxied instrument panel, and reproduces:
  * Table 2 - RC, RC_inh, RC_corr by position, single day (Sec. 5.1)
  * Table 3 - RC aggregated by asset class, single day (Sec. 5.1)
  * Table 4 - XSR correlation, iVol and MDD for the LS portfolio (Sec. 5.1)
  * Figures 2-5 - time-varying RC by asset class, Method 1 (Sec. 5.2)
  * Table 5 - crisis-episode attribution of inherent/correlation RC (Sec. 5.3)

Run as ``python -m exp.exp_1``.
"""
from __future__ import annotations

import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from data.data_loader import load_price_panel
from src import config, icd, portfolio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RESULTS_DIR = "results"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load the proxied instrument panel and log realized coverage."""
    prices, returns, meta = load_price_panel(
        config.TICKER_PROXIES, config.SAMPLE_START_PAPER, config.SAMPLE_END_RUN
    )
    logger.info(
        "Loaded %d rows, %d tickers, %s to %s", len(returns), returns.shape[1],
        returns.index.min().date(), returns.index.max().date(),
    )
    logger.info("ticker_details sources: %s", meta["non_massive_source"])
    return prices, returns, meta


def build_portfolio_weights(
    tickers: list[str], returns: pd.DataFrame, as_of: pd.Timestamp
) -> dict[str, pd.Series]:
    """LS, Eq and IV weights, the latter from trailing volatility as of ``as_of``."""
    vol = portfolio.trailing_volatility(returns, config.IV_VOL_WINDOW_DAYS)
    vol_row = vol.loc[as_of]
    weights = {
        "LS": portfolio.long_short_weights(tickers),
        "Eq": portfolio.equal_weights(tickers),
        "IV": portfolio.inverse_volatility_weights(vol_row),
    }
    return weights


def single_day_tables(
    weights: dict[str, pd.Series], cov: pd.DataFrame, returns: pd.DataFrame, as_of: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Tables 2, 3 and 4 for the single-day analysis date (Sec. 5.1)."""
    table2 = {}
    table3 = {}
    for name, w in weights.items():
        decomposed = icd.icd_decompose(w, cov)
        table2[name] = decomposed
        table3[name] = portfolio.aggregate_by_asset_class(decomposed)

    table2_df = pd.concat(table2, axis=1)
    table3_df = pd.concat(table3, axis=1)

    ls_weights = weights["LS"]
    xsr = icd.xsr_correlation(ls_weights, cov)
    ivol = icd.incremental_vol(ls_weights, cov)
    cum_index = (1.0 + returns.loc[:as_of]).cumprod()
    mdd = cum_index.apply(icd.max_drawdown)
    table4_df = pd.DataFrame({"XSR_Corr": xsr, "iVol": ivol, "MDD_pct": mdd})
    return table2_df, table3_df, table4_df


def time_varying_rc(
    fixed_weights: pd.Series, cov_by_date: dict[pd.Timestamp, pd.DataFrame]
) -> pd.DataFrame:
    """Method 1: RC by asset class over time, current (fixed) weights, rolling covariance.

    Returns a DataFrame indexed by covariance date, with MultiIndex columns
    (asset_class, {'rc', 'rc_inh', 'rc_corr'}).
    """
    rows = {}
    for date, cov in cov_by_date.items():
        decomposed = icd.icd_decompose(fixed_weights, cov)
        rows[date] = portfolio.aggregate_by_asset_class(decomposed).stack()
    out = pd.DataFrame(rows).T
    out.index.name = "date"
    out = out.sort_index()
    return out


def plot_time_varying(series: pd.DataFrame, portfolio_name: str, path: str) -> None:
    """One figure per portfolio: RC_inh and RC_corr by asset class over time."""
    classes = sorted(series.columns.get_level_values(0).unique())
    fig, axes = plt.subplots(len(classes), 1, figsize=(10, 2.6 * len(classes)), sharex=True)
    if len(classes) == 1:
        axes = [axes]
    for ax, cls in zip(axes, classes):
        ax.plot(series.index, series[(cls, "rc_inh")], label="Inherent RC", color="tab:blue")
        ax.plot(series.index, series[(cls, "rc_corr")], label="Correlation RC", color="tab:red")
        ax.plot(series.index, series[(cls, "rc")], label="Total RC", color="black", linestyle="--", linewidth=0.8)
        ax.set_title(cls)
        ax.axhline(0, color="grey", linewidth=0.5)
        ax.legend(fontsize=7, loc="upper left")
    axes[-1].set_xlabel("Covariance date")
    fig.suptitle(f"Time-varying RC decomposition by asset class - {portfolio_name} portfolio (Method 1)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def crisis_attribution(series_by_portfolio: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Table 5: average inherent/correlation RC in pre-crisis vs crisis windows."""
    rows = []
    for episode, windows in config.CRISIS_EPISODES.items():
        pre_start, pre_end = windows["pre_crisis"]
        crisis_start, crisis_end = windows["crisis"]
        for pf_name, series in series_by_portfolio.items():
            classes = sorted(series.columns.get_level_values(0).unique())
            for cls in classes:
                pre = series.loc[pre_start:pre_end, (cls, ["rc_inh", "rc_corr"])].mean()
                crisis = series.loc[crisis_start:crisis_end, (cls, ["rc_inh", "rc_corr"])].mean()
                if pre.isna().all() or crisis.isna().all():
                    continue
                rows.append({
                    "episode": episode, "portfolio": pf_name, "asset_class": cls,
                    "pre_inh": pre[(cls, "rc_inh")], "crisis_inh": crisis[(cls, "rc_inh")],
                    "delta_inh": crisis[(cls, "rc_inh")] - pre[(cls, "rc_inh")],
                    "pre_corr": pre[(cls, "rc_corr")], "crisis_corr": crisis[(cls, "rc_corr")],
                    "delta_corr": crisis[(cls, "rc_corr")] - pre[(cls, "rc_corr")],
                })
    return pd.DataFrame(rows)


def main() -> None:
    prices, returns, meta = load_data()
    tickers = list(returns.columns)

    as_of = pd.Timestamp(config.SINGLE_DAY_DATE)
    if as_of not in returns.index:
        as_of = returns.index[returns.index <= as_of][-1]
    logger.info("Single-day analysis date: %s", as_of.date())

    weights = build_portfolio_weights(tickers, returns, as_of)

    cov_by_date = portfolio.rolling_ewm_covariance(returns, config.COV_WINDOW_DAYS, config.COV_EWMA_ALPHA)
    cov_as_of = cov_by_date[as_of]

    table2, table3, table4 = single_day_tables(weights, cov_as_of, returns, as_of)
    table2.to_csv(f"{RESULTS_DIR}/exp1_table2_rc_by_position.csv")
    table3.to_csv(f"{RESULTS_DIR}/exp1_table3_rc_by_asset_class.csv")
    table4.to_csv(f"{RESULTS_DIR}/exp1_table4_xsr_ivol_mdd.csv")
    logger.info("Saved Tables 2-4 to results/")

    series_by_portfolio = {}
    for name, w in weights.items():
        series = time_varying_rc(w, cov_by_date)
        series_by_portfolio[name] = series
        series.to_csv(f"{RESULTS_DIR}/exp1_timevarying_{name}.csv")
        plot_time_varying(series, name, f"{RESULTS_DIR}/exp1_figure_{name}_timevarying.png")
    logger.info("Saved time-varying series and figures to results/")

    table5 = crisis_attribution(series_by_portfolio)
    table5.to_csv(f"{RESULTS_DIR}/exp1_table5_crisis_attribution.csv", index=False)
    logger.info("Saved Table 5 (crisis attribution) to results/")

    summary = {
        "n_obs": len(returns), "n_tickers": len(tickers),
        "sample_start": str(returns.index.min().date()), "sample_end": str(returns.index.max().date()),
        "single_day_date": str(as_of.date()),
        "excluded_tickers": config.EXCLUDED_TICKERS,
        "non_massive_source": meta["non_massive_source"],
    }
    pd.Series(summary).to_json(f"{RESULTS_DIR}/exp1_run_summary.json", indent=2)
    logger.info("Experiment 1 complete: %s", summary)


if __name__ == "__main__":
    main()
