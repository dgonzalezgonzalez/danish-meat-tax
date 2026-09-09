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
| `outputs/models/stata/country_sdid_estimate.csv` | Country-level Danish beef-price SDiD estimate and inference. |
| `outputs/models/stata/country_sdid_series.csv` | Danish and synthetic country-level beef-price series. |
| `outputs/models/stata/beef_trade_pair_sdid_estimate.csv` | Denmark-importer beef-trade SDiD estimate with placebo inference. |
| `outputs/models/stata/beef_trade_pair_sdid_bootstrap_estimate.csv` | Same beef-trade ATT with unit-cluster bootstrap inference. |
| `outputs/models/stata/beef_trade_pair_sdid_series.csv` | Denmark-importer and synthetic beef-import series. |
| `outputs/models/stata/scc_meta_summary.csv` | Pooled SCC and implied price-gap interval. |
| `outputs/models/stata/beef_policy_calibration.csv` | Three ATT estimates and SCC calibration band. |

## Production and calibration additions

`eurostat_bovine_slaughter.csv` retains JSON-stat dimensions (`freq`, `meat`, `meatitem`, `unit`, `geo`, `time` as supplied), numeric `value`, and source `flag`. Missing source values remain blank. Stata selects B1000/SLAUGHT/M and THS_T or THS_HD. Production result fields are specification, measure, att, se, low, high, p_value, pre_rmse, observations, units, pre_months, post_months. Exact samples and treated/weighted-donor series are exported per specification.

`calibration_scenarios.csv` stores persistence, taxable_share, incremental_pass_through, damage_dkk_kg, announcement_dkk_kg, implementation_dkk_kg, remaining_gap_dkk_kg, conf_low, conf_high, sensitivity_low, and sensitivity_high. SCC and tax inputs are recorded in `scc_meta_summary.csv`. All monetary levels use the common 2024-price approximation. `scc_leave_one_out.csv` records the excluded study and remaining mean. `scc_meta_summary.csv` also includes the directly dated 2030 subset and the Danish net-price conversion.

## Preferred-estimate calibration grids

`calibration_surfaces.csv` has 10,404 rows: `panel` identifies taxable shares 0.25, 0.50, 0.75, and 1; `x`/`persistence` and `y`/`incremental_pass_through` range from zero to one in .02 steps. `taxable_share` is constant within each panel. `beta`, `beta_low`, and `beta_high` preserve the preferred CPI DiD estimate and HAC interval. `pre_price_dkk_kg` anchors the proportional estimate to grocery levels. Damage, announcement, implementation, remaining-gap, and `conf_low`/`conf_high` fields are DKK/kg. The `conf_low`/`conf_high` fields retain the coefficient-only bounds. Figure 4 uses `sensitivity_low`/`sensitivity_high`, the combined SCC-and-coefficient pointwise percentile bounds in DKK/kg. `calibration_scenarios.csv` contains the full 27-row coarse parameter cube with matching amount and confidence fields.

`production_descriptive_statistics.csv` records sample (`all`, `denmark`, `donors`), measure (`THS_T`, `THS_HD`), country-month observation count, mean, sample standard deviation, quartiles, and median from the exact main estimation samples.

`calibration_joint_draws.csv` contains 10,000 paired draws: `draw`, `pooled_mean` (SCC in 2024 USD/tCO2), `beta_draw` (log-price effect), `damage_draw` and `announcement_draw` (DKK/kg). `scc_meta_draws.csv` preserves the SCC draws before independent coefficient variation is added.
