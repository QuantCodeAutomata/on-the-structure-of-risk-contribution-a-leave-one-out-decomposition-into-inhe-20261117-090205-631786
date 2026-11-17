"""Paper-derived parameters for the Inherent and Correlation Decomposition (ICD).

All experiment parameters live here as module-level UPPER_CASE variables.
Each has a comment giving its meaning, unit and source (the paper's section,
or "not specified in the paper").

Paper: Alexander & Fabozzi, "On the Structure of Risk Contribution: A
Leave-One-Out Decomposition into Inherent and Correlation Risk".
"""

# ---------------------------------------------------------------------------
# Shared ICD estimation parameters (Section 5, "An Application to Portfolios")
# ---------------------------------------------------------------------------
COV_WINDOW_DAYS = 126  # business days in the rolling covariance window (Sec. 5)
COV_EWMA_ALPHA = 0.99  # exponential-weight decay parameter for the rolling covariance (Sec. 5)
IV_VOL_WINDOW_DAYS = 126  # trailing window (business days) for the Inverse-Volatility
# portfolio's "trailing six-month volatility" (Sec. 5); the paper names the window
# "six months" but does not give an exact day count, so the same 126-business-day
# convention used for the covariance window is applied (assumed).
LS_LEVERAGE = 10.0  # Long-Short portfolio leverage multiplier on Table 1 pre-leverage weights (Sec. 5)
EQ_WEIGHT = 0.08  # Equal-Weight portfolio weight applied to every included position (Table 1)

# ---------------------------------------------------------------------------
# Experiment 1: Empirical application to multi-asset portfolios
# ---------------------------------------------------------------------------
SINGLE_DAY_DATE = "2025-08-01"  # single-day analysis date for Tables 2-4 (Sec. 5.1)
SAMPLE_START_PAPER = "1990-01-01"  # paper's sample start, Bloomberg futures/FX data (Sec. 5)
SAMPLE_END_PAPER = "2025-08-01"  # paper's sample end (Sec. 5)

# Realized sample actually used: Bloomberg terminal access is unavailable, and the
# permitted data sources (QuantX Dataloader / Massive REST, with Yahoo Finance as
# the Dataloader's documented backstop) do not serve continuous futures series at
# all under the available entitlement (Massive's /futures/v1 routes returned
# NOT_AUTHORIZED for every queried product) and cover the FX and commodity/bond ETF
# proxies only from the dates logged by data/data_loader.py. The realized window is
# fixed in exp/exp_1.py from the loaded panel and reported in results/RESULTS.md.
SAMPLE_START_RUN = "2007-04-18"  # earliest date common to all nine substituted tickers (see data/data_loader.py)
SAMPLE_END_RUN = "2025-08-01"

# Table 1 pre-leverage weights, by Bloomberg ticker (Sec. 5, Table 1). Each row is
# (asset_class, ls_pre_leverage_weight, eq_weight). The IV column of Table 1 is a
# snapshot of the dynamically-computed Inverse-Volatility weight on SINGLE_DAY_DATE,
# not a static input, so it is not stored here: IV weights are always recomputed
# from trailing volatility (Sec. 5, "Portfolio Construction").
TABLE1_WEIGHTS = {
    "CL1 Comdty": {"asset_class": "Commodity", "ls_weight": -0.05},
    "NG1 Comdty": {"asset_class": "Commodity", "ls_weight": 0.05},
    "C 1 Comdty": {"asset_class": "Commodity", "ls_weight": -0.10},
    "ES1 Index": {"asset_class": "Equity", "ls_weight": 0.05},
    "CF1 Index": {"asset_class": "Equity", "ls_weight": -0.20},
    "XU1 Index": {"asset_class": "Equity", "ls_weight": 0.10},
    "TY1 Comdty": {"asset_class": "Fixed Income", "ls_weight": 0.90},
    "RX1 Comdty": {"asset_class": "Fixed Income", "ls_weight": -0.90},
    "JB1 Comdty": {"asset_class": "Fixed Income", "ls_weight": 0.80},
    "CADUSD Curncy": {"asset_class": "FX", "ls_weight": 0.10},
    "EURUSD Curncy": {"asset_class": "FX", "ls_weight": 0.15},
    "JPYUSD Curncy": {"asset_class": "FX", "ls_weight": 0.10},
}

# Substituted tradable tickers used in place of the Bloomberg generic futures/FX
# series, with the proxy's rationale. XU1 Index (Borsa Istanbul BIST 100 futures),
# RX1 Comdty (Euro-Bund futures) and JB1 Comdty (JGB futures) have no continuous
# futures series available through the Dataloader/Massive stack under the available
# entitlement and no liquid, long-history ETF proxy was found (see
# results/RESULTS.md, "Deviations from the paper"); they are excluded from the
# realized universe. The remaining nine positions are mapped to the most liquid
# available ETF with the same economic exposure:
TICKER_PROXIES = {
    "CL1 Comdty": "USO",   # United States Oil Fund (WTI crude front-month proxy)
    "NG1 Comdty": "UNG",   # United States Natural Gas Fund
    "C 1 Comdty": "DBA",   # Invesco DB Agriculture Fund (broad grains/softs proxy; no
    # continuous-corn ETF covers the pre-2010 period, see RESULTS.md)
    "ES1 Index": "SPY",    # SPDR S&P 500 ETF Trust
    "CF1 Index": "EWQ",    # iShares MSCI France ETF (CAC 40-linked exposure proxy)
    "TY1 Comdty": "IEF",   # iShares 7-10 Year Treasury Bond ETF (US 10Y note proxy)
    "CADUSD Curncy": "FXC",  # Invesco CurrencyShares Canadian Dollar Trust
    "EURUSD Curncy": "FXE",  # Invesco CurrencyShares Euro Trust
    "JPYUSD Curncy": "FXY",  # Invesco CurrencyShares Japanese Yen Trust
}
EXCLUDED_TICKERS = ["XU1 Index", "RX1 Comdty", "JB1 Comdty"]

# Five crisis episodes for the attribution analysis (Table 5, Sec. 5.3). The paper
# names the episodes but does not give exact start/end dates for the pre-crisis and
# crisis windows, so the following calendar windows are used (assumed) and reported
# as such in results/RESULTS.md. The Pre-GFC pre-crisis window is bounded below by
# SAMPLE_START_RUN because no earlier data is available under the realized sample.
CRISIS_EPISODES = {
    "Pre-GFC (2007)": {
        "pre_crisis": ("2007-04-18", "2007-07-31"),
        "crisis": ("2007-10-01", "2007-12-31"),
    },
    "GFC Peak (2008-09)": {
        "pre_crisis": ("2008-01-01", "2008-06-30"),
        "crisis": ("2008-09-01", "2009-03-31"),
    },
    "European Debt (2011-12)": {
        "pre_crisis": ("2010-07-01", "2010-12-31"),
        "crisis": ("2011-07-01", "2012-06-30"),
    },
    "Covid (2020)": {
        "pre_crisis": ("2019-07-01", "2019-12-31"),
        "crisis": ("2020-02-15", "2020-04-30"),
    },
    "Fed Tightening (2022)": {
        "pre_crisis": ("2021-07-01", "2021-12-31"),
        "crisis": ("2022-03-01", "2022-12-31"),
    },
}

# ---------------------------------------------------------------------------
# Experiment 2: Convergence of RC and its components (Appendix B)
# ---------------------------------------------------------------------------
N_ASSETS = 5  # number of synthetic Gaussian assets (Appendix B)
COV_DIAG = 1.0  # diagonal (variance) of the simulation covariance matrix Sigma (App. B)
COV_OFFDIAG = 0.5  # off-diagonal (covariance) of Sigma (App. B)
PORTFOLIO_WEIGHT = 1.0  # gross weight per asset ("equal-weighted portfolio", Appendix B).
# The paper reports population targets Total RC = 4.3, Inh = 1.1, Corr = 3.3 for
# Sigma with unit diagonal and 0.5 off-diagonal. Weights normalized to sum to one
# (w_i = 1/5) give sigma_p = 0.774, far from 4.3; w_i = 1 gives sigma_p = 3.87,
# RC_inh = 1.29, RC_corr = 2.58 (eq. 10), the closest integer gross weight to the
# reported figure, so it is used here (assumed; the paper calls this the
# "equal-weighted portfolio" without stating the normalization). The Inh/Total
# ratio is invariant to the common scale factor for this symmetric Sigma, so no
# integer or fractional uniform weight reproduces the paper's exact Inh/Total
# ratio (1.1/4.3 = 0.256 versus 1.29/3.87 = 0.333); see results/RESULTS.md.
MAX_SAMPLE_SIZE = 450  # maximum simulated sample size T (Appendix B)
MIN_WINDOW_SIZE = 5  # expanding window starts at 5 days (Appendix B)
N_BOOTSTRAP_PAPER = 100  # paper's bootstrap replication count (Appendix B)
N_BOOTSTRAP_RUN = 100  # replications actually executed (unchanged, inexpensive)
RANDOM_SEED = 42  # not specified in the paper; fixed here for reproducibility
