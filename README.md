# On the Structure of Risk Contribution: A Leave-One-Out Decomposition into Inherent and Correlation Risk

Replication of two experiments from:

Nolan Alexander and Frank Fabozzi, "On the Structure of Risk Contribution: A
Leave-One-Out Decomposition into Inherent and Correlation Risk," arXiv:2604.10375.

The paper decomposes Risk Contribution (RC) of a position in a portfolio into
an **inherent** component (the position's own scaled variance) and a
**correlation** component (its covariance with the rest of the portfolio),
called the Inherent and Correlation Decomposition (ICD). This repository
implements the decomposition and reproduces:

* **Experiment 1** ("Empirical Application of Inherent and Correlation
  Decomposition to Multi-Asset Portfolios", Sec. 5): ICD applied to three
  multi-asset portfolios (Long-Short, Equal-Weight, Inverse-Volatility) on a
  single day (Tables 2-4) and over time across market regimes (Figures 2-5,
  Table 5 crisis attribution).
* **Experiment 2** ("Convergence of RC and Its Components Simulation",
  Appendix B): a stylized simulation studying the estimation convergence of
  RC and its two components under an expanding-window sample covariance
  (Figure 6).

## Repository layout

```
src/            ICD formulas (src/icd.py), covariance estimation and portfolio
                construction (src/portfolio.py), all parameters (src/config.py)
exp/            exp_1.py (multi-asset portfolios), exp_2.py (convergence simulation)
data/           data_loader.py (QuantX Dataloader REST client),
                generate_synthetic.py (Appendix B synthetic returns)
tests/          pytest unit and market-data tests
results/        tables, figures and RESULTS.md with the paper comparison
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATALOADER_API_KEY and MASSIVE_API_KEY for Experiment 1
```

Experiment 2 uses only synthetic data and needs no API keys.

## Running the tests

```bash
python -m pytest -m "not market_data"     # unit tests, no network access
python -m pytest                           # also runs the market-data tests (needs API keys)
```

## Running the experiments

```bash
python -m exp.exp_1   # Experiment 1: multi-asset ICD application (needs API keys)
python -m exp.exp_2   # Experiment 2: convergence simulation (synthetic data only)
```

`reproduce.sh` runs the full sequence (tests, then both experiments).

## Data

Experiment 1 requires daily price history for the paper's twelve instruments.
Price history is loaded only through the QuantX Dataloader REST API
(`data/data_loader.py`), following the `massive-rest-market-data` convention.
The paper's series are continuous Bloomberg generic futures (`CL1 Comdty`,
`TY1 Comdty`, etc.) rolled with the Bloomberg code `N:05_0_R`; no public
provider reachable from this environment serves that continuous-futures roll,
so each instrument is replaced by the most liquid, long-history, exchange-
traded proxy with the same economic exposure (for example `IEF` for the U.S.
10-year note future `TY1 Comdty`). Three positions with no adequate proxy
(`XU1 Index`, `RX1 Comdty`, `JB1 Comdty`) are excluded from the realized
universe. See `results/RESULTS.md`, "Deviations from the paper", for the full
mapping, the excluded instruments, and the realized sample period.

Experiment 2 uses only synthetic Gaussian returns generated in
`data/generate_synthetic.py`; no market data or API keys are required.

## Results

See `results/RESULTS.md` for the comparison of every reproduced table and
figure against the paper's reported values, with a verdict for each metric,
and the "Deviations from the paper" and "Not reproduced" sections.
