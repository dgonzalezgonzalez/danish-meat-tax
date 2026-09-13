# Longest-history SDiD figure previews

The author requested visual previews of Figures B1, B3 and B4 using earlier histories than the 54-month diagnostic. These previews retain each published donor group, outcome definition and July 2024 treatment date. They do not replace the manuscript figures or estimates.

## Coverage and results

The longest eligible history is the continuous window ending September 2025 in which every original unit has an observed outcome. Production and HICP must be strictly positive before taking logs. There is no interpolation, and missing slaughter is not zero. The post-period remains 15 months.

| Preview | Earliest eligible month | Pre-months | Units | ATT | Recent pre-fit RMSE, published | Recent pre-fit RMSE, extended |
|---|---|---:|---:|---:|---:|---:|
| B1: slaughter weight | June 2014 | 121 | 27 | -0.0331 | 0.0562 | 0.0641 |
| B3: beef-and-veal HICP | December 2016 | 91 | 27 | 0.0083 | 0.0100 | 0.0123 |
| B4: extra-EU imports | January 2010 | 174 | 383 | -0.0944 | 0.0650 | 0.1055 |

The common fit period is April 2023–June 2024, with the treated-minus-synthetic gap centered within those months. All three maximum-history fits are worse on that metric. This fails the author's criterion for replacing the published windows. Full-history RMSE is also exported, but it covers different months and does not determine replacement. The previews show point estimates and fitted paths using `vce(noinference)`; confidence intervals from the shorter publication windows must not be attached to these estimates.

For slaughter, Estonia's May 2014 weight observation is missing, with source flag `|C`; the continuous balanced panel therefore starts in June. For HICP, Finland, Ireland and Romania first report this historical beef-and-veal series in December 2016. Extending earlier would require changing donor membership or imputing data. The cached Commission trade file starts in January 2010. Its larger historical pair universe is restricted to the original 383 pairs (17 Danish); unreported cells are treated using the existing sparse-trade-panel zero convention.

Production uses raw log weight throughout. It does not apply the country-season adjustment used in Table B2's separate long-pre sensitivity. The longest-history exercise therefore isolates support from that transformation choice.

## Sources and reproduction

`scripts/prepare_sdid_max_history.py` queries the full historical Eurostat releases through September 2025, with no lower date bound. HICP retains `prc_hicp_midx`, `CP01121`, `I15`, monthly; slaughter retains `apro_mt_pwgtm`, bovine `B1000`. It preserves source values and flags. The HICP payload was retrieved 11 September 2026 at 14:30:32 UTC and the slaughter payload at 14:30:34 UTC. All overlapping source cells and flags exactly match the publication snapshots. The original inputs are not refreshed.

Separate `max_history_files` records in `data/reference/replication_input_manifest.json` contain the exact URLs, retrieval times, byte counts and SHA-256 checksums. Preprocessing and reproduction, from the project root after normal publication preprocessing:

```powershell
$env:PYTHONPATH = 'src'
python scripts/prepare_sdid_max_history.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_beef_trade_pair_panel.ps1 -WindowStart 2010-01-01 -OutputPath data/processed/sdid_max_trade.csv
python scripts/verify_inputs.py --include-max-history
```

In Stata, run `do scripts/stata/sdid_max_history_figures.do`. Alternatively, `do scripts/stata/master.do maxhistory` rebuilds the publication and then these previews. Analytical selection, SDiD, fit calculations and plotting are all in Stata. Trade joins explicitly use UTF-8 and fixed-width string keys without truncation; the scripts assert key length before conversion and require every publication pair to match.

## Outputs and interpretation

- `outputs/figures/stata/sdid_max_B1.png`, `sdid_max_B3.png`, `sdid_max_B4.png`: each contains the full history and a recent-period zoom using identical estimated weights and the same vertical scale.
- `outputs/models/stata/sdid_max_history_summary.csv`: start dates, pre-month counts, units, ATT, full and common-period centered RMSE, baseline RMSE and its ratio.
- `sdid_max_<exercise>_coverage.csv`: unit identifiers, first valid month and last missing/nonpositive month.
- `sdid_max_<exercise>_sample.csv`: selected unit-month log outcomes and source flags, with unit identifiers. These larger intermediate samples remain local and are regenerated from the cached inputs.
- `sdid_max_<exercise>_series.csv`: treated and raw donor paths, the aligned donor path, gaps, and squared deviations used for the diagnostics.

All donor paths are shifted by the mean gap over their **entire** pre-treatment history. A recent zoom can consequently show a nonzero pre-treatment gap: it is the same fitted path, not a second alignment on the recent months. This is a display adjustment. SDiD additionally uses estimated time weights, so the raw post-treatment vertical gap is not the ATT. The intercept treatment follows the [SDiD framework](https://www.aeaweb.org/articles?id=10.1257/aer.20190159). A visually closer path alone does not establish a more credible causal design.
