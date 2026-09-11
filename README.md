# Data and Code for: Before the Levy: Environmental Policy Announcements and Denmark's Beef Market

**Author:** Diego González-González. The manuscript gives no affiliation; this README follows its author line. **Revision:** 9 September 2026. **Contact:** the author through the [project repository](https://github.com/dgonzalezgonzalez/danish-meat-tax).

## Overview

This package studies market adjustment following Denmark's June 2024 announcement of a future livestock-emissions tax. It prepares grocery and official price panels, estimates difference-in-differences and synthetic difference-in-differences models, examines cattle slaughter and extra-EU imports, and constructs conditional carbon-damage calibrations. Estimation, analytical descriptive statistics, simulations, and calibration grids are produced in Stata. Python renders the four-panel calibration surface figure from Stata outputs; the remaining figures are produced in Stata. Python and PowerShell also handle acquisition, classification, normalization, reshaping, and orchestration.

The revision excludes poultry and eggs as well as other livestock-exposed products from beef controls. Grocery DiD is 0.0278 (SE 0.0144); official CPI DiD is 0.0644 (SE 0.0305). Main slaughter-weight SDiD is -0.0661 (SE 0.0811), with estimates close to zero under longer pre-treatment support. The concurrent end of the cattle nitrate derogation prevents isolating the tax announcement from all other cattle regulation.

## Data availability and provenance

All inputs were obtained from public websites or published research. No confidential individual or administrative records are required. Raw and large processed datasets are excluded from Git; selected results and figures are included. **Public access does not establish permission to redistribute data.** This repository does not claim ownership of third-party data or grant a new license over them.

[replication_input_manifest.json](data/reference/replication_input_manifest.json) identifies the exact research inputs by byte counts and SHA-256 hashes. Its audit date is not an original retrieval timestamp. These sources are revision-prone. An immutable public deposit of the complete input snapshot has not yet been established. A fresh clone with current downloads provides a reproducible workflow but is not guaranteed to reproduce the paper's numbers exactly; exact replication requires the matching snapshots.

| Dataset and provider | Required file(s) under `data/raw/` | Access and provenance | Role |
|---|---|---|---|
| dagligepriser.dk grocery histories | `heissepreise_20260609T092146Z.json` | [Canonical JSON](https://dagligepriser.dk/data/latest-canonical.json); retrieved 9 June 2026, 09:22:01 UTC. Public, without credentials. The historical snapshot is not promised at this changing URL; redistribution terms remain to be confirmed. | Product descriptions, stores, packages, and dated prices; October 2023–September 2025, excluding June 2024. |
| Statistics Denmark PRIS01 | `statbank_pris01.csv`, `statbank_pris01_metadata.json` | [Data](https://api.statbank.dk/v1/data/PRIS01/CSV?VAREGR=*&ENHED=100&Tid=*), [metadata](https://api.statbank.dk/v1/tableinfo/PRIS01?lang=en). Existing snapshot audited 9 September 2026; original retrieval timestamp not recorded. | Monthly CPI; beef plus 50 donors. |
| European Commission beef-carcass prices | `eu_beef_carcass_prices_2023m04_2025m09.json` | [API documentation](https://agridata.ec.europa.eu/extensions/API_Documentation/Beef.html), endpoint `api/beef/prices`, window 3 April 2023–28 September 2025. Existing snapshot audited; original retrieval timestamp not recorded. [Instructions](docs/country_sdid.md). | AO2 young-bull prices, EUR/100 kg, 23 countries. |
| Commission Beef Trade Data Explorer / Eurostat COMEXT | `eu_beef_trade_data_en.csv` | [Dashboard](https://agridata.ec.europa.eu/extensions/DashboardBeef/BeefTrade.html): download the English Data Explorer bulk CSV. Existing snapshot audited; original retrieval timestamp not recorded. [Instructions](docs/beef_trade_pair_sdid.md). | Extra-EU imports in carcass-weight tonnes, 383 importer–partner pairs. |
| Eurostat `apro_mt_pwgtm` | `eurostat_bovine_slaughter_2020_2025.json` | [Exact query](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apro_mt_pwgtm?lang=EN&meat=B1000&sinceTimePeriod=2020-01&untilTimePeriod=2025-09), downloaded 9 September 2026. | EU27 bovine slaughter, thousand tonnes and heads. |
| Statistics Denmark ANI41 | `statbank_ani41.csv`, `statbank_ani41_metadata.json` | [Data](https://api.statbank.dk/v1/data/ANI41/CSV?DYRKAT=*&ENHED=PROD,SLAGEKS&Tid=*&lang=en), [metadata](https://api.statbank.dk/v1/tableinfo/ANI41?lang=en), downloaded 9 September 2026. | National cattle production cross-check. |
| Statistics Denmark PRIS04 | `statbank_pris04_total.csv` | [Total net-price index](https://api.statbank.dk/v1/data/PRIS04/CSV?VAREGR=000005&ENHED=100&Tid=*&lang=en), downloaded 9 September 2026. | Converts 2022-DKK statutory rates to 2024 DKK. |
| SCC studies and conversion constants | Included inventory under `data/reference/` | [Inventory](data/reference/scc_literature_estimates.csv) gives individual citations, URLs, source locators, units, price bases, scenarios, ranges, and selection decisions. US CPI-U constants are transcribed in `scc_meta_analysis.do`; [BLS annual CPI](https://www.bls.gov/cpi/tables/supplemental-files/home.htm). | Ten-study sensitivity benchmark, not an exhaustive systematic review. |

Source metadata and [data_dictionary.md](docs/data_dictionary.md) define variables and units. Consult providers' current reuse conditions before redistribution. No paid access, application, or data-use agreement was required for these public downloads. Commission data acquisition includes manual steps; subsequent transformations are scripted. Official statistics do not require the author's logged-in browser session.

## Software and computational requirements

Validated environment: Windows x64; Python **3.12.14**, NumPy **2.3.5**, pandas **3.0.1**; Matplotlib **3.10.8**; PowerShell; **Stata/MP 19.5** with **sdid 2.0.2**. Stata is commercial software. `estout` is also installed by the dependency script. The paper compiles with **MiKTeX 25.12**, pdfTeX 1.40.28, and BibTeX 0.99e; standard Computer Modern fonts and packages appear in the TeX preamble. No R, MATLAB, or Python econometric library is required.

The tested host has an Intel Core i7-1165G7 at 2.80 GHz, eight logical processors, and about 16 GB physical RAM. Peak memory was not measured. Budget at least 5 GB free disk: required raw snapshots occupy roughly 0.44 GB and processed working files roughly 1.44 GB, plus temporary files. The final complete Stata master, including calibration, took 729 seconds (12.2 minutes); grocery preprocessing adds several minutes. Allow 30 minutes for a local rerun as a planning estimate, excluding variable download time. See [validation.md](docs/validation.md) for the final validation record.

Install Python dependencies with `python -m pip install -r requirements.txt`. For tested versions, use `requirements-replication.txt`. In Stata, run `do scripts/install_stata_dependencies.do` once. This installs missing `sdid` and `estout` from SSC without pinning future SSC versions; record `which sdid` and `which esttab`. A licensed Stata installation must exist. Set `STATA_EXE` when outside conventional installation locations. Python 3.10+ is the intended minimum; only the environment above was tested in this revision.

## Replication instructions

Run from the repository root. Keep fixture outputs in a separate directory.

1. Install software. Acquire the two Commission inputs using the linked instructions. Obtain the named grocery snapshot for exact replication.
2. With `PYTHONPATH=src`, run `python main.py download`. This downloads or reuses grocery data, PRIS01, production, and PRIS04. Avoid `--refresh` for an existing snapshot.
3. Run `python scripts/verify_inputs.py`. Investigate mismatches; do not silently relabel new downloads as the research snapshot.
4. Run the wrapper below to verify inputs, rebuild panels, run every Stata analysis, and optionally compile the paper.

```powershell
$env:PYTHONPATH = 'src'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/replicate.ps1 -Python python -CompilePaper
```

The wrapper uses the June 2026 grocery snapshot and does not modify raw inputs. To deliberately analyze another snapshot, supply `-RawPath` and `-AllowUpdatedInputs`; published numbers may change. Acquisition is the separate `download` stage. The underlying sequence is:

```powershell
$env:PYTHONPATH = 'src'
python main.py process --raw-path data/raw/heissepreise_20260609T092146Z.json
python main.py panel --frequency monthly
python main.py estimate
python main.py outputs
```

`estimate` prepares the grocery Stata file, EU panels, and Eurostat cells before all econometric do-files. `outputs` runs SCC harmonization, simulations, and calibration. After preprocessing, `do scripts/stata/master.do` runs the complete Stata sequence, including production, SCC, and calibration grids. To render the Python surface figure after a direct Stata master run, execute `python scripts/render_calibration.py`. The pipeline `outputs` stage calls this renderer automatically. Optional compilation calls pdfLaTeX, BibTeX, then pdfLaTeX twice. Paper tables contain formatted transcriptions from CSVs: reconcile them using the output map whenever inputs change before interpreting a newly compiled paper as updated results.

### Randomness and diagnostics

Micro/aggregate/country and SCC use seed 20260827; trade uses 20260828; production uses 20260909. SDiD inference uses 200 replications; SCC uses 10,000. Combined calibration uncertainty pairs these SCC draws with independent coefficient draws using seed 20260910. Each analytical do-file clears Stata state and records a log under `outputs/diagnostics/stata/`. Root Windows batch logs are also checked for Stata `r(...)` failures even when the process returns zero. Changes to software, sorting, or inputs can affect simulated results.

The deterministic fixture stops at the Stata input contract and does not fabricate publication estimates:

```powershell
$env:PYTHONPATH = 'src'
python main.py all --fixture --root tmp_tests/offline --frequency monthly
python -m unittest discover -s tests
```

## Programs and outputs

| Location | Contents |
|---|---|
| `main.py`, `src/danish_meat_tax/pipeline.py` | Acquisition, preprocessing, and orchestration. |
| `src/danish_meat_tax/data_sources/` | Grocery, StatBank, and Eurostat readers. |
| `normalize_products.py`, `policy_taxonomy.py`, `panel_builder.py` | Conversion, classification, period aggregation; no estimation. |
| `scripts/prepare_country_beef_panel.ps1`, `scripts/prepare_beef_trade_pair_panel.ps1` | Commission source reshaping, called by `estimate`. |
| `scripts/stata/master.do` | Complete publication analysis in dependency order. |
| `scripts/stata/production_analysis.do` | Six EU27 slaughter specifications and ANI41 descriptive series. |
| `scripts/stata/scc_meta_analysis.do` | Harmonization, bootstrap, leave-one-out checks, figures; calls persistence analysis. |
| `scripts/stata/price_benchmark_analysis.do` | Crossed product–store and circular-month-block resampling of the grocery price benchmark; called by the SCC script. |
| `scripts/stata/persistence_analysis.do` | Preferred CPI DiD calibration; 27 scenarios and four 51-by-51 grids with combined SCC, coefficient, and grocery-price sensitivity bounds. |
| `scripts/stata/production_descriptives.do` | Table 1, Panel C, from the exact main slaughter samples; called by production analysis. |
| `scripts/render_calibration.py`, `src/danish_meat_tax/calibration_figures.py` | Python rendering of the Stata calibration grids; four panels at taxable shares 0.25, 0.50, 0.75, and 1. |
| `outputs/models/stata/`, `outputs/figures/stata/` | Machine-readable results and publication PNGs. |
| `paper/main.tex`, `paper/references.bib`, `paper/main.pdf` | Manuscript, bibliography, compiled paper. |

[output_map.md](docs/output_map.md) maps every paper table and figure and otherwise unmapped in-text numbers to inputs and scripts. [production_analysis.md](docs/production_analysis.md), [methodology.md](docs/methodology.md), and [beef_carbon_price_calibration.md](docs/beef_carbon_price_calibration.md) explain design and interpretation. Historical `docs/plans/` notes are not the current replication specification. Unintegrated world-price experiments are outside the publication master.


The calibration intervals in Figures 2–4 include resampling of the grocery pre-announcement mean (seed 20260911, with one-, two-, and four-month block checks); study-level mapped intervals use seed 20260912. Figure 4 additionally uses the preferred CPI coefficient's uncertainty. These are conditional sensitivity intervals, with independent simulation draws across uncertainty sources. The 59.6 lifecycle benchmark remains fixed because the inspected sources do not supply a compatible sampling interval; [the emissions source audit](docs/emissions_intensity_audit.md) distinguishes producer heterogeneity from uncertainty in this benchmark. Full methods and numerical checks are in [the calibration note](docs/beef_carbon_price_calibration.md).
