version 19.5
clear all
set more off
set linesize 120
set seed 20260827

capture mkdir "outputs/models/stata"
capture mkdir "outputs/figures/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/scc_meta_analysis.log", text replace

local us_cpi_2024 = 313.689
local usd_dkk = 6.8953
local tax_dkk = 300
local beef_kgco2_kg = 59.6

import delimited using "data/reference/scc_literature_estimates.csv", varnames(1) encoding("utf-8") clear
gen byte is_preferred = upper(preferred) == "TRUE"
gen byte is_eligible = upper(eligible_for_pool) == "TRUE"
destring estimate interval_low interval_high pulse_year dollar_year path_year path_value publication_year, replace force

* One preferred estimate per paper. Values reported for dates other than 2030
* are interpreted as time-invariant when the source supplies no time path.
keep if is_preferred
gen double scc_original = estimate
replace scc_original = exp(ln(78) + (2030 - 2025) / (2050 - 2025) * (ln(175) - ln(78))) if study_id == "barrage2024"
gen int display_year = pulse_year
replace display_year = 2030 if study_id == "barrage2024"

gen double carbon_unit_factor = 1
replace carbon_unit_factor = 12 / 44 if original_unit == "USD/tC"
gen double cpi_source = .
replace cpi_source = 195.3 if dollar_year == 2005
replace cpi_source = 218.056 if dollar_year == 2010
replace cpi_source = 237.017 if dollar_year == 2015
replace cpi_source = 245.120 if dollar_year == 2017
replace cpi_source = 255.657 if dollar_year == 2019
replace cpi_source = 258.811 if dollar_year == 2020
replace cpi_source = `us_cpi_2024' if dollar_year == 2024

gen double scc_usd_2024 = scc_original * carbon_unit_factor * `us_cpi_2024' / cpi_source
gen double interval_low_usd_2024 = interval_low * carbon_unit_factor * `us_cpi_2024' / cpi_source
gen double interval_high_usd_2024 = interval_high * carbon_unit_factor * `us_cpi_2024' / cpi_source

* Source ranges are not relabelled as sampling confidence intervals. For the
* hierarchical bootstrap, lognormal within-study variation is calibrated to
* each range's own coverage when known and to a conservative 95% sensitivity
* range for the Hänsel et al. parameter span. Draws are centered on the paper's
* preferred estimate so every paper retains equal expected weight.
gen double range_z = .
replace range_z = invnormal(.83) if interval_type == "66% model range"
replace range_z = invnormal(.95) if interval_type == "5th-95th quantiles"
replace range_z = invnormal(.975) if interval_type == "parameter range"
gen double sigma_log = (ln(interval_high_usd_2024) - ln(interval_low_usd_2024)) / (2 * range_z) ///
    if interval_low_usd_2024 > 0 & interval_high_usd_2024 > 0 & range_z < .

preserve
keep if is_eligible & !missing(scc_usd_2024)
count
local n_papers = r(N)
quietly summarize scc_usd_2024, detail
local pooled_mean = r(mean)
local pooled_median = r(p50)
local pooled_min = r(min)
local pooled_max = r(max)
tempfile meta_pool
save `meta_pool'

capture program drop one_meta_draw
program define one_meta_draw, rclass
    preserve
    bsample
    gen double within_draw = scc_usd_2024
    replace within_draw = exp(ln(scc_usd_2024) - .5 * sigma_log^2 + sigma_log * rnormal()) if sigma_log < .
    quietly summarize within_draw, meanonly
    return scalar pooled_mean = r(mean)
    restore
end

simulate pooled_mean = r(pooled_mean), reps(10000) seed(20260827) nodots: one_meta_draw
quietly centile pooled_mean, centile(2.5 97.5)
local pooled_low = r(c_1)
local pooled_high = r(c_2)
restore

* Retrieve the pre-announcement beef price from the Stata microdata estimate.
preserve
import delimited using "outputs/models/stata/micro_estimates.csv", varnames(1) clear
quietly summarize pre_treated_average if estimator == "micro_did", meanonly
local pre_beef_price = r(mean)
restore

gen double tax_usd = `tax_dkk' / `usd_dkk'
gen double log_price_gap = ln((`pre_beef_price' + (scc_usd_2024 - tax_usd) * `usd_dkk' * `beef_kgco2_kg' / 1000) / `pre_beef_price')
gen double log_price_gap_low = ln((`pre_beef_price' + (interval_low_usd_2024 - tax_usd) * `usd_dkk' * `beef_kgco2_kg' / 1000) / `pre_beef_price')
gen double log_price_gap_high = ln((`pre_beef_price' + (interval_high_usd_2024 - tax_usd) * `usd_dkk' * `beef_kgco2_kg' / 1000) / `pre_beef_price')
local pooled_gap = ln((`pre_beef_price' + (`pooled_mean' - `tax_dkk' / `usd_dkk') * `usd_dkk' * `beef_kgco2_kg' / 1000) / `pre_beef_price')
local pooled_gap_low = ln((`pre_beef_price' + (`pooled_low' - `tax_dkk' / `usd_dkk') * `usd_dkk' * `beef_kgco2_kg' / 1000) / `pre_beef_price')
local pooled_gap_high = ln((`pre_beef_price' + (`pooled_high' - `tax_dkk' / `usd_dkk') * `usd_dkk' * `beef_kgco2_kg' / 1000) / `pre_beef_price')

export delimited using "outputs/models/stata/scc_literature_calibration.csv", replace

tempfile literature_for_figure
save `literature_for_figure'
clear
set obs 1
gen int n_papers = `n_papers'
gen double mean = `pooled_mean'
gen double ci_low = `pooled_low'
gen double ci_high = `pooled_high'
gen double median = `pooled_median'
gen double min = `pooled_min'
gen double max = `pooled_max'
gen double log_price_gap = `pooled_gap'
gen double log_price_gap_low = `pooled_gap_low'
gen double log_price_gap_high = `pooled_gap_high'
gen str60 inference = "hierarchical paper bootstrap with source-range variation"
export delimited using "outputs/models/stata/scc_meta_summary.csv", replace

* Forest plot corresponding to the former panel B. Notes and sources are kept
* out of the image and supplied by LaTeX.
use `literature_for_figure', clear
keep if !missing(log_price_gap) & inlist(estimate_type, "total SCC", "average SCC")
gen str70 display_label = authors + " (" + string(publication_year, "%4.0f") + ")"
replace display_label = display_label + " [lower bound]" if bound_type == "lower"
sort display_label
encode display_label, gen(plot_order)
quietly count
local n_display = r(N)
label define plot_order 0 "Pooled mean (n=`n_papers')", add
twoway ///
    (rcap log_price_gap_low log_price_gap_high plot_order if !missing(log_price_gap_low, log_price_gap_high), horizontal lcolor(gs8)) ///
    (scatter plot_order log_price_gap if is_eligible, mcolor(black) msymbol(O) msize(small)) ///
    (scatter plot_order log_price_gap if !is_eligible & bound_type != "lower", mcolor(black) msymbol(Oh) msize(small)) ///
    (scatter plot_order log_price_gap if bound_type == "lower", mcolor(black) msymbol(T) msize(small)) ///
    (scatteri 0 `pooled_gap', msymbol(D) mcolor(black) msize(medium)) ///
    (pci 0 `pooled_gap_low' 0 `pooled_gap_high', lcolor(black) lwidth(medthick)), ///
    legend(off) ytitle("") xtitle("Log beef-price increase above the announced tax") ///
    yscale(range(-0.5 `=`n_display'+0.5')) ylabel(0/`n_display', valuelabel angle(horizontal) labsize(vsmall)) ///
    xline(0, lcolor(gs8) lpattern(dash)) graphregion(color(white)) plotregion(color(white)) ///
    xsize(11) ysize(7)
graph export "outputs/figures/stata/scc_meta_forest.png", width(3000) replace

* Policy calibration: three econometric estimates and the meta-analytical gap band.
import delimited using "outputs/models/stata/micro_estimates.csv", varnames(1) clear
keep if estimator == "micro_did"
tempfile micro_results
save `micro_results'
import delimited using "outputs/models/stata/aggregate_estimates.csv", varnames(1) clear
append using `micro_results'
keep if inlist(estimator, "micro_did", "aggregate_did", "aggregate_sdid")
gen double plot_position = .
replace plot_position = 1.25 if estimator == "micro_did"
replace plot_position = 2 if estimator == "aggregate_did"
replace plot_position = 2.75 if estimator == "aggregate_sdid"
sort plot_position
gen double meta_gap = `pooled_gap'
gen double meta_gap_low = `pooled_gap_low'
gen double meta_gap_high = `pooled_gap_high'
export delimited using "outputs/models/stata/beef_policy_calibration.csv", replace
twoway ///
    (rarea meta_gap_low meta_gap_high plot_position, color(gs12%55) lcolor(gs10)) ///
    (line meta_gap plot_position, lcolor(black) lpattern(dash) lwidth(medthick)) ///
    (rcap conf_low conf_high plot_position, lcolor(gs7)) ///
    (scatter estimate plot_position, mcolor(black) msymbol(O) msize(medium)), ///
    legend(order(4 "Econometric estimate" 2 "Meta-analytical carbon-price gap" 1 "95% pooled interval") rows(2) position(6) size(small)) ///
    xlabel(1.25 "Microdata DiD" 2 "Aggregate DiD" 2.75 "Aggregate SDiD", labsize(small) angle(15)) ///
    xscale(range(1 3)) xtitle("") ytitle("Log beef-price effect") yline(0, lcolor(gs8)) ///
    graphregion(color(white)) plotregion(color(white)) xsize(8.5) ysize(5.4)
graph export "outputs/figures/stata/beef_policy_calibration.png", width(2400) replace

log close
