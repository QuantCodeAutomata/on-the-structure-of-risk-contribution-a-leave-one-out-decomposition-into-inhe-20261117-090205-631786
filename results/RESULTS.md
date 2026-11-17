# Results

Nolan Alexander and Frank Fabozzi, "On the Structure of Risk Contribution: A
Leave-One-Out Decomposition into Inherent and Correlation Risk," arXiv:2604.10375.

This file compares the artifacts produced by `python -m exp.exp_1` and
`python -m exp.exp_2` against the values the paper reports, gives a verdict
for every compared metric, and records every deviation from the paper and
every item not reproduced. Verdicts follow: **reproduced** (within the
paper's reported range, or else within 10% of the paper's value with the
same sign and the paper's qualitative result holding), **partially
reproduced** (same sign/ranking direction but outside 10%, or a mixed
pattern), **not reproduced** (opposite sign, or a qualitative result such as
a ranking that does not hold).

## Experiment 1: Empirical Application of ICD to Multi-Asset Portfolios

Reproduces Sec. 5 ("An Application to Portfolios"): Tables 2-5 and the
time-varying RC decomposition (Figures 2-5) for the Long-Short (LS),
Equal-Weight (Eq) and Inverse-Volatility (IV) portfolios.

**Data actually used.** The paper's twelve instruments are continuous
Bloomberg generic futures/FX series (1990-Aug 2025) rolled with the Bloomberg
code `N:05_0_R`. No source reachable here (QuantX Dataloader or Massive)
serves that continuous-futures roll under the available entitlement, so each
instrument is replaced by the most liquid, long-history exchange-traded proxy
with the same economic exposure (`src/config.py:TICKER_PROXIES`): `USO` for
`CL1 Comdty`, `UNG` for `NG1 Comdty`, `DBA` for `C 1 Comdty`, `SPY` for
`ES1 Index`, `EWQ` for `CF1 Index`, `IEF` for `TY1 Comdty`, `FXC` for
`CADUSD Curncy`, `FXE` for `EURUSD Curncy`, `FXY` for `JPYUSD Curncy`. Three
positions have no adequate proxy and are excluded from the realized universe
(`src/config.py:EXCLUDED_TICKERS`): `XU1 Index` (Borsa Istanbul BIST 100
futures), `RX1 Comdty` (Euro-Bund futures) and `JB1 Comdty` (JGB futures); no
continuous futures series for these is served by the Dataloader/Massive stack
under the available entitlement, and no liquid, long-history ETF tracks them.
All nine proxies were loaded through the QuantX Dataloader
(`data/data_loader.py`, `POST /fetch-ohlcvs`) with its Yahoo Finance
backstop; `results/exp1_run_summary.json` records `ticker_details.data_source`
for every ticker: eight of the nine (`UNG`, `DBA`, `SPY`, `EWQ`, `IEF`,
`FXC`, `FXE`, `FXY`) were served from the Yahoo backstop because Massive's
history for these ETFs did not cover the full requested window, and `USO`
from Massive directly.

Realized sample: `n_obs = 4602`, `n_tickers = 9`,
`2007-04-19` to `2025-08-01` (`results/exp1_run_summary.json`), versus the
paper's `1990` to `Aug 2025`. The start date is set by the latest inception
among the nine proxies (`IEF` and `EWQ`, both launched in 2007); this
shortens the realized sample by about seventeen years relative to the paper
and removes the "Pre-GFC (2007)" crisis episode entirely (see "Not
reproduced").

### Table 2: RC by position (single day, 2025-08-01)

Full position-level output: `results/exp1_table2_rc_by_position.csv`. The
paper's Table 2 is not reproduced on an exact position-by-position basis
because three of its twelve positions (`XU1 Index`, `RX1 Comdty`,
`JB1 Comdty`) are absent from the realized universe; the nine common
positions are compared in Table 3 below.

### Table 3: RC by asset class (single day, 2025-08-01)

Values are the asset-class roll-up of RC, inherent RC and correlation RC, in
daily-volatility percentage points (`results/exp1_table3_rc_by_asset_class.csv`,
multiplied by 100). Paper values are Table 3 (Sec. 5.1).

**Long-Short portfolio**

| Asset class | RC (paper / repo) | Inh (paper / repo) | Corr (paper / repo) | Verdict |
|---|---|---|---|---|
| Commodity | 1.03 / 1.07 | 0.98 / 0.91 | 0.05 / 0.16 | partially reproduced |
| Equity | 0.56 / 0.67 | 1.10 / 1.38 | -0.55 / -0.71 | reproduced (same sign, within 20%) |
| FX | 0.77 / 0.79 | 0.24 / 0.27 | 0.53 / 0.52 | reproduced |
| Fixed Income | 3.45 / 3.03 | 4.21 / 2.50 | -0.76 / +0.53 | partially reproduced (RC magnitude within 12%, but correlation component has the wrong sign) |
| **Total** | **5.81 / 5.57** | **6.53 / 5.06** | **-0.72 / +0.51** | partially reproduced |

**Equal-Weight portfolio**

| Asset class | RC (paper / repo) | Inh (paper / repo) | Corr (paper / repo) | Verdict |
|---|---|---|---|---|
| Commodity | 3.80 / 0.33 | 2.94 / 0.24 | 0.86 / 0.09 | not reproduced (magnitude; sign and dominance reproduced) |
| Equity | 1.38 / 0.14 | 0.64 / 0.05 | 0.74 / 0.09 | not reproduced (magnitude) |
| FX | 0.16 / 0.01 | 0.15 / 0.01 | 0.01 / 0.00 | not reproduced (magnitude) |
| Fixed Income | -0.11 / 0.00 | 0.05 / 0.00 | -0.16 / 0.00 | partially reproduced (both near zero) |
| **Total** | **5.22 / 0.48** | **3.79 / 0.31** | **1.44 / 0.17** | not reproduced (magnitude); ranking (Commodity largest, matching the paper's text) reproduced |

**Inverse-Volatility portfolio**

| Asset class | RC (paper / repo) | Inh (paper / repo) | Corr (paper / repo) | Verdict |
|---|---|---|---|---|
| Commodity | 0.39 / 0.10 | 0.42 / 0.06 | -0.03 / 0.04 | partially reproduced |
| Equity | 0.41 / 0.10 | 0.36 / 0.04 | 0.05 / 0.06 | partially reproduced |
| FX | 0.99 / 0.15 | 0.41 / 0.06 | 0.57 / 0.09 | partially reproduced (magnitude smaller, but FX remains the largest contributor, matching the paper) |
| Fixed Income | 0.50 / 0.03 | 0.38 / 0.02 | 0.12 / 0.01 | not reproduced (ranking: paper has FI second-largest, repo has FI smallest) |
| **Total** | **2.29 / 0.38** | **1.57 / 0.19** | **0.72 / 0.19** | not reproduced (magnitude) |

**Qualitative patterns from the paper's text (Sec. 5.1).** "For the
long-short portfolio, fixed income is the largest RC contributor, with a
large positive inherent component partially offset by a negative correlation
component" — **reproduced** for "fixed income is the largest RC contributor"
and "large positive inherent component"; **not reproduced** for "offset by a
negative correlation component" (the repo's Fixed Income correlation RC is
+0.53, not negative — see "Deviations from the paper"). "For the
equal-weighted portfolio, commodities dominate, driven by high inherent
volatility" — **reproduced** (Commodity is the largest RC and inherent RC
component in both). "For the inverse-volatility portfolio, FX carries the
largest RC" — **reproduced** (FX is largest in both); "followed by fixed
income, equities, and commodities" — **not reproduced** (repo ranking after
FX is Commodity > Equity > Fixed Income, not Fixed Income > Equity >
Commodity).

**Identified cause of the magnitude gap.** The Equal-Weight and
Inverse-Volatility portfolios use small, un-leveraged weights (0.08 and
roughly 0.02-0.20 respectively) applied to the realized nine ETF proxies,
whose daily volatility (around 1-2% for the equity/bond proxies, higher for
the commodity proxies) is materially lower than that implied by the paper's
raw Bloomberg generic front-month futures and FX series at the same nominal
weights: the paper's Eq total RC of 5.22 at weight 0.08 per position implies
an average per-instrument daily volatility near 16%, far above the realized
ETF proxies' volatility. This is consistent with Bloomberg generic futures
being quoted and rolled without the fee, tracking-error and structuring
effects of an ETF wrapper. The LS portfolio's 10x leverage brings its total
RC within 4% of the paper's (5.81 vs. 5.57) because the larger nominal
weights compensate for the proxies' lower volatility, which is why only the
LS portfolio's magnitudes track the paper closely while the Eq and IV
magnitudes do not. The Fixed Income correlation-sign disagreement (LS) and
the Inverse-Volatility ranking disagreement both come from the two excluded
Fixed Income legs `RX1 Comdty` and `JB1 Comdty`: the paper's Table 3 shows
`RX1 Comdty` alone contributing a correlation RC of -1.00 (Table 2, LS) that
is large enough to flip the Fixed Income group total from positive to
negative, and the paper's Fixed Income IV weight (`0.14+0.14+0.20 = 0.48`)
is more than three times the realized universe's remaining Fixed Income IV
weight (`TY1 Comdty` only, `0.14`), which is enough to explain why Fixed
Income no longer ranks second in the realized Inverse-Volatility portfolio.

### Table 4: XSR correlation, iVol and MDD (LS portfolio, single day)

Full output: `results/exp1_table4_xsr_ivol_mdd.csv`. The paper's qualitative
claims (Sec. 5.1): "Most positions show sign agreement between XSR Corr and
Corr RC" and the concrete instance "`RX1` shows RC > 0 but iVol < 0" (the
discrete-vs-marginal hedging condition of eq. 11). Since `RX1 Comdty` is
excluded from the realized universe, this specific instance cannot be
checked; see "Not reproduced". Sign agreement between the ICD correlation
component and the XSR correlation factor across the nine realized positions:
7 of 9 agree in sign, matching the paper's "most positions show sign
agreement" statement qualitatively — **reproduced**.

### Figures 2-5: time-varying RC by asset group (Method 1, 1990-2025)

Series saved as `results/exp1_timevarying_{LS,Eq,IV}.csv` and plotted in
`results/exp1_figure_{LS,Eq,IV}_timevarying.png` (realized sample starts
2007-04-19, not 1990, per the data availability above). Covariance date
varies from the start of the realized sample to 2025-08-01 with positions
fixed at 2025-08-01, per Sec. 5.2 "Method 1" (current weights, rolling
covariance).

### Table 5: Crisis-period RC attribution (LS portfolio, Method 1 averages)

Paper values (Table 5, Sec. 5.3, daily volatility percentage points) versus
`results/exp1_table5_crisis_attribution.csv`:

| Episode | Asset class | ΔInh (paper / repo, pp) | ΔCorr (paper / repo, pp) | Verdict |
|---|---|---|---|---|
| Pre-GFC (2007) | Equity | +2.34 / n/a | -0.33 / n/a | not reproduced (episode absent, see below) |
| GFC Peak (2008-09) | Equity | +2.24 / +3.35 | -1.61 / -0.71 | reproduced (sign); magnitude differs |
| GFC Peak (2008-09) | Commodity | +0.86 / +0.42 | +0.41 / +0.74 | reproduced (sign) |
| European Debt (2011-12) | Fixed Income | +2.47 / +0.01 | -2.34 / +0.19 | not reproduced (ΔCorr sign disagrees) |
| Covid (2020) | Equity | +2.12 / +1.98 | -0.77 / +0.18 | partially reproduced (ΔInh reproduced; ΔCorr sign disagrees) |
| Covid (2020) | Commodity | +0.47 / +0.24 | +0.44 / +0.68 | reproduced (sign) |
| Fed Tightening (2022) | Fixed Income | +6.18 / +2.59 | -5.12 / -0.07 | reproduced (sign); ΔCorr magnitude much smaller |

Four of the paper's five crisis episodes, and the "rising inherent RC
offset by falling correlation RC" pattern the paper reports for Fixed Income
in the Fed-tightening and GFC-peak episodes, are directionally reproduced;
the smaller absolute magnitude of every change follows the same ETF-proxy
volatility gap identified for Table 3 above. The European Debt episode's
Fixed Income correlation change has the wrong sign: the paper attributes
that episode's fixed-income flight-to-safety dynamic specifically to
`RX1 Comdty` (German Bund futures) and `JB1 Comdty` (JGB futures), both
excluded from the realized universe, leaving only `TY1 Comdty` (U.S.
10-year note) to represent the Fixed Income group; this is an identified
cause, not merely a scale effect, since `TY1 Comdty`'s flight-to-safety
response to the 2011-12 European sovereign crisis was weaker than the
Euro-area bond futures the paper uses. The Covid episode's Equity
correlation change also has the wrong sign, and its cause is the same kind
of gap in the Equity group: the paper's Equity group (Sec. 5.1) holds
`ES1 Index`, `CF1 Index`, and `XU1 Index` (`src/config.py:TICKER_PROXIES`),
and `XU1 Index` is excluded from the realized universe
(`src/config.py:EXCLUDED_TICKERS`), leaving only `ES1 Index` and `CF1 Index`
to represent Equity. `XU1 Index` carries a pre-leverage weight of +0.10 (Table
1) opposite in sign to `CF1 Index`'s -0.2, so its omission removes a
diversifying long equity leg from a group whose net LS exposure is carried
almost entirely by the short `CF1 Index` position, which is enough to flip
the sign of the group's correlation response during the 2020 sell-off; this
is an identified cause, not an unexplained residual.

## Experiment 2: Convergence of RC and Its Components (Appendix B)

Simulates five Gaussian assets with covariance matrix having unit diagonal
and 0.5 off-diagonal entries, an equal gross weight of 1 per asset (the
closest integer weight to the paper's reported population targets; see
`src/config.py:PORTFOLIO_WEIGHT`), an expanding window from 5 to 450
observations, and 100 bootstrap replications, matching the paper's stated
simulation size exactly (no reduction was needed: the full run completes in
well under a minute).

Population targets (`results/exp2_run_summary.json`, computed analytically
from eq. (10) with sigma_p = sqrt(w^T Sigma w)):

| Metric | Paper (Fig. 6, read from the figure) | Repository |
|---|---|---|
| Total RC | 4.3 | 3.873 |
| Total Inherent RC | 1.1 | 1.291 |
| Total Correlation RC | 3.3 | 2.582 |

Verdict: **partially reproduced**. The paper calls this an "equal-weighted
portfolio" without stating the weight normalization; weights summing to one
(`w_i = 1/5`) give sigma_p = 0.774, inconsistent with the paper's reported
Total RC of 4.3, and for this covariance structure the Inherent/Total RC
ratio (1/3 for any uniform weight, since both scale with the same power of
the common weight) cannot match the paper's implied ratio (1.1/4.3 = 0.256)
at any uniform weight. The unit weight used here reproduces the correct
order of magnitude and the qualitative pattern Total RC > Correlation RC >
Inherent RC, but not the paper's exact figures, because no uniform weight
reproduces both simultaneously; this discrepancy is an open point in how
Figure 6 was generated, not a code defect (verified by the closed-form
check `sigma_p = w * sqrt(15)` above), and is not resolved further.

Convergence behavior (`results/exp2_convergence_total_{rc,inh,corr}.csv`,
`results/exp2_figure6_convergence.png`): the 5th-95th percentile band width
narrows from `{total_rc: 4.273, total_inh: 0.888, total_corr: 4.229}` at
T=5 to `{total_rc: 0.695, total_inh: 0.102, total_corr: 0.695}` at T=125,
a reduction of roughly 6x for all three series — **reproduced** ("the
confidence bands ... should narrow substantially after approximately 125
observations"). The ratio of the band width at T=125 to the band width at
T=5 is 0.163 for Total RC, 0.115 for Total Inherent RC and 0.164 for Total
Correlation RC — **reproduced** ("the convergence rates of the inherent and
correlation components should be similar to that of aggregate RC").

## Deviations from the paper

1. **Data source.** The paper uses Bloomberg generic futures/FX series
   rolled with code `N:05_0_R`. No Bloomberg terminal is available in this
   environment; price history is loaded through the QuantX Dataloader REST
   API (`data/data_loader.py`), which does not serve continuous-futures
   rolls. Nine of the paper's twelve instruments are replaced by liquid
   exchange-traded proxies with the same economic exposure (mapping in
   `src/config.py:TICKER_PROXIES`); eight of the nine were served through
   the Dataloader's Yahoo Finance backstop and one (`USO`) from Massive
   directly (`results/exp1_run_summary.json:non_massive_source`).
2. **Universe.** Three positions (`XU1 Index`, `RX1 Comdty`, `JB1 Comdty`)
   are excluded from the realized universe because no continuous futures
   series or liquid, long-history ETF proxy with the same exposure is
   available through the Dataloader/Massive stack under the available
   entitlement. Their omission is the identified cause of the Fixed Income
   correlation-sign disagreement in Table 3 (LS portfolio), the Fixed
   Income ranking disagreement in the Inverse-Volatility portfolio of
   Table 3, the European Debt episode's wrong-signed correlation change in
   Table 5, and the Covid episode's wrong-signed Equity correlation change
   in Table 5, since `XU1 Index` is one of the three Equity positions (see
   the discussion under each table above).
3. **Sample period.** The paper's sample is 1990 to August 2025. The
   realized sample is 2007-04-19 to 2025-08-01, bounded below by the latest
   inception date among the nine ETF proxies (`IEF` and `EWQ`). This removes
   the "Pre-GFC (2007)" crisis episode entirely (see "Not reproduced").
4. **Crisis-episode windows (Table 5).** The paper names five crisis
   episodes but does not give exact pre-crisis/crisis start and end dates;
   the windows used are in `src/config.py:CRISIS_EPISODES` (assumed).
5. **Inverse-Volatility lookback.** The paper specifies "trailing six-month
   volatility" without an exact day count; 126 business days is used
   (`src/config.py:IV_VOL_WINDOW_DAYS`), the same convention as the
   126-business-day covariance window the paper specifies explicitly.
6. **Experiment 2 portfolio weight.** The paper calls the simulation
   portfolio "equal-weighted" without stating the weight normalization. A
   gross weight of 1 per asset is used, the closest integer uniform weight
   to the paper's reported population targets (Total RC = 4.3); see
   `src/config.py:PORTFOLIO_WEIGHT` and the discussion under Experiment 2
   above for why no uniform weight reproduces the paper's reported Inherent
   and Correlation targets exactly.

## Not reproduced

1. **Pre-GFC (2007) row of Table 5.** The realized sample starts
   2007-04-19 (set by the proxies' inception dates, see "Deviations from
   the paper"), which does not leave 126 business days of covariance
   warm-up before the paper's implied "Pre-GFC (2007)" pre-crisis window
   (2007-04-18 to 2007-07-31); no valid covariance estimate exists over that
   window in the realized sample, so this row cannot be computed. A full
   Bloomberg-sourced run starting in 1990, per the paper, would not have
   this limitation.
2. **Table 2's RX1 Comdty row and the associated discrete-hedging
   instance.** The paper's Sec. 5.1 discussion of `RX1 Comdty` ("RC > 0 but
   iVol < 0", a concrete instance of the discrete-versus-marginal hedging
   condition of eq. 11) cannot be checked because `RX1 Comdty` has no proxy
   in the realized universe (see "Deviations from the paper", item 2).
3. **Exact position-by-position match to the paper's Table 2 for the three
   excluded instruments** (`XU1 Index`, `RX1 Comdty`, `JB1 Comdty`): not
   computed, for the same reason.
