# Country-level beef-and-veal consumer-price SDiD

This robustness check compares Denmark with other EU countries in the same consumer-price category. It tests the choice of control group. Denmark's HICP is compiled by Statistics Denmark, so it does not independently validate Danish price collection. It replaces the earlier carcass-price analysis in the existing Figure B3; trade analysis is unchanged.

## Source and sample

- Provider: Eurostat, [Harmonised Index of Consumer Prices](https://ec.europa.eu/eurostat/web/hicp).
- Dataset: `prc_hicp_midx`, historical ECOICOP monthly index, `coicop=CP01121` (Beef and veal), `unit=I15` (2015=100), `freq=M`.
- [Exact JSON-stat query](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_midx?lang=EN&freq=M&unit=I15&coicop=CP01121&sinceTimePeriod=2023-04&untilTimePeriod=2025-09).
- Snapshot: `data/raw/eurostat_beef_hicp_2023m04_2025m09.json`, retrieved 11 September 2026 at 11:24:56 UTC; source update timestamp `2026-02-06T23:00:00+0100`. URL, retrieval timestamp, bytes, and SHA-256 are recorded in `data/reference/replication_input_manifest.json`; `data/raw/hicp_manifest.json` also records retrieval provenance.
- The query uses the historical release for the entire 2023–2025 study window. Eurostat [introduced ECOICOP version 2 and a 2025 index base in 2026](https://ec.europa.eu/eurostat/web/hicp/information-data); the earlier release remains available for 1996–2025 and is frozen except for error corrections. No splice with the new classification is made.
- Preprocessing retains the 27 EU Member States, using Eurostat's `EL` for Greece. EU/euro-area aggregates and non-EU countries are excluded. Original observations and status flags are preserved; missing observations are neither interpolated nor set to zero.
- Stata selects countries with 30 positive monthly observations from April 2023 through September 2025. All 27 countries qualify: Denmark and 26 donors, 810 observations, 15 pre-treatment months and 15 post-treatment months. Treatment begins July 2024.

The index measures price developments, not a currency price level across countries. Its common reference period does not identify purchasing-power differences or an absolute beef price per kilogram. It is not used as the level-price anchor in the SCC calibration.

## Reproduction

With `PYTHONPATH=src`, run `python scripts/prepare_country_hicp_panel.py` from the repository root. This downloads the snapshot only if absent and writes `data/processed/eu_beef_hicp_country_month_panel.csv`. The normal `download` stage acquires HICP and `estimate` reshapes it automatically. Existing snapshots are reused unless `download --refresh` is explicitly selected.

Run `do scripts/stata/country_sdid.do` in Stata/MP 19.5, or run the full `scripts/stata/master.do`. The specification is `sdid ln_price unit month_id treated_post, vce(placebo) reps(200) seed(20260827)`, using sdid 2.0.2. The outcome is log HICP. With one treated country, the package's unit-cluster bootstrap is unavailable; placebo inference relies on comparability of residual variation across countries and is not a randomized-assignment test. The reported p-value is the two-sided normal approximation from the placebo standard error.

`country_sdid_diagnostics.do`, called by the master after the estimate, exports all donor and pre-period weights, 26 leave-one-donor-out point estimates, two short treated-outcome holdouts, and a June-2024-omission estimate with 200 placebo replications. The main unit weights have a Herfindahl sum of squares of 0.124 (effective donor count 8.1); Finland, the Netherlands, and Czechia carry 54.1% together. June 2024 receives 64.8% of the pre-period time weight despite the 24 June agreement. Omitting June gives 0.0220 (placebo SE 0.0282), compared with 0.0157 (0.0293) in the main specification. Donor omissions give point ATTs from 0.0061 to 0.0257. The October–December 2023 holdout yields -0.0094 after April–September training; an April–June 2024 holdout gives 0.0042 but already contains expert-tax and nitrate-policy news. These in-sample and short holdout diagnostics cannot establish the July–September 2025 counterfactual.

## Results and outputs

ATT = 0.0156655, placebo SE = 0.0292872, p = 0.59272426, and 95% interval [-0.041736357, 0.07306736]. The point estimate corresponds to about 1.6%. This smaller, statistically insignificant estimate qualifies the magnitude of the main within-Denmark finding; it does not establish zero effect, and its interval includes the preferred CPI estimate. Common international beef shocks and spillovers remain identification concerns.

The pre-treatment centered-gap RMSE is 0.0099884672 log points. For display, the weighted donor series is shifted by the constant pre-treatment mean treated–donor gap. This aligns the paths in level while preserving all monthly changes; synthetic DiD permits an intercept, and the plotting adjustment does not change the estimate. The raw weighted series is retained for audit.

- `country_sdid_estimate.csv`: estimate, inference, sample dimensions, pre-treatment Danish index mean, and centered pre-fit RMSE.
- `country_sdid_series.csv`: raw treated and synthetic log indices, their gap, post indicator, and display-only `synthetic_aligned`.
- `country_hicp_coverage.csv`: country inclusion and valid-month counts.
- `country_hicp_estimation_sample.csv`: exact source values and flags used in Stata.
- `outputs/figures/stata/country_sdid.png`: the replacement Figure B3.

All CSV outputs are under `outputs/models/stata/`. The obsolete carcass-price preprocessing script and input requirement are removed from the publication workflow; historical versions remain in Git history. No additional appendix price figure is introduced.
