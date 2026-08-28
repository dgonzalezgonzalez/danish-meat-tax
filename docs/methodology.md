# Methodology

## Research question and scope

The paper asks whether Denmark's 24 June 2024 livestock-emissions tax announcement changed beef prices. It reports beef only and estimates all analytical models in Stata.

## Scraped microdata

The main micro specification regresses log normalized price on `beef × post`, product--store fixed effects, and month fixed effects. Standard errors are clustered by product--store. June 2024 is excluded. The sample ends at relative month 15 (September 2025), before the official October 2025 bovine viral diarrhoea outbreak interval.

Beef is compared only with classified untreated foods. Pork, lamb/sheep/goat, dairy, mixed livestock products, non-food products, and unknown products are excluded from beef's control group. Price normalization converts mass to DKK/kg and volume to DKK/litre; unsupported units are excluded.

The event study excludes the partial announcement month of June 2024, uses May as the omitted `t=-1` reference, labels July 2024 as the first complete post-announcement month at `t=0`, and tests the remaining pre-period interactions jointly.

## Official aggregate data

The official panel uses Statistics Denmark PRIS01 monthly CPI series under COICOP 2018. Beef and veal (011221) is treated. The donor pool excludes all treated or plausibly exposed meat and dairy categories. The balanced sample contains 53 series over April 2023--September 2025, exactly 15 pre and 15 post months.

The lags-only DiD preserves the prior OECD specification: subtract the monthly donor mean from log beef CPI, regress the gap on the post indicator, and compute Newey--West standard errors with two lags.

The lags-only regression contains 30 monthly gaps after cross-sectional averaging, but reported `N` is the 1,590 series--month observations in the balanced official panel before that averaging step.

Synthetic DiD uses Stata's `sdid` command with 200 placebo replications. Its figure contains only the treated and synthetic series and marks July 2024 with a dashed vertical line.

## SCC synthesis

One preferred global total-SCC estimate enters per eligible paper. Values are harmonized to 2024 USD/tCO2. Other-year estimates are treated as time-invariant when no source path is reported; Barrage--Nordhaus is interpolated within its published path. Ten papers receive equal weight.

The interval uses 10,000 hierarchical bootstrap replications. Each replication resamples ten papers with replacement. For a paper with point estimate `theta` and positive central range `[L,U]` of coverage `1-2 alpha`, within-paper dispersion is `sigma=(log(U)-log(L))/(2*Phi^{-1}(1-alpha))`; its draw is lognormal with log mean `log(theta)-sigma^2/2`, so the arithmetic expectation remains `theta`. Papers without usable ranges remain at their point estimates. The replication statistic is the mean of ten selected within-paper draws, and the reported endpoints are the 2.5th and 97.5th percentiles of the replicated means. The result is a sensitivity envelope, not a conventional common-effect confidence interval.

## Limitations

- Identification is relative to other foods; Denmark has no untreated national unit.
- Automated classification and package parsing can create measurement error.
- The official panel has few donors and only 15 pre-periods, making SDiD weights fragile.
- SCC estimates are structurally heterogeneous; the pooled interval is a sensitivity envelope.
- Carbon-price mapping is an accounting exercise, not a structural incidence or welfare model.
