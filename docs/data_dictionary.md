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
| `period` | Daily or weekly panel period. |
| `event_period` | Period containing the 2024-06-24 announcement. |
| `relative_time` | Period index relative to event; event period is excluded in balanced panels. |
| `post` | Indicator for periods after announcement. |
| `did` | `treated x post`. |
| `log_price` | Natural log of normalized price. |
| `event_date` | Main event date, `2024-06-24`. |
| `frequency` | `daily` or `weekly`. |

The real `dagligepriser.dk` source stores many product objects with a nested `priceHistory` array. Processing expands each `priceHistory` entry into a separate row before writing `products.csv`. The main panel excludes `non_food`, `unknown`, and rows without usable normalized prices.

## Diagnostics

| File | Meaning |
|---|---|
| `outputs/diagnostics/panel_balance.csv` | Main panel dimensions and filter settings. |
| `outputs/diagnostics/panel_commodity_counts.csv` | Units/rows by commodity, treatment group, and treated status. |
| `outputs/diagnostics/panel_period_support.csv` | Units/rows by relative period and treated status. |
| `outputs/models/pretrend_summary.csv` | Pre-event event-study coefficient diagnostics. |
| `outputs/models/aggregate_trends.csv` | Aggregate normalized price trends by treatment/control series. |
