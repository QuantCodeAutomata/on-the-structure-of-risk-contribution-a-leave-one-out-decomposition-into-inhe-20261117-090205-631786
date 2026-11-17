# AGENTS.md

Guide for coding agents and contributors working in this repository.

## What this repository implements

A reproduction of two experiments from Nolan Alexander and Frank Fabozzi,
"On the Structure of Risk Contribution: A Leave-One-Out Decomposition into
Inherent and Correlation Risk" (arXiv:2604.10375):

* **Experiment 1** (Sec. 5, "An Application to Portfolios"): the Inherent and
  Correlation Decomposition (ICD) of Risk Contribution applied to three
  multi-asset portfolios (Long-Short, Equal-Weight, Inverse-Volatility),
  reproducing Tables 2-5 and Figures 2-5.
* **Experiment 2** (Appendix B, "Convergence of RC and Its Components"): a
  synthetic-data simulation of the point-estimator convergence of total RC
  and its inherent/correlation components, reproducing Figure 6.

## Layout

```
src/        ICD formulas, covariance/portfolio construction, config (flat modules)
exp/        exp_1.py and exp_2.py, run as `python -m exp.<name>`
data/       data_loader.py (QuantX Dataloader market data) and
            generate_synthetic.py (Experiment 2's synthetic returns)
tests/      pytest suite for src/ and exp/
results/    tables, figures and RESULTS.md written by the experiments
```

Library code lives only in flat modules under `src/`; experiment scripts only
in `exp/`; all tests only in `tests/`. Parameters live only in
`src/config.py` as module-level `UPPER_CASE` variables with a source comment
(paper section/equation, or "not specified in the paper"); never duplicate
them inside `exp/` or `src/icd.py`/`src/portfolio.py`. Market data is loaded
only through `data/data_loader.py`; synthetic data for Experiment 2 is
generated only through `data/generate_synthetic.py`. Downloaded market data
is never committed (see `.gitignore`: `data/cache/`).

## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env   # fill in DATALOADER_API_KEY and MASSIVE_API_KEY
```

Both keys are read from the environment with `load_dotenv()` in
`data/data_loader.py` and used only in requests to the QuantX Dataloader and
Massive APIs. Experiment 2 uses only synthetic data and needs no keys.

## Tests

```bash
python -m pytest -m "not market_data" -q   # unit tests, no network access
python -m pytest -m market_data -q         # needs DATALOADER_API_KEY / MASSIVE_API_KEY
python -m pytest -q                        # full suite
```

`market_data` tests (registered in `tests/conftest.py`) load a reduced slice
of the Experiment 1 universe once per session and cache it; they are skipped
automatically when `DATALOADER_API_KEY` is absent.

## Experiments

```bash
python -m exp.exp_1     # Experiment 1: needs DATALOADER_API_KEY / MASSIVE_API_KEY
python -m exp.exp_2      # Experiment 2: synthetic data only
```

`python -m exp.exp_1 --full` runs the paper's full 1990-2025 window and
twelve-instrument universe (see "Deviations from the paper" in
`results/RESULTS.md` for why the default run uses a reduced universe and
window). `reproduce.sh` runs the test suite and both experiments with these
same commands and overwrites every file in `results/`.

## Conventions

* All experiment parameters live in `src/config.py`; no parameter is
  hard-coded inside `src/` or `exp/`.
* `src/icd.py` and `src/portfolio.py` are the single shared implementation of
  the ICD formulas, covariance estimation and portfolio construction; both
  experiments call the same functions with the same argument names and
  return keys.
* After rerunning the experiment commands, every file in `results/` is
  overwritten; the prose, numbers and verdicts in `results/RESULTS.md` are
  not regenerated automatically and must be checked against the new files
  and updated by hand.
* Never commit API keys, `.env`, or files under `data/cache/`.
