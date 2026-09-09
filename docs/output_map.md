# Paper output and numerical-claim map

Table and figure numbers refer to the 9 September 2026 revision. Paths below are relative to the project root. All numerical results are calculated in Stata; TeX applies presentation rounding. The Stata master runs every producing do-file listed here.

| Paper output | Producing file under `scripts/stata/` | Result under `outputs/models/stata/` or `outputs/figures/stata/` | Inputs |
|---|---|---|---|
| Table 1: descriptive statistics | `microdata_analysis.do`, `aggregate_analysis.do`, `production_descriptives.do` | `descriptive_statistics.csv`, `aggregate_descriptive_statistics.csv`, `production_descriptive_statistics.csv` | Grocery panel; PRIS01; main Eurostat slaughter samples |
| Table 2: main ATT estimates | Same | `micro_estimates.csv`, `aggregate_estimates.csv` | Same |
| Figure 1 A/B: event studies | Same | `micro_event_study.png`, `aggregate_event_study.png`; corresponding coefficient CSVs | Same |
| Figure 2: SCC forest | `scc_meta_analysis.do` | `scc_meta_forest.png`, `scc_literature_calibration.csv` | SCC inventory, PRIS04, micro pre-price |
| Figure 3: price calibration | `scc_meta_analysis.do` | `beef_policy_calibration.png`, `beef_policy_calibration.csv`, `scc_meta_summary.csv` | Main estimates and SCC inputs |
| Table B1: preferred SCC values | `scc_meta_analysis.do` | `scc_literature_calibration.csv`; descriptive source columns from inventory | SCC inventory |
| Table B2: production specifications | `production_analysis.do` | `production_estimates.csv` | Eurostat B1000 source cells |
| Figure B1: production | `production_analysis.do` | `production_sdid.png`, `production_THS_T_main_series.csv` | Same |
| Figure B2: official SDiD comparison | `aggregate_analysis.do` | `aggregate_sdid.png`, `aggregate_sdid_series.csv` | PRIS01 |
| Figure B3: country beef prices | `country_sdid.do` | `country_sdid.png`, `country_sdid_estimate.csv`, `country_sdid_series.csv` | Commission AO2 country panel |
| Figure B4: beef imports | `beef_trade_pair_sdid.do`, `beef_trade_pair_sdid_bootstrap.do` | `beef_trade_pair_sdid.png`, `beef_trade_pair_sdid_bootstrap_estimate.csv`, `beef_trade_pair_sdid_series.csv` | Commission extra-EU importer–partner panel |

## Numerical claims outside the tables

- Grocery pretrend p=0.317: `micro_estimates.csv`, `pretrend_p_value`; `microdata_analysis.do` joint pre-coefficient test. Event dates, support counts, and 15/15 windows are defined in the corresponding do-files; the two EU reshaping scripts record panel dimensions in their console output.
- Production -6.4% interpretation: `100*(exp(att)-1)` for the main weight coefficient. Pre-treatment centered gap RMSE 0.056/0.031 and sample dimensions appear in `production_estimates.csv`; each `_sample.csv` retains exact source observations and flags. All inference fields are in that same output.
- SCC mean 160.39, sensitivity endpoints 79.50/366.63, two directly dated 2030 observations and their mean 93.36, tax-price factor 1.04938, and 2024-DKK rates 125.93/314.81: `scc_meta_summary.csv`, produced by `scc_meta_analysis.do`.
- Leave-one-out range 111.56–172.36 and exclusion of Pindyck giving 166.32: `scc_leave_one_out.csv`, same do-file.
- Persistence scenarios: `calibration_scenarios.csv`, `persistence_analysis.do` called by SCC analysis. Full persistence gives an announcement increment 10.80 DKK/kg, central damage 65.91 DKK/kg, remaining gap 47.61 with full additional implementation pass-through and full lifecycle taxable share, and 55.11 with zero additional pass-through. There are 27 scenario rows, with parameters explicitly stored.
- Statutory tax rates, deduction, announcement date, nitrate limits and dates, and BVD chronology are institutional facts cited in `paper/references.bib` and `docs/policy/policy_summary.md`, not empirical estimates. Lifecycle intensity 59.6 and FX 6.8953 are fixed calibration assumptions documented in the calibration note.
- Appendix A equations and signs are analytical derivations, not simulation outputs. Their assumptions and finite-horizon restrictions appear in the proofs.

## Supplementary machine-readable results

`denmark_cattle_production.csv` provides the ANI41 national-production series and Stata year-on-year growth; it is a descriptive cross-check and does not enter the SDiD table. All six production series/sample exports and trade placebo estimates remain available even where the paper displays only the main figure or bootstrap inference.

The SDiD graphs show treated and unit-weighted donor levels. They retain pre-treatment level gaps; SDiD also uses time weighting when calculating ATT. A vertical level gap in these graphs is not itself the treatment effect.

## Production descriptives and preferred-estimate surfaces

- Table 1 Panel C: `production_descriptive_statistics.csv`, from `production_descriptives.do`, using the exact main weight and head-count sample exports. All/Denmark/donor rows contain 810/30/780 country-months per outcome.
- Table B2 (production): columns 1–3 weight, 4–6 counts; main/long-pre/June-omitted. ATT and SE from `production_estimates.csv`; the former horizontal results layout is replaced by specification columns.
- Figure 4 (`fig:surfaces`): `outputs/figures/python/calibration_surfaces.png`, rendered by `scripts/render_calibration.py` from `calibration_surfaces.csv`. `persistence_analysis.do` calculates the four grids, holds f at .25/.50/.75/1, and propagates column 2's HAC coefficient endpoints conditional on other calibration inputs.
- Updated remaining-gap prose: `calibration_scenarios.csv`. Preferred CPI DiD applied to the grocery price anchor; increment 10.80, damages 65.91, full-persistence/no-additional-response gap 55.11, full-response gap 47.61 [36.44,58.10] DKK/kg.
