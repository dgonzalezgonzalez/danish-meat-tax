# Beef Carbon-Price Calibration

This back-of-the-envelope exercise asks whether the estimated beef announcement price effect would cover the gap between the announced Danish livestock tax and the Nordhaus (2017) 2030 social cost of carbon benchmark. The earlier USD 4.7/tCO2e gap compares nominal USD values. With the internally consistent conversion used here, the gap is USD 26.4/tCO2e: Nordhaus reports USD 31.2/tCO2e for 2015 in 2010 USD and states that the SCC grows at 3% per year in real terms, so the benchmark is first grown to 2030 and then converted to 2024 USD. The Danish tax is converted from DKK to USD with the 2024 average exchange rate.

Assumptions:

- Nordhaus benchmark: USD 31.2/tCO2e for 2015 in 2010 USD, grown at 3% per year to USD 48.6/tCO2e in 2030, then converted to USD 69.9/tCO2e after multiplying by the CPI factor 1.4386.
- Announced Danish tax: DKK 300/tCO2e, or USD 43.5/tCO2e at the 2024 average exchange rate.
- Beef carbon intensity: 59.6 kg CO2e/kg product, from the OECD (2025) agri-food carbon-footprint report's Poore and Nemecek (2018) beef-herd benchmark.
- Exchange rate: 6.8953 DKK/USD, the 2024 average USD/DKK rate.
- Average pre-intervention beef price in the estimation panel: 158.54 DKK/kg, or 22.99 USD/kg.

The additional price needed to close the carbon-price gap is:

```math
\Delta p =
\frac{26.4190 \times 59.6}{1000}
= 1.5746\;\text{USD/kg}
= 10.8571\;\text{DKK/kg}.
```

As a log price effect at the observed pre-period beef price:

```math
\tau_{gap} =
\log\left(\frac{\bar p_{pre} + \Delta p}{\bar p_{pre}}\right)
= 0.0662.
```

Main ATT comparison:

| Estimator | ATT | 95% CI | DKK/kg | USD/kg | Implied announcement value, USD/tCO2e | Required tax, USD/tCO2e | Required tax, DKK/tCO2e |
|---|---:|---:|---:|---:|---:|---:|---:|
| DiD | 0.0547 | [0.0240, 0.0855] | 8.92 | 1.29 | 21.7 | 48.2 | 333 |
| SDiD | 0.1828 | [0.0013, 0.3643] | 31.80 | 4.61 | 77.4 | -7.5 | -51 |


The reference value is:

```math
\tau_{gap} = 0.0662.
```

With the updated gap, this reference lies inside the DiD confidence interval and inside the SDiD confidence interval. Using the DiD ATT as the preferred estimate, the announcement effect is equivalent to USD 21.7/tCO2e, so the statutory tax that would exactly reach the inflation-adjusted Nordhaus benchmark is USD 48.2/tCO2e, or DKK 333/tCO2e. Under this internally consistent benchmark, the DiD ATT does not imply lowering the announced DKK 300/tCO2e gross tax; it implies a slightly higher tax. If one instead keeps the grown 2030 Nordhaus benchmark in 2010 USD and compares it directly with the nominal USD value of the Danish tax, the smaller nominal comparison would imply a tax of about USD 26.9/tCO2e.

Latest event-study comparison:

- Latest post-period relative time: 24.
- Latest DiD event-study estimate: 0.1924, with 95% CI [0.0246, 0.3603].
- Latest-period implied price increase: 33.64 DKK/kg, or 4.88 USD/kg.
- Latest-period reverse-engineered carbon price: 81.9 USD/tCO2e.
- Latest-period required statutory tax to match Nordhaus exactly: -11.9 USD/tCO2e, or -82 DKK/tCO2e. Because this is negative, the literal latest-period calculation says the announcement effect alone exceeds the inflation-adjusted Nordhaus benchmark; with a nonnegative tax constraint, the implied statutory tax would be zero.

Figures:

- `outputs/figures/calibration/beef_att_policy_calibration.png`
- `outputs/figures/calibration/event_study_beef_policy_calibration.png`
