"""Experiment 2: convergence of RC and its components (paper Appendix B).

Simulates five i.i.d. Gaussian assets, estimates Total RC, Total Inherent RC
and Total Correlation RC with an expanding-window sample covariance, bootstraps
100 times, and plots the median and 5th-95th percentile bands against the
analytic population targets (Figure 6).

Run as ``python -m exp.exp_2``.
"""
from __future__ import annotations

import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data.generate_synthetic import build_covariance, simulate_returns
from src import config, icd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RESULTS_DIR = "results"


def population_targets(sigma: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    """Analytic population Total RC, Inh and Corr: sigma_p, RC_inh, RC_corr."""
    sigma_p = float(np.sqrt(weights @ sigma @ weights))
    rc_inh = float(np.sum((weights**2) * np.diag(sigma)) / sigma_p)
    rc_corr = sigma_p - rc_inh
    return {"total_rc": sigma_p, "total_inh": rc_inh, "total_corr": rc_corr}


def expanding_window_estimates(
    returns: np.ndarray, weights: np.ndarray, min_window: int
) -> pd.DataFrame:
    """Total RC, Inh and Corr from an expanding-window sample covariance.

    Uses running sums of returns and of outer products so the T-th sample
    covariance (ddof=1, demeaned) is obtained in O(1) per step instead of
    recomputing from scratch (custom implementation, paper Appendix B).
    """
    n_obs, n_assets = returns.shape
    cum_x = np.cumsum(returns, axis=0)
    outer = np.einsum("ti,tj->tij", returns, returns)
    cum_xx = np.cumsum(outer, axis=0)

    rows = []
    for t in range(min_window, n_obs + 1):
        mean = cum_x[t - 1] / t
        cov = (cum_xx[t - 1] - t * np.outer(mean, mean)) / (t - 1)
        cov_df = pd.DataFrame(cov)
        w = pd.Series(weights)
        sigma_p = icd.portfolio_vol(w, cov_df)
        rc_inh_total = float(np.sum((weights**2) * np.diag(cov)) / sigma_p)
        rc_corr_total = sigma_p - rc_inh_total
        rows.append({"T": t, "total_rc": sigma_p, "total_inh": rc_inh_total, "total_corr": rc_corr_total})
    return pd.DataFrame(rows).set_index("T")


def run_bootstrap(
    n_bootstrap: int, max_sample: int, min_window: int, sigma: np.ndarray, weights: np.ndarray, seed: int
) -> dict[str, pd.DataFrame]:
    """Bootstrap ``n_bootstrap`` independent simulations; return raw draws per metric."""
    rng = np.random.default_rng(seed)
    metrics = ["total_rc", "total_inh", "total_corr"]
    draws = {m: np.empty((n_bootstrap, max_sample - min_window + 1)) for m in metrics}
    for b in range(n_bootstrap):
        returns = simulate_returns(max_sample, sigma, rng)
        estimates = expanding_window_estimates(returns, weights, min_window)
        for m in metrics:
            draws[m][b] = estimates[m].to_numpy()
    index = pd.RangeIndex(min_window, max_sample + 1, name="T")
    return {m: pd.DataFrame(draws[m], columns=index) for m in metrics}


def summarize(draws: pd.DataFrame) -> pd.DataFrame:
    """Median and 5th/95th percentile bands across bootstrap replications, per T."""
    return pd.DataFrame({
        "median": draws.median(axis=0),
        "p05": draws.quantile(0.05, axis=0),
        "p95": draws.quantile(0.95, axis=0),
    })


def plot_convergence(summaries: dict[str, pd.DataFrame], targets: dict[str, float], path: str) -> None:
    """Figure 6: confidence bands and median vs window size, with population targets."""
    labels = {"total_rc": "Total RC", "total_inh": "Total Inherent RC", "total_corr": "Total Correlation RC"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharex=True)
    for ax, (key, summary) in zip(axes, summaries.items()):
        ax.plot(summary.index, summary["median"], color="tab:blue", label="Median")
        ax.fill_between(summary.index, summary["p05"], summary["p95"], color="tab:blue", alpha=0.25, label="5th-95th pct")
        ax.axhline(targets[key], color="black", linestyle="--", label="Population target")
        ax.set_title(labels[key])
        ax.set_xlabel("Expanding window size T (days)")
    axes[0].set_ylabel("Estimate")
    axes[0].legend(fontsize=8)
    fig.suptitle("Convergence of RC and its components under expanding-window estimation (Appendix B)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    sigma = build_covariance()
    weights = np.full(config.N_ASSETS, config.PORTFOLIO_WEIGHT)
    targets = population_targets(sigma, weights)
    logger.info("Population targets: %s", targets)

    draws = run_bootstrap(
        config.N_BOOTSTRAP_RUN, config.MAX_SAMPLE_SIZE, config.MIN_WINDOW_SIZE, sigma, weights, config.RANDOM_SEED
    )
    summaries = {m: summarize(d) for m, d in draws.items()}
    for m, summary in summaries.items():
        summary.to_csv(f"{RESULTS_DIR}/exp2_convergence_{m}.csv")
    logger.info("Saved convergence summaries to results/")

    plot_convergence(summaries, targets, f"{RESULTS_DIR}/exp2_figure6_convergence.png")
    logger.info("Saved Figure 6 to results/exp2_figure6_convergence.png")

    band_width_at_125 = {
        m: float(summaries[m].loc[125, "p95"] - summaries[m].loc[125, "p05"]) for m in summaries
    }
    band_width_at_t5 = {
        m: float(summaries[m].loc[config.MIN_WINDOW_SIZE, "p95"] - summaries[m].loc[config.MIN_WINDOW_SIZE, "p05"])
        for m in summaries
    }
    summary_record = {
        "population_targets": targets,
        "n_bootstrap": config.N_BOOTSTRAP_RUN,
        "max_sample_size": config.MAX_SAMPLE_SIZE,
        "band_width_at_T5": band_width_at_t5,
        "band_width_at_T125": band_width_at_125,
    }
    pd.Series(summary_record).to_json(f"{RESULTS_DIR}/exp2_run_summary.json", indent=2)
    logger.info("Experiment 2 complete: %s", summary_record)


if __name__ == "__main__":
    main()
