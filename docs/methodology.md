# Methodology

## Research question and scope

The paper asks whether Denmark's 24 June 2024 livestock-emissions tax announcement changed beef prices. It reports beef only and estimates all analytical models in Stata.

## Scraped microdata

The main micro specification regresses log normalized price on `beef × post`, product--store fixed effects, and month fixed effects. Standard errors are clustered by product--store. June 2024 is excluded. The sample ends at relative month 15 (September 2025), before the official October 2025 bovine viral diarrhoea outbreak interval.

Beef is compared only with classified untreated foods. Pork, lamb/sheep/goat, dairy, mixed livestock products, non-food products, and unknown products are excluded from beef's control group. Price normalization converts mass to DKK/kg and volume to DKK/litre; unsupported units are excluded.

The event study omits relative month `-1` and tests the remaining pre-period interactions jointly. A Stata synthetic DiD robustness check uses complete commodity--store units and placebo inference.

## Official aggregate data

The official panel uses Statistics Denmark PRIS01 monthly CPI series under COICOP 2018. Beef and veal (011221) is treated. The donor pool excludes all treated or plausibly exposed meat and dairy categories. The balanced sample contains 53 series over April 2023--September 2025, exactly 15 pre and 15 post months.

The lags-only DiD preserves the prior OECD specification: subtract the monthly donor mean from log beef CPI, regress the gap on the post indicator, and compute Newey--West standard errors with two lags.

Synthetic control matches 12 lagged CPI outcomes and three- and four-digit category covariates. Inference is the share of donor-placebo post/pre RMSPE ratios at least as large as beef's ratio. Synthetic DiD uses Stata's `sdid` command with placebo inference. SC and SDiD figures contain only treated and synthetic series.

## SCC synthesis

One preferred global total-SCC estimate enters per eligible paper. Values are harmonized to 2024 USD/tCO2. Other-year estimates are treated as time-invariant when no source path is reported; Barrage--Nordhaus is interpolated within its published path. Ten papers receive equal weight. A 10,000-replication hierarchical paper bootstrap propagates between-paper dispersion and reported positive source ranges without treating model or parameter ranges as sampling confidence intervals.

## Limitations

- Identification is relative to other foods; Denmark has no untreated national unit.
- Automated classification and package parsing can create measurement error.
- The official panel has few donors and only 15 pre-periods, making synthetic weights fragile.
- SCC estimates are structurally heterogeneous; the pooled interval is a sensitivity envelope.
- Carbon-price mapping is an accounting exercise, not a structural incidence or welfare model.
