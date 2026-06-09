# Danish Meat Tax Announcement Price Effects

This repository estimates whether Denmark's 2024-06-24 announcement of a livestock carbon tax changed Danish supermarket prices for meat products. The current main sample uses Danish grocery price histories from `dagligepriser.dk`, normalized to DKK per kilogram or liter where source quantities permit.

## Policy And Treatment Definition

Denmark's Green Tripartite agreement was announced on 2024-06-24. The announced policy is an upstream livestock-emissions carbon tax, not a retail meat tax. Treatment coding follows the policy channel:

- `beef`, `pork`, `lamb_sheep_goat`, and `mixed_livestock` are treated meat commodities.
- `dairy_cattle` is treated by default because dairy-cattle emissions are inside the livestock channel.
- fish, seafood, plant foods, and other non-meat foods are controls.
- unknown commodities are excluded from the main sample.
- non-food products are excluded from the main sample.

Use `--dairy-as-control` for a dairy-as-control sensitivity sample, `--include-unknown` to retain unknown commodities, and `--include-non-food` to retain non-food products.

## Data Pipeline

Install dependencies:

```bash
py -3 -m pip install -r requirements.txt
```

Run the full offline fixture pipeline:

```bash
$env:PYTHONPATH="src"; py -3 main.py all --fixture
```

Run the current real-data workflow:

```bash
$env:PYTHONPATH="src"; py -3 main.py download
$env:PYTHONPATH="src"; py -3 main.py process
$env:PYTHONPATH="src"; py -3 main.py panel --frequency monthly --unit-level product_store --min-pre-periods 1 --min-post-periods 1
$env:PYTHONPATH="src"; py -3 main.py estimate
$env:PYTHONPATH="src"; py -3 main.py outputs
```

Methodological defaults:

- Frequency: monthly.
- Event date: 2024-06-24; for monthly panels the event period is June 2024.
- Estimation unit: `product_store`.
- Panel inclusion: units need at least one pre-event and one post-event observation.
- Outcome: log normalized price.
- Price normalization: source prices are converted to DKK/kg or DKK/liter when quantity parsing succeeds; rows with failed normalization are excluded.
- Raw and large processed data are ignored by Git; selected model, figure, table, and diagnostic outputs are committed.

## Econometric Specification

The main DiD estimator is a two-way fixed-effects regression:

```math
\log(p_{it}) =
\alpha_i + \lambda_t
+ \beta \left(\text{Treated}_i \times \text{Post}_t\right)
+ \varepsilon_{it}.
```

Here `i` indexes the estimation unit, `t` indexes the panel period, `p` is normalized price, unit fixed effects absorb time-invariant product-store price levels, and period fixed effects absorb common food-price shocks.

The subgroup DiD estimator replaces the single treatment interaction with treated-commodity interactions:

```math
\log(p_{it}) =
\alpha_i + \lambda_t
+ \sum_{g \in G} \beta_g
\left(\mathbf{1}\{g_i=g\} \times \text{Post}_t\right)
+ \varepsilon_{it}.
```

The event-study estimator is:

```math
\log(p_{it}) =
\alpha_i + \lambda_t
+ \sum_{\tau \neq -1} \delta_{\tau}
\left(\text{Treated}_i \times \mathbf{1}\{\text{RelativeTime}_t=\tau\}\right)
+ \varepsilon_{it}.
```

Relative period `-1` is the omitted reference period. Output event-study CSVs and plots explicitly include `t = -1` as a zero point estimate with no confidence interval, so figures show the reference period rather than silently skipping it.

DiD standard errors are clustered by estimation unit. The reported confidence intervals use normal critical value 1.96.

## Synthetic DiD

Synthetic DiD is estimated on complete `commodity_store` units because the weighting step requires a rectangular panel. The estimator:

- averages treated complete units;
- chooses donor unit weights on the simplex to match the treated pre-period path;
- chooses time weights on the simplex to weight pre-period imbalance;
- estimates the post-period treated-synthetic gap net of the weighted pre-period gap.

The SDiD estimand is:

```math
\hat{\tau}_{SDID}
=
\frac{1}{T_1}\sum_{t \in \mathcal{T}_1}
\left(\bar{Y}_{1t} - \sum_{j \in \mathcal{C}} \hat{w}_j Y_{jt}\right)
-
\sum_{t \in \mathcal{T}_0} \hat{\lambda}_t
\left(\bar{Y}_{1t} - \sum_{j \in \mathcal{C}} \hat{w}_j Y_{jt}\right).
```

SDiD standard errors are computed by a nonparametric bootstrap over complete treated and control units, with replacement within treatment arm. The code uses a fixed seed (`20240624`) and records the realized bootstrap count in metadata. Current committed outputs use 25 bootstrap replications to keep the full repository pipeline reproducible in ordinary local runs.

SDiD is estimated for all treated commodities jointly and for each treated meat subgroup when the complete-unit donor support is sufficient. In the current run, `lamb_sheep_goat` is skipped for SDiD because complete-unit support is insufficient; the skip reason is stored in `outputs/models/sdid/skipped_sdid_groups.csv`.

## Beef Carbon-Price Calibration

The main interpretive exercise focuses on beef because it is the treated meat commodity with an observed DiD effect and acceptable pre-trend diagnostics.

The question: Denmark's announced livestock tax was about USD 43/tCO2e, while the Nordhaus (2017) 2030 benchmark is about USD 48.3/tCO2e. Would the estimated beef price increase cover the additional USD 4.7/tCO2e gap?

Assumptions:

- Social cost benchmark: Nordhaus (2017), `https://doi.org/10.1073/pnas.1609244114`.
- Beef carbon intensity: 59.6 kg CO2e/kg product, using the OECD (2025) agri-food carbon-footprint report's Poore and Nemecek (2018) beef-herd benchmark.
- Exchange rate: 6.8953 DKK/USD, the 2024 average USD/DKK rate used for this accounting conversion.
- Average pre-intervention beef price: computed directly from the estimation panel over pre-event beef observations.

The additional beef price equivalent of the carbon-price gap is:

```math
\Delta p_{USD/kg}
=
\frac{4.7 \times 59.6}{1000}.
```

Converted to DKK/kg:

```math
\Delta p_{DKK/kg}
=
\Delta p_{USD/kg} \times 6.8953.
```

Converted to a log price effect at the observed pre-period beef price:

```math
\tau_{gap}
=
\log\left(
\frac{\bar{p}_{pre} + \Delta p_{DKK/kg}}
{\bar{p}_{pre}}
\right).
```

The reverse-engineered carbon price implied by an estimated beef log effect is:

```math
\widehat{SCC}
=
\frac{
\left[\bar{p}_{pre}\left(\exp(\hat{\tau})-1\right)/6.8953\right]
\times 1000
}{59.6}.
```

The output graph `outputs/figures/sdid/beef_att_policy_calibration.png` plots beef ATT point estimates and 95 percent confidence intervals for DiD and SDiD, with a horizontal reference line at `tau_gap`. The graph `outputs/figures/sdid/event_study_beef_policy_calibration.png` repeats the reference line for the beef DiD event study and compares it to the latest available post-period event-study estimate. The discussion file `docs/beef_carbon_price_calibration.md` reports the arithmetic, assumptions, reverse-engineered tax values, and interpretation.

## Output Structure

Processed data and diagnostics:

- `data/processed/products.csv`: normalized product-price records.
- `data/processed/commodity_panel.csv`: model-ready panel.
- `outputs/diagnostics/panel_balance.csv`: panel-level sample settings and counts.
- `outputs/diagnostics/panel_commodity_counts.csv`: commodity and treatment support.
- `outputs/diagnostics/panel_period_support.csv`: period-by-treatment support.

DiD outputs:

- `outputs/models/did/ate.csv`: all-treated DiD estimate.
- `outputs/models/did/heterogeneity.csv`: treated-commodity DiD estimates.
- `outputs/models/did/event_study.csv`: all-treated event-study estimates.
- `outputs/models/did/event_study_<group>.csv`: subgroup event-study estimates.
- `outputs/models/did/pretrend_summary.csv`: individual pre-period diagnostic summary.
- `outputs/models/did/aggregate_trends.csv`: aggregate normalized price trends.
- `outputs/figures/did/event_study_overall.png`: all-treated event-study plot.
- `outputs/figures/did/event_study_<group>.png`: subgroup event-study plots.
- `outputs/figures/did/aggregate_trends.png`: treated/control aggregate trends.
- `outputs/tables/did/did_results.tex`: publication-style DiD table.

SDiD outputs:

- `outputs/models/sdid/synthetic_did.csv`: all-treated SDiD estimate.
- `outputs/models/sdid/synthetic_did_<group>.csv`: subgroup SDiD estimates.
- `outputs/models/sdid/synthetic_did_*_metadata.csv`: sample and inference metadata.
- `outputs/models/sdid/synthetic_did_*_trends.csv`: treated and synthetic paths.
- `outputs/models/sdid/synthetic_did_*_unit_weights.csv`: donor weights.
- `outputs/models/sdid/synthetic_did_*_time_weights.csv`: pre-period weights.
- `outputs/models/sdid/skipped_sdid_groups.csv`: subgroups skipped because support is insufficient.
- `outputs/models/sdid/beef_policy_calibration.csv`: beef carbon-price calibration estimates.
- `outputs/figures/sdid/synthetic_did_trends.png`: all-treated SDiD trend plot.
- `outputs/figures/sdid/synthetic_did_<group>_trends.png`: subgroup SDiD trend plots.
- `outputs/figures/sdid/beef_att_policy_calibration.png`: beef ATT vs carbon-price-gap reference.
- `outputs/figures/sdid/event_study_beef_policy_calibration.png`: beef event study vs carbon-price-gap reference.
- `outputs/tables/sdid/synthetic_did_results.tex`: publication-style SDiD table.

All graph titles are intentionally omitted; captions should be supplied in paper, slides, or figure notes.

## Tests

Run:

```bash
$env:PYTHONPATH="src"; py -3 -m unittest discover -s tests
```

The test suite covers taxonomy, data-source fixtures, panel construction, estimator outputs, split output directories, LaTeX table generation, and smoke tests for the full fixture pipeline.

## Caveats

These are announcement effects, not realized statutory tax effects. The analysis uses supermarket price histories and deterministic commodity classification; mixed products and edge-case product names should receive manual review before paper submission. The beef carbon-price calibration is a transparent back-of-the-envelope accounting exercise, not a structural pass-through model.
