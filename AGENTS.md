# Repository Guidelines

## Project Structure & Module Organization

Core Python code lives in `src/danish_meat_tax/`. Keep pipeline orchestration in `pipeline.py`, configuration and paths in `config.py`, estimators in `estimators.py`, and source-specific ingestion under `data_sources/`. Thin entry points live in `main.py` and `scripts/`. Tests mirror package behavior in `tests/test_*.py`. Methodology and policy notes belong in `docs/`; the publication source is `paper/main.tex`. Raw inputs, processed panels, and generated artifacts are written to `data/` and `outputs/` and are mostly ignored by Git.

## Build, Test, and Development Commands

Run commands from the repository root in PowerShell:

```powershell
py -3 -m pip install -r requirements.txt
$env:PYTHONPATH="src"; py -3 main.py all --fixture
$env:PYTHONPATH="src"; py -3 -m unittest discover -s tests
```

The fixture pipeline is the preferred offline smoke test; it exercises ingestion through tables and figures without downloading data. For real data, run the stages in order: `download`, `process`, `panel`, `estimate`, then `outputs`. Use `py -3 main.py panel --frequency monthly` for the default analysis frequency.

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, PEP 8 naming, type hints on public interfaces, and `from __future__ import annotations` where forward annotations help. Use `snake_case` for functions, modules, variables, and generated filenames; use `PascalCase` for classes and `UPPER_CASE` for constants. Prefer `pathlib.Path` over string path manipulation. No formatter or linter is configured, so keep imports grouped and changes consistent with neighboring code.

## Testing Guidelines

Tests use the standard-library `unittest` framework. Name files `test_<area>.py`, classes `<Area>Test`, and methods `test_<expected_behavior>`. Add focused unit tests for transformations or estimators and update the fixture smoke test when pipeline stages or output contracts change. There is no formal coverage threshold; cover regressions and important branches explicitly.

## Commit & Pull Request Guidelines

Recent commits use concise, imperative subjects such as `Fix ATT definition and SDiD table stats`; `feat:` prefixes also appear for new capabilities. Keep each commit scoped and describe the observable change. Pull requests should explain the research or code rationale, list validation commands, link relevant issues, and identify changed data assumptions. Include regenerated tables or figures when output changes, but do not commit raw or large processed datasets.

## Data and Reproducibility

Do not embed credentials or machine-specific absolute paths. Document new external sources and normalization assumptions in `docs/` and preserve an offline fixture path for reproducible tests.
