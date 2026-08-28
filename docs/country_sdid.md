# Country-level beef-price SDiD robustness check

This check addresses the control-food independence assumption by treating Denmark as the exposed unit and using other EU Member States as the donor pool.

## Source and sample

- Source page: European Commission, [Beef statistics](https://agriculture.ec.europa.eu/data-and-analysis/markets/overviews/market-observatories/meat/beef-statistics_en).
- API: [Agri-food Data API beef documentation](https://agridata.ec.europa.eu/extensions/API_Documentation/Beef.html), carcass endpoint `api/beef/prices`.
- Query window: 3 April 2023 through 28 September 2025; the monthly estimation window is April 2023--September 2025.
- Series: product code `AO2`, reported as “Young bulls”; this is conformation class O and fat-cover class 2 under the Commission's [carcass-classification methodology](https://agriculture.ec.europa.eu/document/download/2fd345d9-fef1-40fc-94e7-f4608682a38d_en?filename=methodology-carcase-remainders_en.pdf).
- Prices are reported in EUR per 100 kg of carcass weight. Weekly observations are averaged within country-month. The EU aggregate is excluded, and only countries with all 30 monthly observations are retained.
- Final panel: 23 countries (Denmark plus 22 donors), 690 observations. Monthly cells contain 1--6 available weekly reports.

## Reproduction

1. Download the API JSON to `data/raw/eu_beef_carcass_prices_2023m04_2025m09.json`.
2. Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_country_beef_panel.ps1`.
3. Run `scripts/stata/country_sdid.do` in Stata 19.5. The estimator is Stata's existing `sdid` command with `vce(placebo) reps(200)` and seed `20260827`.

The graph is written to `outputs/figures/stata/country_sdid.png`; the ATT and placebo-based standard error/interval are written to `outputs/models/stata/country_sdid_estimate.csv`.

## Bootstrap attempt

The installed `sdid` v2.0.2 command was also run with `vce(bootstrap) reps(200)`. It returns Stata error `r(451)`: the bootstrap standard error requires more than one treated unit when there is a single treatment period. Since this design has only Denmark as the treated country, the package's unit-cluster bootstrap is unavailable. The placebo-based standard error remains the valid built-in inference for this one-treated-unit specification; duplicating Denmark or resampling months would not be the same estimator's standard bootstrap.
