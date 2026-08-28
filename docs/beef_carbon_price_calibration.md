# Beef carbon-price calibration

The calibration uses the Stata estimates and an equal-paper-weight synthesis of ten eligible preferred global total-SCC estimates. Estimates reported for dates other than 2030 are treated as time-invariant when their sources do not provide a time path. Barrage and Nordhaus (2024) is log-interpolated within its published 2025--2050 path.

## Meta-analytical benchmark

- Pooled mean: USD 157.96/tCO2 in 2024 dollars.
- Hierarchical 95% interval: USD 77.22--363.40/tCO2.
- Median across paper point estimates: USD 109.74/tCO2.
- Number of equally weighted papers: 10.

The hierarchical interval uses 10,000 paper-bootstrap replications. Let `theta_j` denote a paper's preferred estimate and `[L_j,U_j]` a positive central range with coverage `1-2 alpha_j`. Its log-scale dispersion is

```text
sigma_j = (log(U_j) - log(L_j)) / (2 * Phi^-1(1-alpha_j)).
```

Each replication samples ten papers with replacement. For every selected paper with a usable range it draws

```text
X_j = exp(log(theta_j) - sigma_j^2/2 + sigma_j * Z_j),  Z_j ~ N(0,1),
```

which keeps `E[X_j]=theta_j`; papers without a usable range remain at their point estimate. The mean of the ten selected draws is saved. The reported interval is the 2.5th--97.5th percentile range of the 10,000 saved means. Ricke et al.'s 66% model range and Rennert et al.'s 5th--95th quantiles retain their stated coverages, while Hänsel et al.'s parameter span is conservatively calibrated as a 95% range. Paper resampling captures between-paper dispersion and the lognormal draws propagate within-paper range information. These inputs are not relabelled as sampling confidence intervals.

## Mapping to beef prices

Assumptions:

- Effective average output burden in 2030: DKK 120/tCO2e after the 60% per-animal deduction.
- Marginal abatement incentive in 2030: DKK 300/tCO2e.
- Exchange rate: 6.8953 DKK/USD.
- Lifecycle beef carbon-intensity benchmark: 59.6 kg CO2e/kg product. This is broader than the farm-level emissions base subject to the Danish levy, so the exercise is an accounting sensitivity, not a tax-base calculation.
- Mean pre-announcement beef price: DKK 158.54/kg.

For SCC value `s` and policy margin `tau`, the additional log beef-price gap is:

```text
log((158.54 + (s * 6.8953 - tau) * 59.6 / 1000) / 158.54)
```

At the pooled mean, the log-price gap is 0.311 under the DKK 120 average-burden scenario, with a hierarchical interval of 0.144--0.640. Under the DKK 300 marginal-incentive scenario, it is 0.260, with an interval of 0.084--0.604.

The main microdata DiD estimate is 0.0437 (clustered SE 0.0163). At the pre-period mean this is approximately DKK 7.1/kg, mechanically equivalent to about USD 17/tCO2 under the common intensity assumption. This announcement-period price equivalent is not added to either future statutory margin: signals across dates are not structurally additive, and observed pass-through depends on adjustment, credibility, discounting, contracts, demand, and costs.

This is an accounting comparison, not a structural welfare or pass-through model.
