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
| `price` | Observed nominal price. |
| `currency` | Currency, default `DKK` when source omits it. |
| `unit` | Source unit/package field where available. |
| `commodity` | Normalized commodity category. |
| `treated` | Policy-exposure indicator. |
| `treatment_group` | Treatment subtype or control group. |
| `policy_confidence` | `core`, `livestock_scope`, `sensitivity`, `control`, `ambiguous_mixed`, or `unknown`. |
| `matched_terms` | Classifier terms that triggered assignment. |
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
| `log_price` | Natural log of price. |
| `event_date` | Main event date, `2024-06-24`. |
| `frequency` | `daily` or `weekly`. |
