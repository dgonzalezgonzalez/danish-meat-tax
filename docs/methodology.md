# Methodology

## Research question and scope

The paper asks whether beef-market outcomes during Denmark's 2024 cattle-policy transition are compatible with anticipation of a future emissions charge. The April-announced, July-effective end of the cattle nitrate derogation overlaps the June tax agreement; the post contrast cannot isolate the levy. It reports beef only and estimates all analytical models in Stata.

## Grocery change-event diagnostic

The grocery source's `priceHistory` records changes, not unchanged daily posted quotes, and the frozen snapshot has no complete historical availability record. The supplementary regression averages recorded event quotes within product--store--months and regresses their log normalized price on `beef × post`, product--store fixed effects, and month fixed effects. It describes repricing records rather than a monthly posted-price causal effect. Product--store clustering does not capture national policy uncertainty. June 2024 is excluded. The sample runs from October 2023 through September 2025. See [the grocery audit](grocery_history_audit.md).

Beef is compared only with classified untreated foods. Pork, poultry, eggs, lamb/sheep/goat, dairy, mixed livestock products, non-food products, and unknown products are excluded from beef's control group. A saved Jev name audit screens candidate beef products, retaining 118 strongly supported plain-meat names after explicit false-positive exclusions. Price normalization converts mass to DKK/kg and volume to DKK/litre, including a multipack fallback; unsupported units are excluded.

The event study excludes the partial announcement month of June 2024, uses May as the omitted `t=-1` reference, leaves the June event-month slot empty at zero, and labels July 2024 as `t=+1`. It tests the remaining pre-period interactions jointly. Its bars reflect only product--store clustering for the selected event records.

## Official aggregate data

The official panel uses Statistics Denmark PRIS01 monthly CPI series under COICOP 2018. Beef and veal (011221) is treated. The donor pool excludes all treated or plausibly exposed meat and dairy categories. The balanced sample contains 51 series over April 2023--September 2025, exactly 15 pre and 15 post months.

The lags-only DiD preserves the prior OECD specification: subtract the monthly donor mean from log beef CPI, regress the gap on the post indicator, and compute Newey--West standard errors with two lags.

The lags-only regression contains 30 monthly gaps after cross-sectional averaging; Table 2 reports both 30 regression observations and the 1,530 underlying series--months. HAC lags 3, 4, and 6 are also exported. July--December 2024 and January--September 2025 gap contrasts are reported separately because the average effect is concentrated in 2025.

Synthetic DiD uses Stata's `sdid` command with 200 placebo replications. A central same-product check compares Danish beef-and-veal HICP with the other 26 EU countries, April 2023--September 2025. This changes the counterfactual, while the Danish series still comes from the national statistical provider. Extra-EU bilateral trade is a separate diagnostic and excludes intra-EU flows. The optional window audit varies pre-period support by outcome; fit for one outcome is not a veto for another, and its `vce(noinference)` results do not gain new standard errors.

## SCC synthesis

One selected benchmark enters per included paper. Pindyck measures an average rather than a marginal SCC; its exclusion is reported. Values are harmonized to 2024 USD/tCO2. Other-year estimates are held constant as an explicit sensitivity assumption even when a source supplies a changing path; Barrage--Nordhaus is interpolated within its published path. Ten papers receive equal weight.

The interval uses 10,000 hierarchical bootstrap replications. Each replication resamples ten papers with replacement. For a paper with point estimate `theta` and positive central range `[L,U]` of coverage `1-2 alpha`, within-paper dispersion is `sigma=(log(U)-log(L))/(2*Phi^{-1}(1-alpha))`; its draw is lognormal with log mean `log(theta)-sigma^2/2`, so the arithmetic expectation remains `theta`. Papers without usable ranges remain at their point estimates. The replication statistic is the mean of ten selected within-paper draws, and the reported endpoints are the 2.5th and 97.5th percentiles of the replicated means. The result is a sensitivity envelope, not a conventional common-effect confidence interval.

The accounting map is evaluated separately at DKK 120/tCO2e, the effective average output burden after the 60 percent per-animal deduction, and DKK 300/tCO2e, the 2030 marginal abatement incentive. These quoted rates are in 2022 prices and are converted to 2024 DKK with PRIS04. The conditional level-price exercise separates unknown causal attribution `q`, persistence `a`, taxable lifecycle share `f`, and **additional** implementation pass-through `lambda`. The plotted surfaces set `q=1`; a separate table shows `q=0` and `q=.5`. A total pass-through estimate cannot be added to an earlier price increment. The grocery level anchor is provisional because selected change events are not posted-price spells.

## Theoretical interpretation

The paper represents competitive equilibrium with a strictly concave market potential in current and implementation-date output, normalized at an arbitrary positive reference quantity so isoelastic demand is well-defined for every positive elasticity. A credible expected future emissions wedge reduces both quantities when costly adjustment links production plans, raising the current price. The implementation-date output plan is committed before policy uncertainty resolves. Constant-elasticity quasi-linear preferences generate isoelastic beef demand, while Cobb--Douglas production with capital fixed over the policy horizon generates convex costs and upward-sloping supply. The resulting exact local comparative statics connect announcement incidence to demand elasticity, production curvature, discounting, and adjustment costs; finite changes are first-order approximations. Under stationary two-date assumptions, the finite model price change is bounded by `delta/(1+delta)` times the expected future output wedge. A fixed-stock counterexample instead shifts slaughter forward and lowers the current price when liability falls on later slaughter. A herd stock-flow representation separates births, slaughter counts, carcass weight, trade, and retail margins. The slaughter estimates remain imprecise and sensitive to the pre-treatment window; mean carcass weight is estimated directly rather than by subtracting separately weighted ATTs.

## Limitations

- The Danish CPI comparison uses other foods as controls; the EU HICP comparison uses the same beef product in other countries. Neither isolates the tax from Denmark's nitrate-derogation change.
- Grocery change histories lack dated product availability. Their diagnostic and level anchor are subject to repricing selection.
- Automated classification and package parsing can create measurement error.
- The official panel has one treated beef series and 15 pre-periods; same-product country-price and longer-window comparisons show sensitivity to counterfactual choice.
- SCC estimates are structurally heterogeneous; the pooled interval is a sensitivity envelope.
- Carbon-price mapping is an accounting exercise, not a structural incidence or welfare model.
- Slaughter estimates do not establish contraction; they do not measure herd size or emissions.
- The April-announced, July-effective end of the cattle nitrate derogation is an unresolved confound.

## Production extension

See `production_analysis.md`: six Stata SDiD specifications, a direct mean-carcass-weight estimate, EU27 bovine slaughter, positive complete panels, no missing-to-zero replacement, main 15/15 months and two temporal sensitivities. The appendix reports full results.
