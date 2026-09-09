# Validation record — 9 September 2026

## Executed checks

- Reprocessed the original June 2026 grocery snapshot after updating policy classification; rebuilt the monthly product–store panel and Stata input. The grocery ATT changed because poultry/eggs were removed as controls and ambiguous mixtures were reclassified consistently during preprocessing.
- Rebuilt both Commission panels through the existing PowerShell scripts: 23 countries / 690 observations for AO2 prices; 383 importer–partner pairs / 11,490 observations for extra-EU imports, including 17 treated pairs and 7,775 zero cells.
- Decoded the official Eurostat JSON-stat payload, preserving missing values and flags. All six production samples have 27 complete positive country series.
- Ran the complete `scripts/stata/master.do` successfully with Stata/MP 19.5. Final wall time: **729.297 seconds**. The master includes microdata, aggregate CPI, country prices, trade placebo and bootstrap, six production specifications, national production descriptors, and SCC calibration. All seven analytical logs reached normal closure; the batch log contains no terminal Stata `r(...)` error.
- Ran **27 unittest tests**, including the offline fixture, production JSON-stat ordering/missing/flag tests, rejection of dairy controls, and detection of a Stata do-file error despite a zero operating-system exit code. All passed.
- Verified all **nine** raw research inputs against the SHA-256 manifest using `scripts/verify_inputs.py`.
- Parsed `scripts/replicate.ps1` with the PowerShell parser: no syntax errors. Its constituent preprocessing and estimation commands were executed; the new wrapper itself was not separately rerun end to end after the successful master validation.
- Compiled the revised manuscript with pdfLaTeX, BibTeX, and resolving pdfLaTeX passes. The **33-page PDF** has no undefined references/citations or overfull/underfull warnings in the final TeX log. Rendered all pages through Poppler and visually checked page layouts, equations, tables, figures, captions, and bibliography, with individual checks of Table 1, Table B2, and the four-panel surface figure.
- `git diff --check` passed. Existing unrelated world-price experiments and browser artifacts were preserved.
- The academic-writing skill passed the standard skill validator. Its corpus documents four distinct research projects behind seven Scholar entries, separating versions and coauthored evidence; the final instructions incorporate the author's table and manuscript-detail preferences.

## Author-comment revision checks

- Re-ran all 27 unit tests successfully after pipeline integration changes.
- Ran `production_descriptives.do` against the exact main estimation samples: six descriptive rows, with 810/30/780 country-months for all countries/Denmark/donors per outcome. The production analysis calls this do-file automatically.
- Ran the revised pipeline `outputs` stage successfully, including SCC analysis, the nested persistence do-file, and the Python renderer. The previously validated production and price estimators were unchanged, so the complete estimation master was not redundantly rerun after these additions.
- In the initial coefficient-only version, verified all 10,404 unique surface cells: taxable shares .25/.50/.75/1, full a/lambda support, accounting identities, interval order, and collapsed coefficient uncertainty at zero persistence. The global point minimum is 47.61 DKK/kg; the lowest conditional confidence bound is 36.44. The original HAC endpoints are transformed in reverse order because R decreases in the coefficient.
- Matplotlib 3.10.8 renders Stata-calculated grids. Visual inspection found and corrected overlapping panel labels and clipped vertical-axis labels. The four-panel figure retains dashed interval meshes and uses one common vertical scale.
- The paper uses the preferred official CPI DiD coefficient with an explicit grocery-level anchor assumption. The SDiD equations follow Arkhangelsky et al. (2021), equations 1.1 and 2.4–2.5; notation preserves the manuscript's unit/time effects. JEL codes were checked against the American Economic Association classification.

## Research audit findings

The model's comparative-static signs and proofs were retained, with explicit competitive-equilibrium scope, interiority, fixed-stock counterexample, finite-horizon qualifications, and the bounded-curvature condition for distant implementation. The multi-period stable root is defined in distance from implementation. Domestic retail incidence remains conditional on omitted trade and distribution margins.

The production evidence does not establish contraction: main weight ATT -0.0661, placebo SE 0.0811, and long-pre adjusted ATT -0.0055. The paper reports all six specifications and explicitly discusses the concurrent end of Denmark's cattle nitrate derogation. Food-control substitution, common policy shocks, and inference dependence across products or importer pairs remain limitations. An earlier independent-samples test comparing price estimates was removed because the estimates concern the same market.

Calibration corrections include the 2022 price base of statutory rates, the Cai–Lontzek combined-risk value of 124 USD/tC, and Cai et al. (2016)'s 2010 pulse and dollar base. The corrected selected-study mean is 160.39 USD/tCO2 with sensitivity envelope 79.50–366.63. This envelope is not a sampling confidence interval. Constant values at 2030, the assigned probability coverage of the ethical-parameter span, Pindyck's assumed monetary base and average-SCC object, and lifecycle versus taxable emissions are explicit assumptions. Leave-one-out and persistence/additional-pass-through scenarios are exported.

## Practical limits

This is validation in the stated local environment, not an independent clean-machine replication or a journal certification. Historical inputs are identified by hashes but lack a complete immutable public deposit. Source reuse rights, an original-code license, and author preservation/assistance declarations remain to be supplied for a journal deposit. No empirical inference is drawn from the deterministic fixture.

## Combined SCC and coefficient uncertainty

Figure 4 now uses pointwise combined sensitivity intervals rather than coefficient-only confidence bounds. The original SCC simulation exports 10,000 draws; persistence analysis pairs these with independent beta_hat + HAC_SE*t(28) draws and exports the paired inputs. Price anchor, emissions intensity, FX, and tax rate remain fixed. The independence and reference-distribution assumptions are stated in the manuscript and calibration documentation.

The complete updated `outputs` stage passed. An independent NumPy recomputation from the exported paired draws matched Stata's 2.5th/97.5th percentiles (Weibull sample-quantile convention) at a=0, .5, and 1. All 10,404 cells have ordered intervals; intervals shift by exactly the deterministic implementation amount, and SCC uncertainty remains at a=0. Bounds are stored in double precision. At a=f=lambda=1 the combined interval is 11.04–132.35 DKK/kg; the point remains 47.61. The old coefficient-only interval remains exported for comparison.

The rebuilt 33-page PDF has no unresolved references or overfull/underfull boxes. Figure 4 and the affected surrounding pages were rendered and visually checked; all panels use the same zero-based vertical scale and the legend identifies combined sensitivity bounds.
