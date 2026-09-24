# Appendix SDiD window comparison

## Design and interpretation

This diagnostic tests whether additional history improves the appendix SDiD comparisons. It does not overwrite publication estimates. The candidate pre-treatment lengths, chosen before inspecting results, are 24, 36, and 54 months, against the published 15 months. They start in July 2022, July 2021, and January 2020; all end in June 2024. The post-treatment period remains July 2024–September 2025.

The five outcomes are national CPI (51 commodity series), country HICP (27 countries), bovine slaughter weight and heads (27 countries each), and extra-EU imports (383 importer–partner pairs, including 17 Danish pairs). All retain their published donor membership. The scripts assert complete histories rather than silently dropping units. Slaughter remains in raw log levels: this isolates the window change from the seasonal adjustment in the existing Table B2 long-pre specifications. The latter are a separate joint sensitivity to support and transformation and remain unchanged.

The comparison metric is the root mean squared treated-minus-synthetic gap after removing its mean **over the same April 2023–June 2024 evaluation months**. Centering permits the additive level difference allowed by SDiD. The CSV also reports centered RMSE over each full training period, but those values cover different observations and do not determine the decision. These are in-sample diagnostics, not validation on held-out months or proof of a better causal counterfactual.

Window assessment is outcome-specific. A price or slaughter specification does not depend on the fit of the trade panel, and there is no joint all-outcome veto. The diagnostic exports point estimates and fitted paths using `vce(noinference)`; its ATT values have no new uncertainty estimates. The 15-month window remains the published common-support reference, while all longer-window ATT values and fit measures are reported as sensitivity checks. Their in-sample fit does not justify selecting a new primary window. A useful next design would reserve a prespecified pre-treatment block for holdout prediction and inspect donor weights and placebo fit separately for each outcome.

## Results

Centered pre-treatment RMSE over the common April 2023–June 2024 months:

| Outcome | 15 pre-months | 24 pre-months | 36 pre-months | 54 pre-months |
|---|---:|---:|---:|---:|
| National CPI | 0.0054 | 0.0099 | 0.0118 | 0.0111 |
| Country HICP | 0.0100 | 0.0102 | 0.0096 | 0.0097 |
| Slaughter weight | 0.0562 | 0.0598 | 0.0622 | 0.0630 |
| Slaughter heads | 0.0562 | 0.0609 | 0.0633 | 0.0640 |
| Extra-EU imports | 0.0650 | 0.0801 | 0.0861 | 0.0963 |

Only HICP improves, slightly, with 36 or 54 pre-months. Its ATT remains small (0.0231 and 0.0223 versus 0.0157). Longer windows worsen the common-period fit for the other outcomes, although the slaughter-weight ATT moves towards zero. The 15-month published specifications remain reference estimates for their shared policy window; these outcome-level results display the sensitivity rather than selecting one window by a cross-outcome rule. [Maximum-history previews](sdid_max_history.md) for B1, B3 and B4 also have worse common-period fit than their published counterparts.

Point estimates by pre-treatment length, with no new inference:

| Outcome | 15 months | 24 months | 36 months | 54 months |
|---|---:|---:|---:|---:|
| National CPI | 0.0759 | 0.0427 | 0.0615 | 0.0597 |
| Country beef HICP | 0.0157 | 0.0283 | 0.0231 | 0.0223 |
| Slaughter weight | -0.0661 | -0.0777 | -0.0206 | -0.0143 |
| Slaughter heads | -0.0350 | -0.0531 | -0.0089 | -0.0091 |
| Extra-EU imports | -0.0801 | -0.0770 | -0.0791 | -0.0843 |

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

Outputs under `outputs/models/stata/` are `sdid_window_audit.csv` (20 point estimates and both fit measures), `sdid_window_decision.csv` (outcome-specific common-period fit comparison, not an automatic publication selection), and `sdid_window_<exercise>_<pre_months>_series.csv` (raw treated and synthetic paths). Diagnostics are supplementary replication outputs. Price inputs preserve double precision; trade joins explicitly retain UTF-8 names and convert keys to fixed-width strings only after checking that no name will be truncated.

## Figure presentation

Every appendix SDiD figure shifts the weighted donor log series by its unweighted mean pre-treatment treated–donor gap. Only the displayed intercept changes; monthly changes, estimation inputs, weights, ATT and inference are unaffected. Each caption states the adjustment, and the original `synthetic` path remains beside `synthetic_aligned` in the CSV. SDiD's time weighting means the post-treatment plotted gap alone is not the ATT.

Figures B2 and B3 both use the axis title “Log consumer price index.” B2 is Statistics Denmark's national CPI; B3 is Eurostat HICP, whose Danish series is compiled by Statistics Denmark. Their common provider does not make their definitions identical; captions retain the CPI/HICP distinction.
