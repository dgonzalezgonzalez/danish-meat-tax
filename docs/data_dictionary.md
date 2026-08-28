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
