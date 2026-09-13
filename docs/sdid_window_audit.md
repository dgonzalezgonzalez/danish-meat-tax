# Appendix SDiD window comparison

## Design and decision rule

This diagnostic tests whether additional history improves the appendix SDiD comparisons. It does not overwrite publication estimates. The candidate pre-treatment lengths, chosen before inspecting results, are 24, 36, and 54 months, against the published 15 months. They start in July 2022, July 2021, and January 2020; all end in June 2024. The post-treatment period remains July 2024–September 2025.

The five outcomes are national CPI (51 commodity series), country HICP (27 countries), bovine slaughter weight and heads (27 countries each), and extra-EU imports (383 importer–partner pairs, including 17 Danish pairs). All retain their published donor membership. The scripts assert complete histories rather than silently dropping units. Slaughter remains in raw log levels: this isolates the window change from the seasonal adjustment in the existing Table B2 long-pre specifications. The latter are a separate joint sensitivity to support and transformation and remain unchanged.

The comparison metric is the root mean squared treated-minus-synthetic gap after removing its mean **over the same April 2023–June 2024 evaluation months**. Centering permits the additive level difference allowed by SDiD. The CSV also reports centered RMSE over each full training period, but those values cover different observations and do not determine the decision. These are in-sample diagnostics, not validation on held-out months or proof of a better causal counterfactual.

Replacement requires an improvement in every outcome. ATT signs, p-values, and standard errors do not determine that decision. The diagnostic exports point estimates and fitted paths using `vce(noinference)`. No longer window passes the fit criterion, so the publication estimates and their existing 200-replication inference are retained. The diagnostic does not support a claim of improved precision. The short-window point estimates are rerun as an internal replication check.

## Results

Centered pre-treatment RMSE over the common April 2023–June 2024 months:

| Outcome | 15 pre-months | 24 pre-months | 36 pre-months | 54 pre-months |
|---|---:|---:|---:|---:|
| National CPI | 0.0054 | 0.0099 | 0.0118 | 0.0111 |
| Country HICP | 0.0100 | 0.0102 | 0.0096 | 0.0097 |
| Slaughter weight | 0.0562 | 0.0598 | 0.0622 | 0.0630 |
| Slaughter heads | 0.0562 | 0.0609 | 0.0633 | 0.0640 |
| Extra-EU imports | 0.0650 | 0.0801 | 0.0861 | 0.0963 |

Only HICP improves, slightly, with 36 or 54 pre-months. All other outcomes fit worse under every extension, so none meets the all-outcome replacement rule. The published specifications are retained. [Maximum-history previews](sdid_max_history.md) subsequently requested for B1, B3 and B4 also have worse common-period fit than their published counterparts.

## Sources and reproduction

The additional Eurostat HICP snapshot is `data/raw/eurostat_beef_hicp_2020m01_2025m09.json`, retrieved 11 September 2026 at 14:16:22 UTC. The source update remains 6 February 2026, 23:00 +0100. It uses the same frozen historical release, product, unit, and frequency as the publication query, with `sinceTimePeriod=2020-01`. The exact URL, checksum, and byte count are stored separately under `window_audit_files` in `data/reference/replication_input_manifest.json`. Existing publication input records are unchanged. All overlapping source cells and flags match the original HICP snapshot exactly.

PRIS01, slaughter, and Commission trade histories already exist in the cached research inputs. Trade preprocessing accepts an optional `WindowStart`; its default publication output is unchanged. Although the extended source contains more trading pairs, Stata restricts the audit to the original 383 pairs. All overlapping trade cells, including zero observations and source-row counts, match the publication panel.

From the project root, after normal publication preprocessing:

```powershell
$env:PYTHONPATH = 'src'
python scripts/prepare_sdid_window_inputs.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_beef_trade_pair_panel.ps1 -WindowStart 2020-01-01 -OutputPath data/processed/sdid_window_trade.csv
python scripts/verify_inputs.py --include-window-audit
```

Then in Stata:

```stata
do scripts/stata/master.do audit
```

This runs the publication master followed by the isolated window diagnostic and its verification. To repeat only the diagnostic after publication outputs exist, run `prepare_sdid_window_cpi.do`, `sdid_window_audit.do`, and `verify_sdid_revision.do` in that order, under `scripts/stata/`. All analytical computation is in Stata; Python downloads/reshapes HICP, and PowerShell reshapes trade records.

Outputs under `outputs/models/stata/` are `sdid_window_audit.csv` (20 point estimates and both fit measures), `sdid_window_decision.csv` (whether each longer window improves all outcomes), and `sdid_window_<exercise>_<pre_months>_series.csv` (raw treated and synthetic paths). Diagnostics are supplementary replication outputs, not additional paper figures. Price inputs preserve double precision; trade joins explicitly retain UTF-8 names and convert keys to fixed-width strings only after checking that no name will be truncated.

## Figure presentation

Every appendix SDiD figure shifts the weighted donor log series by its unweighted mean pre-treatment treated–donor gap. Only the displayed intercept changes; monthly changes, estimation inputs, weights, ATT and inference are unaffected. Each caption states the adjustment, and the original `synthetic` path remains beside `synthetic_aligned` in the CSV. SDiD's time weighting means the post-treatment plotted gap alone is not the ATT.

Figures B2 and B3 both use the axis title “Log consumer price index.” B2 is Statistics Denmark's national CPI; B3 is Eurostat HICP, whose Danish series is compiled by Statistics Denmark. Their common provider does not make their definitions identical; captions retain the CPI/HICP distinction.
