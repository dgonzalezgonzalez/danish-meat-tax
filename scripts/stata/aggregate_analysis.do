version 19.5
clear all
set more off
set linesize 120
set seed 20260827

capture mkdir "outputs/models/stata"
capture mkdir "outputs/figures/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/aggregate_analysis.log", text replace

local event = tm(2024m7)
local window_start = tm(2023m4)
local window_end = tm(2025m9)
local reference = tm(2024m6)

import delimited using "data/raw/statbank_pris01.csv", delimiter(";") varnames(1) stringcols(_all) encoding("utf-8") clear
rename *, lower

gen str12 product_code_raw = substr(varegr, 1, strpos(varegr, " ") - 1)
gen str8 product_code = subinstr(product_code_raw, ".", "", .)
gen strL product_name = substr(varegr, strpos(varegr, " ") + 1, .)
gen month = monthly(tid, "YM")
format month %tm
replace indhold = "" if indhold == ".."
destring indhold, replace dpcomma force
rename indhold cpi

* Retain terminal food and non-alcoholic beverage indices under COICOP 2018.
gen byte food_leaf = ///
    (strlen(product_code) == 5 & inlist(substr(product_code, 1, 3), "011", "012") & product_code != "01122") | ///
    (strlen(product_code) == 6 & substr(product_code, 1, 3) == "011")
keep if food_leaf

* Beef is treated. Policy-exposed or compositionally ambiguous livestock foods
* are excluded from the donor pool, including poultry and eggs.
gen byte beef = product_code == "011221"
gen byte excluded_livestock = inlist(product_code, "011222", "011223", "01123", "01124", "01125")
replace excluded_livestock = 1 if inlist(product_code, "01141", "01142", "01143", "01145", "01146", "01147", "01152")
replace excluded_livestock = 1 if inlist(product_code, "011224", "01144")
drop if excluded_livestock
drop if missing(cpi, month)

egen unit = group(product_code), label
xtset unit month
gen double ln_cpi = ln(cpi)
keep if inrange(month, `window_start', `window_end')
assert month < `event' if inrange(month, `window_start', `reference')
assert month >= `event' if inrange(month, `event', `window_end')
gen byte post = month >= `event'
gen byte treated_post = beef * post
bysort unit: egen byte pre_count = total(month < `event')
bysort unit: egen byte post_count = total(month >= `event')
keep if pre_count == 15 & post_count == 15
assert pre_count == 15
assert post_count == 15
drop pre_count post_count

compress
save "data/processed/statbank_cpi_panel.dta", replace
export delimited using "data/processed/statbank_cpi_panel.csv", replace

quietly count
local panel_observations = r(N)
quietly levelsof unit, local(all_units)
local panel_units : word count `all_units'
quietly summarize cpi if beef & !post, meanonly
local pre_beef_cpi = r(mean)

* -------------------------------------------------------------------------
* Descriptive statistics for the balanced official CPI sample.
* -------------------------------------------------------------------------
tempfile aggregate_descriptives
tempname aggregate_desc_post
postfile `aggregate_desc_post' str12 sample str28 variable long observations double mean sd p25 median p75 using `aggregate_descriptives', replace
foreach sample in all beef donors {
    local condition
    if "`sample'" == "beef" local condition if beef
    if "`sample'" == "donors" local condition if !beef
    quietly summarize cpi `condition', detail
    post `aggregate_desc_post' ("`sample'") ("Consumer price index") (r(N)) (r(mean)) (r(sd)) (r(p25)) (r(p50)) (r(p75))
}
postclose `aggregate_desc_post'
preserve
use `aggregate_descriptives', clear
export delimited using "outputs/models/stata/aggregate_descriptive_statistics.csv", replace
restore

* -------------------------------------------------------------------------
* Synthetic difference-in-differences with the same sdid placebo command.
* -------------------------------------------------------------------------
sdid ln_cpi unit month treated_post, vce(placebo) reps(200) seed(20260827)
local sdid_att = e(ATT)
local sdid_se = e(se)
local sdid_p = 2 * normal(-abs(`sdid_att' / `sdid_se'))
local sdid_low = e(ATT_l)
local sdid_high = e(ATT_r)
matrix sdid_series = e(series)
preserve
clear
svmat double sdid_series
rename sdid_series1 month
rename sdid_series2 synthetic
rename sdid_series3 treated
format month %tm
* Display only: align the pre-treatment means; retain raw donor levels.
gen double display_gap = treated - synthetic
quietly summarize display_gap if month < `event', meanonly
gen double synthetic_aligned = synthetic + r(mean)
drop display_gap
export delimited using "outputs/models/stata/aggregate_sdid_series.csv", replace
twoway ///
    (line treated month, lcolor(black) lwidth(medthick)) ///
    (line synthetic_aligned month, lcolor(gs7) lpattern(dash) lwidth(medthick)), ///
    legend(order(1 "Beef and veal" 2 "Weighted donors") rows(1) position(6)) ///
    xline(`event', lcolor(gs9) lpattern(shortdash)) ///
    xtitle("") ytitle("Log consumer price index") graphregion(color(white)) plotregion(color(white))
graph export "outputs/figures/stata/aggregate_sdid.png", width(2200) replace
restore

* -------------------------------------------------------------------------
* Lags-only aggregate DiD. The OECD specification is intentionally unchanged:
* collapse the donor mean, difference it from beef, and use Newey-West lag(2).
* Only the symmetric 15-month window and donor composition differ.
* -------------------------------------------------------------------------
preserve
drop if beef
collapse (mean) ln_cpi, by(month)
rename ln_cpi cpi_bar
tempfile donor_mean
save `donor_mean'
restore

preserve
keep if beef
keep month ln_cpi
rename ln_cpi cpi_beef
merge 1:1 month using `donor_mean', nogen assert(3)
gen double cpi_diff_bar = cpi_beef - cpi_bar
gen byte post_hac = month >= `event'
tsset month
sort month
newey cpi_diff_bar post_hac, lag(2)
local did_att = _b[post_hac]
local did_se = _se[post_hac]
local did_p = 2 * ttail(e(df_r), abs(`did_att' / `did_se'))
local did_low = `did_att' - invttail(e(df_r), .025) * `did_se'
local did_high = `did_att' + invttail(e(df_r), .025) * `did_se'
local did_n = e(N)
local did_r2 = e(r2)

* A monthly gap is the unit of inference. Show sensitivity to plausible
* truncation lags rather than treating the two-lag threshold as decisive.
tempfile hac_results timing_results
tempname hac_post timing_post
postfile `hac_post' byte max_lag double estimate std_error p_value using `hac_results', replace
foreach bandwidth in 2 3 4 6 {
    quietly newey cpi_diff_bar post_hac, lag(`bandwidth')
    local p = 2 * ttail(e(df_r), abs(_b[post_hac] / _se[post_hac]))
    post `hac_post' (`bandwidth') (_b[post_hac]) (_se[post_hac]) (`p')
}
postclose `hac_post'
quietly summarize cpi_diff_bar if month < `event', meanonly
local pre_gap = r(mean)
postfile `timing_post' str22 period int months double gap_vs_pre using `timing_results', replace
quietly summarize cpi_diff_bar if inrange(month, tm(2024m7), tm(2024m12)), meanonly
post `timing_post' ("2024m7-2024m12") (r(N)) (r(mean) - `pre_gap')
quietly summarize cpi_diff_bar if inrange(month, tm(2025m1), tm(2025m9)), meanonly
post `timing_post' ("2025m1-2025m9") (r(N)) (r(mean) - `pre_gap')
quietly summarize cpi_diff_bar if month >= `event', meanonly
post `timing_post' ("2024m7-2025m9") (r(N)) (r(mean) - `pre_gap')
postclose `timing_post'
tempfile cpi_gap
save `cpi_gap'
use `hac_results', clear
export delimited using "outputs/models/stata/aggregate_hac_sensitivity.csv", replace
use `timing_results', clear
export delimited using "outputs/models/stata/aggregate_timing.csv", replace
use `cpi_gap', clear
restore

* -------------------------------------------------------------------------
* Descriptive monthly beef-minus-food gap, relative to June 2024.
* A saturated treated-month regression has unit leverage for the lone treated
* series; its generic robust intervals cannot measure national shocks.
* -------------------------------------------------------------------------
preserve
drop if beef
collapse (mean) ln_cpi, by(month)
rename ln_cpi donor_log_cpi
tempfile event_donors
save `event_donors'
restore
preserve
keep if beef
keep month ln_cpi
merge 1:1 month using `event_donors', nogen assert(3)
gen double price_gap = ln_cpi - donor_log_cpi
quietly summarize price_gap if month == `reference', meanonly
assert r(N) == 1
gen double estimate = price_gap - r(mean)
gen int relative_time = month - `event'
gen double std_error = .
gen double conf_low = .
gen double conf_high = .
keep month relative_time estimate std_error conf_low conf_high
format month %tm
export delimited using "outputs/models/stata/aggregate_event_study.csv", replace
twoway scatter estimate relative_time, ///
    mcolor(black) msymbol(O) msize(small) ///
    legend(off) yline(0, lcolor(gs6) lpattern(dash)) xline(-0.5, lcolor(gs9) lpattern(shortdash)) ///
    xtitle("Months relative to July 2024") ytitle("Beef-minus-food log CPI gap, relative to June") ///
    xlabel(-15(5)15) graphregion(color(white)) plotregion(color(white))
graph export "outputs/figures/stata/aggregate_event_study.png", width(2200) replace
restore

* Estimator-level machine-readable results for tables and calibration.
tempfile estimates
tempname estimates_post
postfile `estimates_post' str20 estimator double estimate std_error p_value conf_low conf_high ///
    long observations units periods double pre_treated_average r_squared ///
    str24 time_window str3 lags_only str3 covariates str20 inference using `estimates', replace
post `estimates_post' ("aggregate_did") (`did_att') (`did_se') (`did_p') (`did_low') (`did_high') ///
    (`panel_observations') (`panel_units') (30) (`pre_beef_cpi') (`did_r2') ("2023m4-2025m9") ("Yes") ("No") ("HAC Newey-West lag 2")
post `estimates_post' ("aggregate_sdid") (`sdid_att') (`sdid_se') (`sdid_p') (`sdid_low') (`sdid_high') ///
    (`panel_observations') (`panel_units') (30) (`pre_beef_cpi') (.) ("2023m4-2025m9") ("No") ("No") ("placebo")
postclose `estimates_post'
use `estimates', clear
export delimited using "outputs/models/stata/aggregate_estimates.csv", replace

log close
