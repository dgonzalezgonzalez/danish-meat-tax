---
title: Danish Meat Tax Announcement Price Effects
type: research-pipeline
status: completed
created: 2026-06-08
---

# Danish Meat Tax Announcement Price Effects

## Summary

Build a reproducible empirical pipeline that studies whether Denmark's carbon tax announcement for livestock agriculture shifted supermarket consumer prices for meat commodities. The pipeline will document the policy, scrape or ingest product-level grocery price data, normalize products into a commodity panel, estimate TWFE DiD/event-study models around the announcement date, and export publication-ready figures, LaTeX tables, and README documentation.

---

## Problem Frame

Denmark announced the Green Tripartite agreement on 2024-06-24. Public coverage described it as a world-first carbon tax on livestock emissions, with cattle and pigs most salient, but the institutional policy design is broader than a retail meat tax: it taxes agricultural greenhouse gas emissions from livestock production, with implementation scheduled later and with deductions/transition rules. The empirical design should therefore estimate announcement effects on consumer prices rather than statutory pass-through from an already-active tax.

The treated product definition must be source-backed. The core treated set should include beef and pork because these categories are central in the announcement and livestock emissions base. Lamb/sheep/goat should not be excluded by default because official and technical policy material discuss livestock emissions beyond cattle and pigs. Poultry should be handled as a lower-intensity or secondary livestock category, not silently merged with untreated food controls. Fish/seafood and non-meat foods should remain controls unless later source review shows inclusion.

The repository is currently empty and not a Git repository locally. The implementation must first establish a project skeleton and connect it to `dgonzalezgonzalez/danish-meat-tax.git` before commit/push can succeed.

---

## Requirements

- **R1 Policy design memo:** Document the 2024-06-24 Green Tripartite announcement, later political/institutional milestones, implementation timing, tax base, livestock scope, and treated product coding rules.
- **R2 Raw data collection:** Use the named `Herover/heissepreise` resource where feasible, prioritizing Danish supermarket price snapshots/history from `dagligepriser.dk` or its data endpoints.
- **R3 Balanced panel window:** Construct a panel with the same number of periods before and after 2024-06-24, using the maximum balanced window supported by observed data coverage.
- **R4 Processed commodity panel:** Produce product/commodity-level panel data with price, date, store/supermarket, product metadata, normalized commodity category, treatment status, and treatment subtype.
- **R5 Econometrics:** Estimate TWFE DiD and event-study specifications at commodity/product level, clustered at the commodity or product level as appropriate.
- **R6 Heterogeneity:** Report overall treated effects and heterogeneity by affected commodity type: beef, pork, lamb/sheep/goat, poultry/other livestock when data supports it.
- **R7 Outputs:** Generate event-study plots, ATE LaTeX tables, diagnostics, and reproducible data dictionaries.
- **R8 Master runner:** Provide one main script that runs data collection, processing, estimation, output generation, and documentation checks.
- **R9 Documentation:** Write a detailed README covering policy summary, data pipeline, identification strategy, how to run, outputs, and limitations.
- **R10 Git handoff:** Commit and push changes to the public GitHub repository once implementation is complete and local Git state is valid.

---

## Assumptions

- The primary intervention date is 2024-06-24, the date of the Green Tripartite announcement; later dates such as broad parliamentary agreement in November 2024 should be robustness/event-marker checks, not the main treatment date unless the policy memo finds stronger evidence.
- Unit of analysis is product/commodity-by-date, with store retained as a dimension and possibly a fixed effect; if identical products appear across stores, the processed data can support product-store and commodity-store panels.
- Daily prices are preferred. If data gaps are large, weekly aggregation is acceptable and should be documented before estimation.
- Treatment is assigned by product commodity category, not by observed price change, keyword alone, or supermarket department alone.
- The core deliverable is a reproducible research repo, not a finished academic paper.

---

## Scope Boundaries

### In Scope

- Policy-source review for Denmark's livestock carbon tax announcement.
- Scraped/downloaded supermarket price microdata and reproducible local cache.
- Commodity classification for meat products and clean controls.
- TWFE DiD, event-study plots, heterogeneity estimates, and LaTeX result tables.
- README and pipeline documentation.

### Deferred to Follow-Up Work

- Synthetic control or matrix completion estimators.
- Full pass-through model tied to producer-level emissions intensity.
- Cross-country placebo comparisons.
- Manual product taxonomy curation beyond a transparent first-pass classifier and documented overrides.

### Out of Scope

- Estimating welfare, emissions, or consumption changes.
- Legal advice about the tax.
- Claims about realized statutory tax effects after implementation unless post-implementation price data are available.

---

## Key Technical Decisions

| Decision | Rationale |
|---|---|
| Use 2024-06-24 as main event date | This captures the announcement effect requested by the user and matches the official Green Tripartite announcement timing. |
| Treat "livestock meat" as policy-exposed, with subtypes | Official design is production-emissions-based, not a retail list of beef/pork only. Subtypes preserve the user's beef/pork focus while allowing lamb and other livestock to be checked. |
| Keep poultry as secondary/low-intensity treated or sensitivity group | Poultry is livestock but less central to public coverage and emissions intensity. Separating it protects the control group from accidental contamination. |
| Build immutable raw-data cache plus processed outputs | Scraped price data can change or disappear. Raw snapshots make results reproducible. |
| Prefer weekly balanced panel if daily sparsity is high | Grocery scraping can have missing dates/products. Weekly aggregation reduces noise while preserving event-study timing. |
| Use Python for pipeline and R or Python for econometrics, chosen after repo setup | Empty repo has no established stack. Python is natural for scraping/processing; R has strong DiD/table tooling. Final choice should favor reproducibility and available dependencies. |
| Export both model-ready data and presentation outputs | Makes the research auditable and lets future estimators reuse the panel. |

---

## High-Level Technical Design

Directional structure:

```text
raw policy/data sources
  -> source review + policy treatment taxonomy
  -> grocery price downloader/cache
  -> product normalization + commodity classification
  -> balanced panel builder
  -> TWFE/event-study estimators
  -> figures/tables/diagnostics
  -> README + data dictionary
```

Recommended repo shape:

```text
README.md
main.py or run_pipeline.R
requirements.txt / pyproject.toml and optional renv.lock
data/raw/
data/processed/
docs/policy/
docs/plans/
outputs/figures/
outputs/tables/
scripts/
src/
tests/
```

No large raw data files should be committed unless small and legally safe. Prefer `.gitignore` plus documented download/cache commands.

---

## Implementation Units

### U1: Repository Bootstrap And Configuration

**Files:** `README.md`, `.gitignore`, `pyproject.toml` or `requirements.txt`, `main.py`, `src/`, `scripts/`, `tests/`

**Purpose:** Establish reproducible project skeleton in the empty workspace and connect it to the GitHub remote when implementation begins.

**Dependencies:** None.

**Technical Design:** Choose Python-first unless execution research shows the data source or econometrics tooling strongly favors R. Add clear directories for raw data, processed data, outputs, source code, scripts, and tests.

**Test Scenarios:**
- Happy path: `main.py --help` or equivalent runner invocation reports available pipeline stages.
- Integration: fresh checkout can install dependencies and import project modules.
- Error path: runner fails with a clear message when required external data are missing.

**Verification:** Project has predictable structure and a single entry point before data logic is added.

---

### U2: Policy Source Review And Treatment Taxonomy

**Files:** `docs/policy/policy_summary.md`, `src/policy_taxonomy.py`, `tests/test_policy_taxonomy.py`

**Purpose:** Encode source-backed treatment categories and document the policy's institutional process.

**Dependencies:** U1.

**Technical Design:** Create a taxonomy that maps product categories to `treated`, `treatment_group`, and `policy_confidence`. Include beef/cattle, pork/pig, lamb/sheep/goat, poultry/other livestock, fish/seafood, and non-meat controls.

**Test Scenarios:**
- Happy path: beef and pork product labels map to treated core groups.
- Happy path: lamb/sheep/goat labels map to treated or sensitivity group, not untreated.
- Edge case: chicken/poultry maps to secondary/low-intensity livestock group.
- Edge case: fish/seafood maps to untreated control.
- Error path: unknown products map to explicit `unknown` rather than false controls.

**Verification:** Policy memo and taxonomy agree on treatment definitions and cite sources.

---

### U3: Grocery Price Data Downloader

**Files:** `src/data_sources/heissepreise.py`, `scripts/download_prices.py`, `tests/test_heissepreise_source.py`, `data/raw/.gitkeep`

**Purpose:** Download or scrape Danish supermarket price data from the named `Herover/heissepreise` ecosystem and cache raw snapshots.

**Dependencies:** U1.

**Technical Design:** Use structured endpoints or repository data formats where available. Store raw responses with timestamps and source metadata. Avoid brittle HTML scraping unless no structured endpoint exists.

**Test Scenarios:**
- Happy path: downloader stores a raw snapshot with source URL, retrieval time, and product records.
- Edge case: duplicate product records are retained or de-duplicated according to documented source keys.
- Error path: network/source failure returns a clear stage failure without corrupting existing cache.
- Integration: downloader can run in dry-run mode for CI without network.

**Verification:** Raw data cache contains inspectable product price records for Denmark.

---

### U4: Product Normalization And Commodity Classification

**Files:** `src/normalize_products.py`, `src/commodity_classifier.py`, `scripts/build_processed_panel.py`, `tests/test_commodity_classifier.py`

**Purpose:** Transform raw grocery records into standardized product and commodity records.

**Dependencies:** U2, U3.

**Technical Design:** Normalize dates, prices, units, store names, product names, package sizes, and categories. Use deterministic keyword/rule classification first, with documented overrides for ambiguous meat terms.

**Test Scenarios:**
- Happy path: common Danish labels for beef, pork, lamb, chicken, fish, and plant foods classify correctly.
- Edge case: mixed products such as ready meals, sausages, minced meat blends, and deli products get explicit mixed/ambiguous flags.
- Edge case: unit price and package price are both preserved where available.
- Error path: invalid prices or dates are excluded with row-level reason codes.

**Verification:** Processed product table includes store, date, price, normalized commodity, treatment group, and quality flags.

---

### U5: Balanced Panel Builder

**Files:** `src/panel_builder.py`, `scripts/build_balanced_panel.py`, `tests/test_panel_builder.py`, `data/processed/.gitkeep`

**Purpose:** Create balanced pre/post panels centered on the announcement date.

**Dependencies:** U4.

**Technical Design:** Select the largest symmetric window around 2024-06-24 with sufficient product coverage. Provide daily and weekly options if data supports both. Define product inclusion rules before estimation.

**Test Scenarios:**
- Happy path: panel has equal number of periods before and after event date.
- Edge case: products missing too many periods are excluded with documented reasons.
- Edge case: event date handling is consistent when aggregation is weekly.
- Error path: insufficient data coverage causes a clear failure and suggests shorter window or aggregation.

**Verification:** Model-ready panel reports row counts, period counts, treated/control counts, and balance diagnostics.

---

### U6: TWFE And Event-Study Estimation

**Files:** `src/estimators.py` or `scripts/estimate_twfe.R`, `scripts/run_estimations.py`, `tests/test_estimators.py`

**Purpose:** Estimate announcement effects and heterogeneity by meat type.

**Dependencies:** U5.

**Technical Design:** Estimate log-price outcomes with product/commodity fixed effects and time fixed effects. Include event-time interactions for treated units and subtype interactions for heterogeneity. Cluster standard errors at product or commodity level, with sensitivity to store-product clustering if feasible.

**Test Scenarios:**
- Happy path: overall TWFE model returns coefficient, standard error, confidence interval, p-value, sample size, fixed effects metadata, and cluster definition.
- Happy path: event-study model returns relative-time coefficients excluding a pre-event reference period.
- Happy path: heterogeneity models return separate estimates for beef, pork, lamb/sheep/goat, and poultry/other when present.
- Edge case: unsupported treatment groups with too few observations are dropped with warnings.
- Error path: model fails clearly when treatment or time variation is absent.

**Verification:** Estimation outputs are saved in machine-readable files for plots and tables.

---

### U7: Figures, Tables, And Diagnostics

**Files:** `src/output.py`, `scripts/make_outputs.py`, `outputs/figures/.gitkeep`, `outputs/tables/.gitkeep`, `tests/test_outputs.py`

**Purpose:** Produce event-study plots and LaTeX ATE tables.

**Dependencies:** U6.

**Technical Design:** Generate one overall event-study plot, subtype event-study plots, a main ATE LaTeX table, and diagnostics for pre-trends/sample composition. Table notes should include fixed effects, clustered standard errors, event date, outcome definition, sample window, and treatment definitions.

**Test Scenarios:**
- Happy path: output stage writes expected figure and `.tex` table files.
- Happy path: LaTeX table includes coefficient labels, standard errors, N, fixed effects, clustering, and notes.
- Edge case: missing subtype estimates do not break all outputs.
- Error path: malformed estimation output produces a clear validation error.

**Verification:** Outputs render/read without manual edits.

---

### U8: Master Pipeline Runner

**Files:** `main.py`, `scripts/run_all.py`, `tests/test_pipeline_smoke.py`

**Purpose:** Run all steps from one file as requested.

**Dependencies:** U1-U7.

**Technical Design:** Expose stages such as `download`, `process`, `panel`, `estimate`, `outputs`, and `all`. Include config for event date, window length, aggregation frequency, and dry-run/test fixture mode.

**Test Scenarios:**
- Happy path: fixture-mode `all` run creates processed panel, model output, figure, and table.
- Edge case: rerunning pipeline does not duplicate outputs or corrupt cache.
- Error path: missing raw data in offline mode produces clear next action.
- Integration: stage-specific run can resume from existing earlier artifacts.

**Verification:** A single command can regenerate all non-network outputs from cached data.

---

### U9: README, Data Dictionary, And Reproducibility Notes

**Files:** `README.md`, `docs/policy/policy_summary.md`, `docs/data_dictionary.md`, `docs/methodology.md`

**Purpose:** Document policy, data, methods, execution, outputs, and limitations.

**Dependencies:** U1-U8.

**Technical Design:** README should be reader-first: research question, policy summary, data source, treatment coding, identification strategy, run instructions, output paths, and caveats.

**Test Scenarios:**
- Happy path: README commands match available runner stages.
- Happy path: data dictionary covers every processed panel column.
- Edge case: limitations explicitly distinguish announcement effects from statutory tax effects.
- Integration: docs link to generated outputs and policy memo.

**Verification:** New reader can understand and run the project without asking for hidden context.

---

### U10: Commit And Push

**Files:** repository root

**Purpose:** Publish completed implementation to `dgonzalezgonzalez/danish-meat-tax.git`.

**Dependencies:** U1-U9.

**Technical Design:** If local workspace is not a Git repo, initialize or clone the public repo into the workspace, set remote, verify branch, then commit and push. Preserve generated large-data exclusions.

**Test Scenarios:**
- Integration: `git status` shows intended tracked files only before commit.
- Error path: unauthenticated push or missing remote is reported with exact remediation.

**Verification:** GitHub remote contains committed pipeline and docs.

---

## System-Wide Impact

- **Interaction graph:** `main.py` orchestrates download, processing, panel building, estimation, and output stages. Each stage should accept explicit input/output paths for reproducibility.
- **Error propagation:** Stage failures should stop downstream execution and preserve existing artifacts unless the user explicitly overwrites.
- **State lifecycle risks:** Raw data cache and generated outputs should be treated separately from committed source files.
- **API surface parity:** CLI runner, scripts, and README instructions must expose the same stages and config names.
- **Integration coverage:** Fixture-based pipeline smoke tests are required because networked data downloads may not run in CI.
- **Unchanged invariants:** The project should not require committing large raw scrape files or credentials.

---

## Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| Heissepreise/Dagligepriser data do not cover enough symmetric periods around 2024-06-24 | Medium | High | Detect maximum balanced window; add weekly aggregation; document if announcement study is underpowered. |
| Product taxonomy misclassifies mixed meat products | High | Medium | Use explicit ambiguous/mixed flags and sensitivity excluding ambiguous products. |
| Lamb/sheep/goat data are sparse | Medium | Medium | Include group if support exists; otherwise report as pooled other livestock or documented sparse category. |
| Poultry policy status is ambiguous for retail treatment | Medium | Medium | Separate poultry as secondary/sensitivity group, not main control. |
| Announcement effect may reflect broader food inflation shocks | Medium | High | Use time fixed effects, controls, pre-trend diagnostics, placebo groups, and robustness windows. |
| Data source terms or availability limit scraping | Medium | High | Prefer public structured data endpoints; cache metadata; document source and access date. |
| Empty local repo blocks commit/push | High | Medium | Bootstrap Git remote before implementation and verify branch/authentication. |

---

## Documentation / Operational Notes

- `docs/policy/policy_summary.md` should include a short timeline: 2024-06-24 Green Tripartite announcement, later political agreement milestones, expected implementation schedule, tax-rate structure, and livestock scope.
- README should state that estimates are announcement effects on observed supermarket prices, not realized effects of a tax already collected.
- README should identify the event date and any robustness event dates in absolute dates.
- Generated tables should include notes describing treatment groups and balanced-window construction.
- Large raw data should remain untracked unless explicitly approved.

---

## Sources & References

- BBC News, "Denmark to charge farmers carbon tax on livestock", https://www.bbc.com/news/articles/c20nq8qgep3o
- Danish Government announcement, "Regeringen og parterne i grøn trepart indgår historisk aftale om et grønt Danmark", https://regeringen.dk/aktuelt/nyheder/2024/regeringen-og-parterne-i-groen-trepart-indgaar-historisk-aftale-om-et-groent-danmark/
- Danish Green Tripartite agreement PDF, https://regeringen.dk/media/ng3b13va/aftale-om-et-groent-danmark.pdf
- Danish Ministry of Taxation / Expert Group material, "Green Tax Reform final report", https://skm.dk/media/tngh1b4r/green-tax-reform-final-report.pdf
- Herover/heissepreise, https://github.com/Herover/heissepreise
- Daglige Priser data site, https://dagligepriser.dk/
