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

The pipeline is designed around the `Herover/heissepreise` ecosystem and Danish grocery data from `dagligepriser.dk`. Raw downloaded files are cached under `data/raw/` and intentionally ignored by Git. A deterministic fixture mode is included so the whole pipeline and tests run offline.

## Pipeline

Install dependencies:

```bash
py -3 -m pip install -r requirements.txt
```

Run the full offline fixture pipeline:

```bash
$env:PYTHONPATH="src"; py -3 main.py all --fixture
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
- `data/processed/commodity_panel.csv`: balanced model-ready panel.
- `outputs/models/ate.csv`: TWFE ATE estimate.
- `outputs/models/heterogeneity.csv`: subtype ATE estimates.
- `outputs/models/event_study.csv`: event-study coefficients.
- `outputs/figures/event_study_overall.png`: event-study plot.
- `outputs/tables/ate_results.tex`: LaTeX result table.

Generated data and outputs are ignored by Git except placeholder directories.

## Econometric Specification

The main model estimates log prices with product-store fixed effects and period fixed effects:

```text
log(price_it) = beta * Treated_i * Post_t + unit FE_i + period FE_t + error_it
```

The event-study model estimates treated relative-time effects and omits the pre-event period `-1` as reference. Standard errors are clustered by product-store unit.

## Caveats

This project estimates announcement effects, not realized statutory tax effects. Product classification is deterministic and transparent, but mixed meat products should receive manual review before paper-grade results. The maximum balanced pre/post period depends on grocery data coverage around 2024-06-24.
