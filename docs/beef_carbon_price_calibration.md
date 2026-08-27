# Beef carbon-price calibration

The calibration uses the Stata estimates and an equal-paper-weight synthesis of ten eligible preferred global total-SCC estimates. Estimates reported for dates other than 2030 are treated as time-invariant when their sources do not provide a time path. Barrage and Nordhaus (2024) is log-interpolated within its published 2025--2050 path.

## Meta-analytical benchmark

- Pooled mean: USD 157.96/tCO2 in 2024 dollars.
- Hierarchical 95% interval: USD 77.22--363.40/tCO2.
- Median across paper point estimates: USD 109.74/tCO2.
- Number of equally weighted papers: 10.

The hierarchical interval uses 10,000 paper-bootstrap replications. Within each replication, source-level variation is drawn when a paper reports a positive range. Ricke et al.'s 66% model range and Rennert et al.'s 5th--95th quantiles retain their stated coverages. Hänsel et al.'s parameter span is conservatively calibrated as a 95% range. These inputs are not relabelled as sampling confidence intervals.

## Mapping to beef prices

Assumptions:

- Announced tax: DKK 300/tCO2.
- Exchange rate: 6.8953 DKK/USD.
- Beef carbon intensity: 59.6 kg CO2e/kg product.
- Mean pre-announcement beef price: DKK 158.54/kg.

For SCC value `s`, the additional log beef-price gap above the announced tax is:

```text
log((158.54 + (s * 6.8953 - 300) * 59.6 / 1000) / 158.54)
```

At the pooled mean, the log-price gap is 0.260, with a hierarchical interval of 0.084--0.604.

The main microdata DiD estimate is 0.0437 (clustered SE 0.0163). At the pre-period mean this is approximately DKK 7.1/kg, equivalent to about USD 17/tCO2. Combining that announcement-equivalent response with the announced gross tax produces about USD 61/tCO2, below the pooled SCC mean. Matching the pooled mean mechanically would leave a statutory component of roughly USD 141/tCO2, or DKK 970/tCO2, before deductions and incidence adjustments.

This is an accounting comparison, not a structural welfare or pass-through model.
