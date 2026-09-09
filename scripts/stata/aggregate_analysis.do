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
gen str3 category3 = substr(product_code, 1, 3)
gen str4 category4 = substr(product_code, 1, 4)
encode category3, gen(category3_id)
encode category4, gen(category4_id)
xtset unit month
gen double ln_cpi = ln(cpi)
tab category3_id, gen(category3_fe)
local n3 = r(r)
tab category4_id, gen(category4_fe)
local n4 = r(r)
local category_covariates
forvalues j = 1/`=`n3'-1' {
    local category_covariates `category_covariates' category3_fe`j'
}
forvalues j = 1/`=`n4'-1' {
    local category_covariates `category_covariates' category4_fe`j'
}
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
export delimited using "outputs/models/stata/aggregate_sdid_series.csv", replace
twoway ///
    (line treated month, lcolor(black) lwidth(medthick)) ///
    (line synthetic month, lcolor(gs7) lpattern(dash) lwidth(medthick)), ///
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
restore

* -------------------------------------------------------------------------
* Aggregate event study, preserving the OECD covariate-adjusted setup while
* using June 2024 as the omitted month immediately before treatment.
* -------------------------------------------------------------------------
local adjustment_terms
foreach covariate of local category_covariates {
    quietly summarize `covariate' if beef, meanonly
    gen double `covariate'_dm = `covariate' - r(mean)
    local adjustment_terms `adjustment_terms' c.beef#ib(`reference').month#c.`covariate'_dm c.beef#c.`covariate'_dm
}
reg ln_cpi beef c.beef#ib(`reference').month `adjustment_terms' i.month i.category3_id i.category4_id, vce(robust)
local event_n = e(N)
tempfile event_results
tempname event_post
postfile `event_post' int month relative_time double estimate std_error conf_low conf_high using `event_results', replace
forvalues current_month = `window_start'/`window_end' {
    local relative_time = `current_month' - `event'
    if `current_month' == `reference' {
        post `event_post' (`current_month') (`relative_time') (0) (.) (.) (.)
    }
    else {
        quietly lincom c.beef#`current_month'.month, level(95)
        post `event_post' (`current_month') (`relative_time') (r(estimate)) (r(se)) (r(lb)) (r(ub))
    }
}
postclose `event_post'
preserve
use `event_results', clear
format month %tm
export delimited using "outputs/models/stata/aggregate_event_study.csv", replace
twoway ///
    (rcap conf_low conf_high relative_time, lcolor(gs8) lwidth(thin)) ///
    (scatter estimate relative_time, mcolor(black) msymbol(O) msize(small)), ///
    legend(off) yline(0, lcolor(gs6) lpattern(dash)) xline(-0.5, lcolor(gs9) lpattern(shortdash)) ///
    xtitle("Months relative to the announcement") ytitle("Log CPI effect and 95% CI") ///
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
