---
status: completed
created: 2026-06-09
type: research-implementation
owner: codex
---

# Food-Only Normalized Panel and Parallel-Trends Estimation Plan

## Summary

The project should move from a broad grocery-product panel to a food-only econometric sample. The current Codex baseline downloads and expands `dagligepriser.dk` / `Herover/heissepreise` product price histories, but it still keeps many `unknown` products, uses package-level prices, and selects a symmetric pre/post window by default. Those choices inflate non-food controls, make treatment/control composition weak, and can damage pre-period event-study behavior.

This plan restores the intended design: treated commodities are products derived from cattle/cows, pigs, sheep, and lamb; controls are other identified food items. The panel should use normalized prices, ideally DKK per kilogram or DKK per liter where weight conversion is not meaningful, and `log(normalized_price)`. The estimation stage should produce TWFE ATE tables and event-study plots with explicit pretrend diagnostics before results are interpreted.

---

## Current Baseline

- Workspace restored to latest Codex commit: `3b4891d docs: add real TWFE event study outputs`.
- Uncommitted edits from the other agent were discarded in:
  - `src/danish_meat_tax/estimators.py`
  - `src/danish_meat_tax/output.py`
  - `src/danish_meat_tax/pipeline.py`
- Untracked clean-output directories from that run were removed:
  - `outputs/figures_clean/`
  - `outputs/models_clean/`
  - `outputs/tables_clean/`

---

## Requirements

- Use more periods and more food items, even if the final panel is not symmetric around the 2024-06-24 announcement.
- Avoid non-food and unresolved `unknown` products in the econometric sample.
- Keep food controls broad: fish, seafood, poultry if coded as control/sensitivity by spec choice, eggs, fruit, vegetables, grains, bread, oils, sweets, beverages, plant protein, and other identified food groups.
- Treat products derived from cattle/cows, pigs, sheep, and lamb:
  - beef and veal
  - pork
  - lamb, sheep, and goat if present
  - dairy should be handled explicitly as livestock-exposed because dairy cattle emissions are within the institutional policy channel, not silently pooled with controls
- Normalize prices before logs:
  - target variable: `normalized_price_dkk_per_kg` where product quantity can be converted to kilograms
  - allow `normalized_price_dkk_per_liter` or a `normalized_price_unit` field for liquids such as milk
  - exclude or flag products where unit normalization is not defensible
- Add download/cache behavior so reruns reuse prior raw data and avoid needless full replacement.
- Produce TWFE ATE and event-study outputs for:
  - all treated commodities
  - beef/veal
  - pork
  - lamb/sheep/goat
  - dairy/livestock-derived dairy sensitivity or main spec, depending on final taxonomy decision
- Produce diagnostics that make parallel-trends assessment visible before interpreting estimates.

---

## Key Decisions

1. **Food-only sample is default for real estimation.**
   `unknown` should not be a control group. It can stay in processed data for audit, but panel construction should default to `food_status == "food"` and exclude `food_status in {"non_food", "unknown"}` from model-ready panels.

2. **Treatment taxonomy separates policy exposure from commodity labels.**
   `commodity` should describe product class; `treatment_group` should describe econometric treatment. Dairy needs an explicit decision because the policy taxes dairy-cattle emissions, but retail dairy is not the same market as meat. Recommended default: include dairy as a separate livestock-exposed treated/sensitivity group, and report main results both with and without dairy.

3. **Unbalanced wider window beats symmetric small window for this phase.**
   Keep all available pre/post periods after applying minimum support rules. Record counts by relative period. Symmetric panels can remain a robustness option, not the default.

4. **Normalized price is the analysis price.**
   Raw package price should remain for provenance, but `log_price` should use normalized DKK/unit. Rows with unparsed units should be excluded from main econometric samples and counted in diagnostics.

5. **Pretrend diagnostics are first-class outputs.**
   Event-study plots are not enough. Add pre-period coefficient tables, joint pretrend tests when feasible, and commodity-level aggregate trend plots for treated vs controls.

---

## Implementation Units

### U1: Raw Data Cache and Incremental Download

**Files:**
- `src/danish_meat_tax/data_sources/heissepreise.py`
- `src/danish_meat_tax/pipeline.py`
- `tests/test_heissepreise_source.py`

**Design:**
- Keep existing timestamped raw downloads.
- Add a stable cache manifest under `data/raw/` with source URL, retrieved timestamp, content hash, record count, and local raw file path.
- Before downloading, check whether a cached source file exists and is usable.
- Add CLI controls:
  - `--refresh` to force download
  - `--source-url` to override source
  - `--max-age-days` to refresh stale cache
- Preserve fixture mode unchanged.

**Test Scenarios:**
- Happy path: cached raw file exists and `--refresh` is false; downloader returns cache without network fetch.
- Happy path: `--refresh` true; downloader writes a new timestamped file and updates manifest.
- Edge case: manifest points to missing file; downloader falls back to fresh download.
- Error path: all source URLs fail and no cache exists; error lists attempted sources.

**Verification:**
- Rerunning `main.py download` should not create duplicate 300MB raw files unless cache is stale or refresh is requested.

---

### U2: Food Taxonomy and Non-Food Exclusion

**Files:**
- `src/danish_meat_tax/policy_taxonomy.py`
- `src/danish_meat_tax/normalize_products.py`
- `docs/data_dictionary.md`
- `tests/test_policy_taxonomy.py`
- `tests/test_commodity_classifier.py`

**Design:**
- Extend `TreatmentAssignment` with `food_status` and `analysis_role`.
- Expand Danish and English terms for food groups using source names/categories.
- Classify:
  - `treated_livestock_meat`: beef/veal, pork, lamb/sheep/goat
  - `treated_livestock_dairy`: dairy products, separately flagged
  - `control_food`: identified non-treated food groups
  - `exclude_non_food`: household, personal care, pet, alcohol if not desired, tobacco, cleaning, pharmacy, etc.
  - `exclude_unknown`: unresolved products
- Keep matched terms so exclusions are auditable.

**Test Scenarios:**
- Happy path: Danish beef, pork, lamb, milk, cheese, bread, rice, apples, fish classify correctly.
- Edge case: mixed meals containing meat are flagged `ambiguous_mixed` and not silently treated as clean controls.
- Edge case: household/non-food product names classify as `exclude_non_food`.
- Error path: empty product names become `exclude_unknown`.

**Verification:**
- Processed products include counts by `food_status`, `analysis_role`, `commodity`, and `treatment_group`.

---

### U3: Unit Parsing and Normalized Prices

**Files:**
- `src/danish_meat_tax/normalize_products.py`
- `docs/data_dictionary.md`
- `tests/test_pipeline_smoke.py`
- `tests/test_commodity_classifier.py`

**Design:**
- Parse source quantity/unit fields and package text from product names.
- Convert common units:
  - grams to kg
  - kilograms to kg
  - milliliters to liters
  - liters to liters
  - pieces/counts remain excluded from normalized main sample unless a defensible mass unit is present
- Add fields:
  - `raw_price`
  - `raw_unit`
  - `quantity_value`
  - `quantity_unit`
  - `normalized_price`
  - `normalized_price_unit`
  - `normalization_status`
- Use normalized price for `log_price`.

**Test Scenarios:**
- Happy path: `500 g` at 40 DKK converts to 80 DKK/kg.
- Happy path: `1 kg` stays at price per kg.
- Happy path: `1 liter` milk converts to DKK/liter and is flagged as liquid unit.
- Edge case: multi-pack names are flagged for review unless explicit total mass is parsed.
- Error path: no parseable unit yields `normalization_status == "missing_unit"` and row excluded from main model.

**Verification:**
- `data/processed/products.csv` preserves raw package price and normalized price; `commodity_panel.csv` uses normalized price.

---

### U4: Wider Food-Only Panel Builder

**Files:**
- `src/danish_meat_tax/panel_builder.py`
- `src/danish_meat_tax/pipeline.py`
- `tests/test_panel_builder.py`

**Design:**
- Add panel filters:
  - `--food-only` default true for real data
  - `--include-dairy-as-treated` default true for broad policy-exposure spec
  - `--exclude-unknown` default true
  - `--min-pre-periods`
  - `--min-post-periods`
  - `--max-pre-periods` optional
  - `--max-post-periods` optional
  - `--symmetric-window` optional
- For weekly panels, keep all observed weeks satisfying min support unless symmetric mode is requested.
- Diagnostics should report period counts, unit support distribution, rows dropped by reason, and counts by store/commodity/treatment group.

**Test Scenarios:**
- Happy path: unbalanced panel keeps more post than pre periods when available.
- Happy path: `--symmetric-window` reproduces old equal pre/post behavior.
- Edge case: unit with post only is dropped; unit with at least configured pre/post support is kept.
- Error path: no treated or no food controls remain; builder fails with clear message.

**Verification:**
- Real weekly panel should include more than the current 34 pre + 34 post window when data allow it, and should show near-zero `unknown` in model sample.

---

### U5: Parallel-Trends Diagnostics

**Files:**
- `src/danish_meat_tax/estimators.py`
- `src/danish_meat_tax/output.py`
- `tests/test_estimators.py`
- `tests/test_outputs.py`

**Design:**
- Keep TWFE residualized OLS with unit and period fixed effects.
- Add pretrend output:
  - event-study coefficient CSV with `pre_period` indicator
  - pre-period coefficient summary
  - joint test placeholder or implemented Wald test for all pre-event coefficients excluding reference
  - aggregate trend plot by treatment/control group before model estimation
- Add event-study plots with clear pre/post split and reference period.
- Ensure group-specific event studies use same control-food sample and not `unknown` controls.

**Test Scenarios:**
- Happy path: event-study result includes relative-time rows, confidence intervals, and pre-period flag.
- Happy path: group-specific estimates use selected treatment group vs food controls.
- Edge case: a group with too few treated units is skipped with metadata, not fatal to full run.
- Error path: no estimable pre-period coefficients returns diagnostic status instead of crashing output generation.

**Verification:**
- Outputs include enough artifacts to inspect parallel trends before reading ATE table.

---

### U6: Main Pipeline, Docs, and Reproducibility

**Files:**
- `main.py`
- `scripts/run_all.py`
- `README.md`
- `docs/methodology.md`
- `docs/policy/policy_summary.md`
- `docs/data_dictionary.md`
- `tests/test_pipeline_smoke.py`

**Design:**
- Add a main real-data recipe:
  - cache/download
  - process with food taxonomy and normalized prices
  - build wide weekly food-only panel
  - estimate TWFE/event studies
  - generate figures/tables/diagnostics
- Document main vs sensitivity specifications:
  - meat-only treated
  - meat plus dairy livestock-exposed treated
  - poultry as control or sensitivity depending on final scope
  - symmetric vs wider unbalanced window
- Document that raw large files remain ignored; small final tables/figures may be force-added if desired.

**Test Scenarios:**
- Integration: fixture `main.py all --fixture --frequency weekly` still runs end-to-end.
- Integration: fixture with food-only and normalized-price path yields non-empty model outputs.
- Error path: process/panel stage reports missing normalized price rather than producing invalid logs.

**Verification:**
- README commands reproduce full pipeline from a clean checkout plus cached/downloaded data.

---

## System-Wide Impact

- **Data size:** food-only filtering should reduce model panel size while improving relevance. Raw cache remains large and ignored.
- **Econometric sample:** estimates will not be comparable to previous committed outputs because controls and price variable change.
- **Policy interpretation:** dairy must be labeled carefully as livestock-exposed, not meat. Main tables should make this distinction visible.
- **Backwards compatibility:** fixture mode and old symmetric panel option remain available for tests and robustness.
- **Reproducibility:** diagnostics become part of the output contract, not ad hoc notebook inspection.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Unit parsing drops many food items | Report `normalization_status` counts; allow sensitivity using package price only for products without parseable units, clearly labeled. |
| Food classifier misses Danish terms | Keep transparent matched terms and add classifier tests as new examples are found. |
| Dairy treatment choice changes results | Report meat-only and meat-plus-dairy specifications separately. |
| Pretrends remain poor after cleanup | Add aggregate food-index plots, restrict to stable stores/commodities, and consider matched controls or official CPI validation as follow-up. |
| Huge raw files slow reruns | Manifest cache and no-refresh default avoid repeated downloads. |

---

## Documentation / Operational Notes

- Update README with the restored baseline note only if needed; avoid documenting disliked intermediate agent output.
- Keep large raw and processed files ignored.
- After implementation, rerun real-data TWFE and commit code plus small result artifacts.
- Push to `origin/main` only after tests and real estimation outputs are regenerated.

---

## Sources & References

- Existing plan: `docs/plans/2026-06-08-001-research-danish-meat-tax-plan.md`
- Pipeline entry: `main.py`
- Downloader: `src/danish_meat_tax/data_sources/heissepreise.py`
- Normalizer: `src/danish_meat_tax/normalize_products.py`
- Taxonomy: `src/danish_meat_tax/policy_taxonomy.py`
- Panel builder: `src/danish_meat_tax/panel_builder.py`
- Estimators: `src/danish_meat_tax/estimators.py`
- Outputs: `src/danish_meat_tax/output.py`
- Policy summary: `docs/policy/policy_summary.md`
