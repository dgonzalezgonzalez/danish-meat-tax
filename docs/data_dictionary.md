# Data Dictionary

## `data/processed/products.csv`

| Column | Meaning |
|---|---|
| `row_id` | Source row number within raw file. |
| `date` | Observed price date. |
| `store` | Supermarket or chain name. |
| `product_id` | Source product identifier or generated fallback. |
| `product_name` | Source product label. |
| `category_raw` | Source category/department field. |
| `price` | Observed nominal package price from the source. |
| `raw_price` | Copy of source package price before normalization. |
| `currency` | Currency, default `DKK` when source omits it. |
| `unit` | Source unit/package field where available. |
| `raw_unit` | Copy of the source unit field. |
| `quantity_value` | Parsed product quantity used for price normalization. |
| `quantity_unit` | Parsed product quantity unit. |
| `normalized_price` | Price normalized to a comparable physical unit. |
| `normalized_price_unit` | `dkk_per_kg`, `dkk_per_liter`, or blank when not normalized. |
| `normalization_status` | `ok`, `missing_unit`, or `unsupported_unit`. |
| `commodity` | Normalized commodity category. |
| `treated` | Policy-exposure indicator. |
| `treatment_group` | Treatment subtype or control group. |
| `policy_confidence` | `core`, `livestock_scope`, `sensitivity`, `control`, `ambiguous_mixed`, or `unknown`. |
| `matched_terms` | Classifier terms that triggered assignment. |
| `food_status` | `food`, `non_food`, or `unknown`. |
| `analysis_role` | Econometric role such as `treated_livestock_meat`, `treated_livestock_dairy`, `control_food`, `exclude_non_food`, or `exclude_unknown`. |
| `quality_flag` | Row-level quality status. |
| `unit_id` | Store-product panel identifier. |

## `data/processed/commodity_panel.csv`

Includes product columns above plus:

| Column | Meaning |
|---|---|
| `period` | Daily, weekly, monthly, or quarterly panel period. |
| `event_period` | Period containing the 2024-06-24 announcement. |
| `relative_time` | Period index relative to event; event period is excluded in balanced panels. |
| `post` | Indicator for periods after announcement. |
| `did` | `treated x post`. |
| `log_price` | Natural log of normalized price. |
| `event_date` | Main event date, `2024-06-24`. |
| `frequency` | `daily`, `weekly`, `monthly`, or `quarterly`. |

The real `dagligepriser.dk` source stores many product objects with a nested `priceHistory` array. Processing expands each `priceHistory` entry into a separate row before writing `products.csv`. The main panel excludes `non_food`, `unknown`, and rows without usable normalized prices.

## Diagnostics

| File | Meaning |
|---|---|
| `outputs/diagnostics/panel_balance.csv` | Main panel dimensions and filter settings. |
| `outputs/diagnostics/panel_commodity_counts.csv` | Units/rows by commodity, treatment group, and treated status. |
| `outputs/diagnostics/panel_period_support.csv` | Units/rows by relative period and treated status. |
| `outputs/models/stata/micro_estimates.csv` | Scraped-data DiD summary. |
| `outputs/models/stata/descriptive_statistics.csv` | Scraped-sample level-price and panel-support descriptives. |
| `outputs/models/stata/aggregate_descriptive_statistics.csv` | Official CPI descriptives for beef and donor series. |
| `outputs/models/stata/aggregate_estimates.csv` | Official DiD and SDiD summaries. |
| `outputs/models/stata/micro_event_study.csv` | Scraped-data beef event-study coefficients. |
| `outputs/models/stata/aggregate_event_study.csv` | Official beef event-study coefficients. |
| `outputs/models/stata/country_sdid_estimate.csv` | Country-level Danish beef-and-veal HICP SDiD estimate and inference. |
| `outputs/models/stata/country_sdid_series.csv` | Danish and synthetic country-level log HICP series. |
| `outputs/models/stata/beef_trade_pair_sdid_estimate.csv` | Denmark-importer beef-trade SDiD estimate with placebo inference. |
| `outputs/models/stata/beef_trade_pair_sdid_bootstrap_estimate.csv` | Same beef-trade ATT with unit-cluster bootstrap inference. |
| `outputs/models/stata/beef_trade_pair_sdid_series.csv` | Denmark-importer and synthetic beef-import series. |
| `outputs/models/stata/scc_meta_summary.csv` | Pooled SCC and implied price-gap interval. |
| `outputs/models/stata/beef_policy_calibration.csv` | Three ATT estimates and SCC calibration band. |

## Production and calibration additions

`eurostat_bovine_slaughter.csv` retains JSON-stat dimensions (`freq`, `meat`, `meatitem`, `unit`, `geo`, `time` as supplied), numeric `value`, and source `flag`. Missing source values remain blank. Stata selects B1000/SLAUGHT/M and THS_T or THS_HD. Production result fields are specification, measure, att, se, low, high, p_value, pre_rmse, observations, units, pre_months, post_months. Exact samples and treated/weighted-donor series are exported per specification.

`calibration_scenarios.csv` stores persistence, taxable_share, incremental_pass_through, damage_dkk_kg, announcement_dkk_kg, implementation_dkk_kg, remaining_gap_dkk_kg, conf_low, conf_high, sensitivity_low, and sensitivity_high. SCC and tax inputs are recorded in `scc_meta_summary.csv`. All monetary levels use the common 2024-price approximation. `scc_leave_one_out.csv` records the excluded study and remaining mean. `scc_meta_summary.csv` also includes the directly dated 2030 subset and the Danish net-price conversion.

## Preferred-estimate calibration grids

`calibration_surfaces.csv` has 10,404 rows: `panel` identifies taxable shares 0.25, 0.50, 0.75, and 1; `x`/`persistence` and `y`/`incremental_pass_through` range from zero to one in .02 steps. `taxable_share` is constant within each panel. `beta`, `beta_low`, and `beta_high` preserve the preferred CPI DiD estimate and HAC interval. `pre_price_dkk_kg` anchors the proportional estimate to grocery levels. Damage, announcement, implementation, remaining-gap, and `conf_low`/`conf_high` fields are DKK/kg. The `conf_low`/`conf_high` fields retain the coefficient-only bounds. Figure 4 uses `sensitivity_low`/`sensitivity_high`, the combined SCC, coefficient, and grocery-price pointwise percentile bounds in DKK/kg. `calibration_scenarios.csv` contains the full 27-row coarse parameter cube with matching amount and confidence fields.

`production_descriptive_statistics.csv` records sample (`all`, `denmark`, `donors`), measure (`THS_T`, `THS_HD`), country-month observation count, mean, sample standard deviation, quartiles, and median from the exact main estimation samples.

`calibration_joint_draws.csv` contains 10,000 paired draws: `draw`, `pooled_mean` (SCC in 2024 USD/tCO2), `beta_draw` (log-price effect), `damage_draw` and `announcement_draw` (DKK/kg). `scc_meta_draws.csv` preserves the SCC draws before independent coefficient variation is added.


## Price resampling and joint calibration (September 2026)

- `price_benchmark_draws.csv`: 10,000 rows keyed by `draw`; `price_draw` is the two-month-block resampled arithmetic grocery mean; `price_block1` and `price_block4` are alternative block lengths. All prices are DKK/kg.
- `price_benchmark_summary.csv`: `block_months`, fixed original `point`, percentile `low`/`high`, draw `sd`, and original sample `observations`, `units`, and `months`.
- `scc_price_gap_draws.csv`: paired `pooled_mean` SCC and all price-draw fields, plus `gap_effective_120` and `gap_marginal_300` in log-price units. Percentiles refer to combined SCC/price sensitivity.
- `calibration_joint_draws.csv`: now also stores all three price-draw fields. `announcement_draw = price_draw*(exp(beta_draw)-1)`; the main two-month draw enters the surface bounds.
- `calibration_block_sensitivity.csv`: `block_months`, `low`, `high` for the full a=f=lambda=1 level gap in DKK/kg, holding the SCC and coefficient draws identical across block choices.
- `scc_literature_calibration.csv`: `source_gap_low/high_effective_120` and `source_gap_low/high_marginal_300` retain direct source-range mappings at the fixed central price. `log_price_gap_low/high_*` now contain simulated 2.5th–97.5th percentile SCC/price bounds, with missing bounds for the theory-only and lower-bound rows. Published `interval_low/high_usd_2024` retain their original definitions.

All resulting bounds condition on fixed lifecycle intensity, FX, tax rates, and independent draws across the three uncertainty sources. Neither `f` nor intensity is assigned a probability distribution.


## Eurostat country consumer-price replacement

`eu_beef_hicp_country_month_panel.csv` is decoded from the Eurostat JSON-stat snapshot: `geo` (EU country code), `country` (source label), `month` (YYYY-MM), `hicp` (index, 2015=100), `flag` (unaltered Eurostat status), `coicop` (CP01121, beef and veal), and `index_unit` (I15). EU and euro-area aggregates and non-EU countries are excluded. Missing values remain blank. Country completeness and positive-value selection occur in Stata, with no interpolation or zero filling.

`country_hicp_coverage.csv` records `geo`, `country`, `valid_months`, and `included` for the requested window. All 27 EU countries have 30 valid months. `country_hicp_estimation_sample.csv` preserves the exact 810-row sample, index values, flags, log outcome, monthly dates, country IDs, and treatment indicators.

`country_sdid_estimate.csv` now uses estimator label `country_sdid_HICP`; `pre_treated_average` is an index level, not a currency amount. `pre_rmse` is the root mean squared pre-treatment treated–synthetic gap after subtracting its pre-treatment mean. `country_sdid_series.csv` contains `month_id`, `synthetic`, `treated`, `post`, `gap`, and `synthetic_aligned` (raw synthetic series shifted by the pre-treatment mean gap for display); series and gaps are in log-index units. Output filenames and the single appendix figure are retained; the price source is replaced, with no additional price robustness figure. Trade definitions are unchanged.
