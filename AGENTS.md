# Repository Guidelines

## Project Structure & Module Organization

Core Python code lives in `src/danish_meat_tax/`. Keep pipeline orchestration in `pipeline.py`, configuration and paths in `config.py`, all analytical estimation, descriptive statistics, simulations, and most figure construction in `scripts/stata/`, and source-specific ingestion under `data_sources/`. Thin entry points live in `main.py` and `scripts/`. Tests mirror package behavior in `tests/test_*.py`. Methodology and policy notes belong in `docs/`; the publication source is `paper/main.tex`. Raw inputs, processed panels, and generated artifacts are written to `data/` and `outputs/` and are mostly ignored by Git.

## Build, Test, and Development Commands

Run commands from the repository root in PowerShell:

```powershell
py -3 -m pip install -r requirements.txt
$env:PYTHONPATH="src"; py -3 main.py all --fixture
$env:PYTHONPATH="src"; py -3 -m unittest discover -s tests
```

The fixture pipeline is the preferred offline smoke test; it exercises ingestion through the Stata input contract without downloading data or fabricating analytical estimates. For real data, run the stages in order: `download`, `process`, `panel`, `estimate`, then `outputs`. Use `py -3 main.py panel --frequency monthly` for the default analysis frequency.

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, PEP 8 naming, type hints on public interfaces, and `from __future__ import annotations` where forward annotations help. Use `snake_case` for functions, modules, variables, and generated filenames; use `PascalCase` for classes and `UPPER_CASE` for constants. Prefer `pathlib.Path` over string path manipulation. No formatter or linter is configured, so keep imports grouped and changes consistent with neighboring code.

## Testing Guidelines

Tests use the standard-library `unittest` framework. Name files `test_<area>.py`, classes `<Area>Test`, and methods `test_<expected_behavior>`. Add focused unit tests for transformations or estimators and update the fixture smoke test when pipeline stages or output contracts change. There is no formal coverage threshold; cover regressions and important branches explicitly.

## Commit & Pull Request Guidelines

Recent commits use concise, imperative subjects such as `Fix ATT definition and SDiD table stats`; `feat:` prefixes also appear for new capabilities. Keep each commit scoped and describe the observable change. Pull requests should explain the research or code rationale, list validation commands, link relevant issues, and identify changed data assumptions. Include regenerated tables or figures when output changes, but do not commit raw or large processed datasets.

## Data and Reproducibility

Do not embed credentials or machine-specific absolute paths. Document new external sources and normalization assumptions in `docs/` and preserve an offline fixture path for reproducible tests.

## Publication invariants

Beef is the sole treatment of interest. Never use livestock-exposed meat, poultry, eggs, dairy, or ambiguous mixed livestock products as beef controls. Preserve source flags and missing observations in official production data; missing slaughter is not zero. The primary production comparison is Denmark against the other EU27 countries, with July 2024 treatment and April 2023--September 2025 support. All analytical computation remains in Stata. Python may render the calibration surface figure from Stata-computed grids, as requested by the author. Python and PowerShell may download, classify, normalize, reshape, and orchestrate.

Run `scripts/stata/master.do` after preprocessing to rebuild every publication analysis. Record source snapshots and hashes in `data/reference/replication_input_manifest.json`; never refresh the manifest merely to make a mismatch pass. The paper's tables contain formatted results copied from Stata CSVs, so reconcile them whenever inputs change. See `docs/output_map.md` for all tables, figures, and otherwise unmapped in-text numbers.

Treat the April/July 2024 nitrate-derogation change as an unresolved confound. Do not interpret uncertain slaughter estimates as proof of contraction or pooled SCC sensitivity envelopes as sampling confidence intervals. Statutory 120/300 DKK rates are quoted in 2022 prices; calibration converts them to 2024 DKK. Separate announcement persistence from additional implementation pass-through to prevent double counting.

Write academic artifacts in normal scholarly prose, following the question, mechanism, design, evidence, and implications. Conversation brevity does not apply to the paper. Preserve existing unrelated work and never invent author affiliations, data rights, repository licenses, or preservation commitments.

Use the official CPI DiD (Table 2, column 2; HAC with two lags) as the preferred price estimate. Keep dataset identifiers and random seeds in replication documentation, not manuscript prose. Empirical result tables use specification columns and ATT rows with parenthesized standard errors.

The country-price robustness check uses Eurostat beef-and-veal HICP for Denmark against the other EU27 countries, April 2023--September 2025, with July 2024 treatment and placebo SDiD inference. It replaces the carcass-price check; do not reintroduce carcass prices as consumer prices. This changes the control group, not the underlying Danish statistical provider. The Commission beef-trade analysis and grocery level-price anchor for SCC calibration remain separate.
