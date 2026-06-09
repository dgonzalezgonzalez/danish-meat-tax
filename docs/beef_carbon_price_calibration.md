# Beef Carbon-Price Calibration

This back-of-the-envelope exercise asks whether the estimated beef announcement price effect would cover the USD 4.7/tCO2e gap between the announced Danish livestock tax (USD 43.0/tCO2e) and the Nordhaus (2017) 2030 social cost of carbon benchmark (USD 48.3/tCO2e).

Assumptions:

- Beef carbon intensity: 59.6 kg CO2e/kg product, from the OECD (2025) agri-food carbon-footprint report's Poore and Nemecek (2018) beef-herd benchmark.
- Exchange rate: 6.8953 DKK/USD, the 2024 average USD/DKK rate.
- Average pre-intervention beef price in the estimation panel: 158.54 DKK/kg, or 22.99 USD/kg.

The additional price needed to close the carbon-price gap is:

```math
\Delta p =
\frac{4.7 \times 59.6}{1000}
= 0.2801\;\text{USD/kg}
= 1.9315\;\text{DKK/kg}.
```

As a log price effect at the observed pre-period beef price:

```math
\tau_{gap} =
\log\left(\frac{\bar p_{pre} + \Delta p}{\bar p_{pre}}\right)
= 0.0121.
```

Main ATT comparison:

| Estimator | ATT | 95% CI | DKK/kg | USD/kg | Implied USD/tCO2e |
|---|---:|---:|---:|---:|---:|
| DiD | 0.0547 | [0.0240, 0.0855] | 8.92 | 1.29 | 21.7 |
| SDiD | 0.1828 | [0.0013, 0.3643] | 31.80 | 4.61 | 77.4 |


The reference value, 0.0121, lies below the reported DiD and SDiD confidence intervals if both interval lower bounds exceed it. In that case the observed announcement price increase is larger than the increment needed to bridge USD 4.7/tCO2e. Reverse-engineering from the point estimates implies a carbon price above the Nordhaus benchmark, so the announcement pass-through would be too high under these assumptions.

Latest event-study comparison:

- Latest post-period relative time: 24.
- Latest DiD event-study estimate: 0.1924, with 95% CI [0.0246, 0.3603].
- Latest-period implied price increase: 33.64 DKK/kg, or 4.88 USD/kg.
- Latest-period reverse-engineered carbon price: 81.9 USD/tCO2e.

Figures:

- `outputs/figures/sdid/beef_att_policy_calibration.png`
- `outputs/figures/sdid/event_study_beef_policy_calibration.png`
