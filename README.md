# Danish Meat Tax Announcement Price Effects

This repository studies whether Denmark's 2024-06-24 announcement of a livestock carbon tax affected supermarket consumer prices for meat products.

## Policy Summary

Denmark's Green Tripartite agreement was announced on 2024-06-24. Public coverage described it as a world-first carbon tax on livestock emissions. The policy is not a retail meat tax: it targets agricultural greenhouse-gas emissions from livestock production, with later implementation and transition rules.

Treatment coding follows that institutional design:

- Beef/cattle and pork/pig: core treated groups.
- Lamb/sheep/goat: livestock-exposed, not a clean control.
- Poultry: sensitivity group because it is livestock but less central to the announcement and emissions intensity.
- Fish/seafood and non-meat foods: controls.

See `docs/policy/policy_summary.md` for source links and institutional details.

## Data

The pipeline is designed around the `Herover/heissepreise` ecosystem and Danish grocery data from `dagligepriser.dk`. Raw downloaded files are cached under `data/raw/` and intentionally ignored by Git. A cache manifest prevents repeated full downloads unless `--refresh` is passed or the cache is stale. The canonical Danish source is large: a 2026-06-09 pull of `latest-canonical.json` contained about 2.07 million price-history rows before quality filters.

The downloader preserves source product objects and the processing stage expands each `priceHistory` entry into one product-date price row. Processing also assigns food/treatment taxonomy fields and normalizes prices to DKK/kg or DKK/liter when source quantity and unit information permit. A deterministic fixture mode is included so the whole pipeline and tests run offline.

## Pipeline

Install dependencies:

```bash
py -3 -m pip install -r requirements.txt
```

Run the full offline fixture pipeline:

```bash
$env:PYTHONPATH="src"; py -3 main.py all --fixture
```

Run against real Danish grocery data:

```bash
$env:PYTHONPATH="src"; py -3 main.py download
$env:PYTHONPATH="src"; py -3 main.py process
$env:PYTHONPATH="src"; py -3 main.py panel --frequency monthly --unit-level product_store --min-pre-periods 1 --min-post-periods 1
$env:PYTHONPATH="src"; py -3 main.py estimate
$env:PYTHONPATH="src"; py -3 main.py outputs
```

Useful real-data options:

```bash
$env:PYTHONPATH="src"; py -3 main.py download --refresh
$env:PYTHONPATH="src"; py -3 main.py panel --frequency weekly --symmetric-window
$env:PYTHONPATH="src"; py -3 main.py panel --frequency weekly --unit-level product_store
$env:PYTHONPATH="src"; py -3 main.py panel --frequency weekly --dairy-as-control
$env:PYTHONPATH="src"; py -3 main.py panel --frequency weekly --include-unknown --include-non-food
```

Run individual stages:

```bash
$env:PYTHONPATH="src"; py -3 main.py download --fixture
$env:PYTHONPATH="src"; py -3 main.py process
$env:PYTHONPATH="src"; py -3 main.py panel --frequency daily
$env:PYTHONPATH="src"; py -3 main.py estimate
$env:PYTHONPATH="src"; py -3 main.py outputs
```

Run tests:

```bash
$env:PYTHONPATH="src"; py -3 -m unittest discover -s tests
```

## Outputs

- `data/processed/products.csv`: normalized product-price records.
- `data/processed/commodity_panel.csv`: model-ready food-only panel.
- `outputs/diagnostics/panel_commodity_counts.csv`: model sample composition.
- `outputs/diagnostics/panel_period_support.csv`: period-by-treatment support.
- `outputs/models/ate.csv`: TWFE ATE estimate.
- `outputs/models/heterogeneity.csv`: subtype ATE estimates.
- `outputs/models/event_study.csv`: event-study coefficients.
- `outputs/models/pretrend_summary.csv`: pre-period event-study diagnostic summary.
- `outputs/models/aggregate_trends.csv`: aggregate normalized price trends.
- `outputs/figures/event_study_overall.png`: overall event-study plot.
- `outputs/figures/aggregate_trends.png`: aggregate treated/control food-price trend plot.
- `outputs/tables/ate_results.tex`: LaTeX result table.
- `outputs/models/synthetic_did.csv`: synthetic DiD estimate.
- `outputs/figures/synthetic_did_trends.png`: treated and synthetic-control time series.
- `outputs/tables/synthetic_did_results.tex`: synthetic DiD LaTeX result table.

Large raw and processed data files are ignored by Git. Selected model, figure, table, and diagnostic artifacts are committed for review.

## Econometric Specification

The main model estimates log prices with product-store fixed effects and period fixed effects:

```text
log(normalized_price_it) = beta * Treated_i * Post_t + unit FE_i + period FE_t + error_it
```

The event-study model estimates treated relative-time effects and omits the pre-event period `-1` as reference. Standard errors are clustered by product-store unit. Monthly aggregation is the current main specification because it keeps the full post-announcement horizon while reducing weekly noise; daily and weekly panels are available as robustness frequencies.

By default, the econometric unit is `product_store`, which keeps the largest food cross-section available after normalization and treatment/control classification. Use `--unit-level commodity_store` for a smaller commodity-chain panel or `--unit-level commodity` for an all-store commodity panel. The panel keeps all available pre/post periods after food-only and normalized-price filters, retaining units with at least one pre and one post observation. Use `--symmetric-window` for the older equal-period design and `--require-complete-units` for a stricter complete-unit panel; both can be too restrictive for large price-history data where records are sparse rather than daily-complete.

## Caveats

This project estimates announcement effects, not realized statutory tax effects. Product classification is deterministic and transparent, but mixed meat products should receive manual review before paper-grade results. Dairy is coded as a separate livestock-exposed treatment by default because dairy-cattle emissions are inside the policy channel; `--dairy-as-control` provides a sensitivity sample.
