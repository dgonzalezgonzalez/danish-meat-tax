# Cattle slaughter and production extension

The primary source is Eurostat `apro_mt_pwgtm`, meat B1000, frequency M, slaughter activity SLAUGHT. Thousand tonnes (`THS_T`) measure carcass weight; thousand heads (`THS_HD`) count slaughtered animals. Denmark is treated; the other 26 EU27 countries are donors. Other Danish livestock categories are exposed to the policy and cannot serve as untreated production controls.

`data_sources/production.py` downloads the original JSON-stat payload and writes cells, missing values, and source flags without estimation. `scripts/stata/production_analysis.do`, called by both the Python estimate stage and Stata master, selects countries, constructs log outcomes and balanced windows, estimates SDiD, computes inference and diagnostics, and draws the graph.

The main window is April 2023–September 2025, with July 2024 treatment (15 pre/15 post). All 27 countries are positive and complete. The longer specification starts January 2020 (54/15) and subtracts each country's pre-treatment calendar-month mean log output, adding back its overall pre-treatment mean. This changes both support and seasonal adjustment, so it is a joint sensitivity check. The third drops June 2024 from the main window (14/15) and uses a contiguous period index. No missing slaughter is recoded as zero. Placebo inference uses 200 replications and seed 20260909.

Main weight ATT is -0.0661 (SE 0.0811; interval -0.225 to 0.093); the longer adjusted estimate is -0.0055. Main heads ATT is -0.0350 (SE 0.0814); all six intervals include zero. The evidence cannot establish contraction, and the change across temporal windows qualifies the model's interpretation. The April-announced, July-effective end of Denmark's cattle nitrate derogation is an unresolved cattle-specific confound.

Slaughterhouse output is not identical to domestic cattle production. Live-animal trade and slaughter coverage matter. Statistics Denmark ANI41 contains separate production and slaughter/export concepts; the script exports the cattle-total production series and year-on-year growth as a national cross-check. It does not merge that concept into the Eurostat panel.

Exact outputs are mapped in `output_map.md`; hashes and access instructions appear in the root README. Source flags are retained in each exported estimation sample. The graph's donor series uses unit weights and retains a pre-treatment level gap; the ATT additionally uses time weighting.
