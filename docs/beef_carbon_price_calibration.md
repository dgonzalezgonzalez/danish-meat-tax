# Beef carbon-damage calibration

The exercise asks how much of a climate-damage price benchmark could be covered by the observed announcement-period price increase if it persists to implementation. It is conditional accounting, not a welfare estimate or an identified pass-through model. The SCC entry point is `scripts/stata/scc_meta_analysis.do`, called by the master and pipeline `outputs` stage.

## Study selection and harmonization

The inventory records one preferred input per included study. Ten studies receive equal weight. This selected corpus is not an exhaustive systematic review, and its members share models and assumptions. Pindyck's 83.6 USD value is the high-confidence, 10th–90th percentile trimmed lognormal specification in Table 7; it measures average catastrophic-damage avoidance rather than marginal SCC. Excluding it gives 166.32 USD/tCO2. Cai–Lontzek uses Table 9's combined economic-and-climate-risk benchmark, 124 USD/tC for 2005 (IES 1.5, risk aversion 10); 99 was an upper value in a different growth-only exercise and was corrected.

Cai et al. (2016) uses 2010 as both the initial SCC year and dollar base; the earlier 2015 coding was corrected. Pindyck's 2017 monetary base is an explicit inventory assumption; exclusion sensitivity addresses its additional comparability issue.

Multiply USD/tC by 12/44 and inflate US dollars with annual CPI-U to 2024. Barrage–Nordhaus 2030 is log-interpolated between 2025 and 2050. Only it and Nordhaus's 2030 estimate are directly dated to 2030; their mean is 93.36 USD/tCO2. The other values are held constant as a sensitivity assumption even when a source models a rising or stochastic path. The ten-study benchmark is not a pooled forecast for 2030.

The selected mean is 160.39 USD/tCO2; median 109.74; leave-one-out means span 111.56–172.36. Every result is exported, retaining source locators and selection notes.

## Hierarchical sensitivity envelope

For preferred value theta and a positive source range [L,U], assign log-scale dispersion

```text
sigma = (log(U)-log(L)) / (2*Phi_inverse(1-alpha))
X = exp(log(theta)-sigma^2/2+sigma*Z), Z ~ N(0,1).
```

This centers E[X] on theta and matches the range's log width. It generally does not reproduce both endpoints as the corresponding simulated quantiles. Ricke's 66% range uses alpha=.17, Rennert's 5th–95th quantiles use .05, and Hänsel's ethical-parameter span is assigned .025 as an explicit sensitivity assumption. That assignment has no sampling-probability interpretation. Inputs without a usable range stay at their point values.

Each of 10,000 replications resamples ten papers with replacement and draws independently for every selected occurrence, then averages. Seed is 20260827. The 2.5th–97.5th percentiles are 79.50–366.63 USD/tCO2. These describe sensitivity to selected studies and range assumptions, not confidence intervals for a common structural parameter or evidence from independent studies.

## Units and policy margins

- Pre-announcement grocery beef mean: 162.4435 DKK/kg. It spans several pre-announcement months; treating it as a 2024 real-price benchmark is an approximation.
- Exchange-rate assumption: 6.8953 DKK/USD, the 2024 annual conversion used in the exercise. It is not a forecast of 2030 currency values.
- Lifecycle emissions: 59.6 kg CO2e/kg beef, the beef-herd benchmark of Poore and Nemecek (2018), as presented by OECD (2025). This exceeds the farm-level tax base and combines gases whose dynamic damages differ.
- Quoted 2030 rates: 120 DKK/tCO2e average burden and 300 marginal abatement incentive, both in 2022 prices. PRIS04 annual means give a factor 1.0493796, hence 125.9256 and 314.8139 in 2024 DKK.

For SCC c and policy margin tau, the broad common-intensity mapping is

```text
log((pre_price + (c*FX-tau)*intensity/1000)/pre_price).
```

At the pooled mean it gives 0.307 [0.143,0.631] for average burden and 0.255 [0.082,0.593] for marginal incentive. These intervals have a different interpretation from the econometric intervals plotted alongside them; their overlap is not a formal hypothesis test. The marginal incentive is not interpreted as average output tax incidence.

## Persistence and additional implementation response

Let a be announcement persistence, f the assumed taxable fraction of lifecycle intensity, and lambda additional implementation pass-through relative to the reference-animal average burden. The remaining level gap is

```text
SCC_mean*FX*intensity/1000
 - a*pre_price*(exp(preferred_aggregate_DiD_ATT)-1)
 - lambda*average_tax_2024*f*intensity/1000.
```

The last term is additional incidence after the announcement period. If an external pass-through estimate measures total incidence including earlier adjustment, replace the two price terms with that total instead of adding it again. The 300-DKK marginal abatement rate does not enter this output-price decomposition.

The preferred official CPI DiD is 0.0643767291 (column 2, HAC with two lags). Applying this proportional estimate to the grocery DKK/kg benchmark assumes the same proportional response across these measures; CPI index points are never treated as DKK/kg. The announcement point increment is 10.80 DKK/kg against central lifecycle damages of 65.91. With full persistence and no additional implementation increase, the remaining gap is 55.11. At full persistence, full taxable lifecycle share, and full additional pass-through, it is 47.61.

`persistence_analysis.do`, called by the SCC script, exports `calibration_scenarios.csv` (all 27 combinations in {0,.5,1}) and `calibration_surfaces.csv` (four 51-by-51 grids). All four surfaces vary a and lambda over [0,1], with f fixed at .25, .50, .75, or 1. Python renders these Stata outputs without estimation.

`scc_meta_draws.csv` preserves the original 10,000 hierarchical SCC draws. `persistence_analysis.do` pairs them with independent coefficient draws beta_hat + HAC_SE * t(28), using seed 20260910. The 28 degrees of freedom match the preferred 30-month, intercept-plus-post Newey-West regression. This is an approximate coefficient-uncertainty distribution using the same reference distribution as the reported interval. `calibration_joint_draws.csv` stores the paired SCC, coefficient, damage, and announcement draws for auditing. The announcement draw now multiplies exp(beta_draw)-1 by an independent resampled grocery mean. Independence across SCC, coefficient, and grocery-price draws is assumed, not estimated; possible covariance between grocery prices and the official CPI estimate is omitted.

For each persistence value, Stata calculates the 2.5th and 97.5th percentiles of damage_draw - a*announcement_draw. Subtracting the deterministic implementation increment then gives `sensitivity_low` and `sensitivity_high` for every f/lambda combination. The exact same paired draws are used across the grid, avoiding unrelated simulation noise between parameter combinations. At a=0, the interval reduces to the SCC sensitivity interval in DKK/kg less the implementation increment. These are pointwise combined sensitivity intervals, not simultaneous confidence bands or frequentist confidence intervals for a common SCC parameter. Intensity, FX, and policy rates remain fixed. Price-benchmark and coefficient uncertainty both drop out at a=0.

The original coefficient-only bounds remain available as `conf_low` and `conf_high` for comparison, but Figure 4 now plots the combined sensitivity fields. At a=f=lambda=1 the combined interval is 11.06–132.19 DKK/kg, versus 36.44–58.10 using only coefficient uncertainty.

The point minimum over the cube is 47.61, and the minimum combined lower bound is 11.06: no scenario closes the central gap. Full persistence and implementation cover about 28% of damages; announcement alone covers at most about 16%. The SCC threshold for point closure at a=f=lambda=1 is about 44.55 USD/tCO2. These are conditional accounting comparisons, not identified tax incidence or welfare.


## Grocery price uncertainty (11 September 2026)

`price_benchmark_analysis.do` runs automatically at the start of the SCC script, hence from `master.do` and the pipeline `outputs` stage. It uses exactly the pre-treatment beef observations underlying the microdata mean: 1,638 product–store–months, 535 product–store units, and eight pre-period months. The arithmetic mean is 162.4435219472477 DKK/kg. It is observation-weighted, not a balanced-unit or expenditure-weighted index.

For each of 10,000 replications, resample 535 complete unit histories with replacement and independently resample a common calendar sequence using circular blocks of two months (four blocks). Calculate the ratio of resampled price totals to observed-cell counts. Unobserved cells contribute zero to both totals and counts, never an imputed zero price. This adapts crossed row/column resampling to allow short time blocks; see [Owen (2007), The pigeonhole bootstrap](https://doi.org/10.1214/07-AOAS122). It assumes exchangeability across unit histories and approximate stationarity across the short calendar support. With only eight months, it is a resampling sensitivity exercise, not a claim of reliable nominal frequentist coverage. Non-random source coverage, common product-brand or retailer dependence beyond the retained unit histories and calendar blocks, and systematic measurement error are not resolved.

Seed 20260911 produces main two-month draws followed by one- and four-month alternatives. The main 2.5th–97.5th percentile interval is 146.97–178.28 DKK/kg; one-month blocks give 146.41–178.94 and four-month blocks 147.52–177.91. The original point estimate stays unchanged.

Figure 2 maps each available SCC distribution jointly with these price draws. Individual-study simulations use seed 20260912 and the existing mean-centered lognormal calibration; Moore's external 5th–95th range uses z=Phi_inverse(.95), just as Rennert's. Studies without usable ranges hold SCC fixed, so their bars only show grocery-price variation. The theory-only row retains missing results. Bilal's lower bound is a conditional marker at the central price and is not converted into an invented SCC distribution. The source-specific ranges remain in the appendix and in `source_gap_low/high_*` audit fields; simulated `log_price_gap_low/high_*` are now 95% sensitivity percentiles and do not preserve the source endpoints' original coverage.

Figures 2 and 3 use the same 10,000 paired pooled SCC and grocery-price draws, exported in `scc_price_gap_draws.csv`. Their pooled accounting intervals are 0.1431428422–0.6308839088 (effective burden) and 0.0822055974–0.5934049987 (marginal incentive). Figure 3's three ATT intervals are unchanged: those estimates do not use the level-price benchmark. No joint interval or formal test for ATT minus the accounting gap is calculated.

Figure 4 uses the same price/SCC pairs plus the existing independent coefficient draws. At a=f=lambda=1, one-, two-, and four-month blocks yield 10.94–132.57, 11.06–132.19, and 11.12–132.32 DKK/kg. This is little change from 11.04–132.35 with a fixed price benchmark; finite simulation quantiles need not widen monotonically when an uncertainty component is added. The point accounting conclusions are unchanged. Emissions-intensity uncertainty remains unmodeled for the reasons in [the source audit](emissions_intensity_audit.md).
