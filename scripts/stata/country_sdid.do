version 19.5
clear all
set more off
set linesize 120
set seed 20260827

capture mkdir "outputs/models/stata"
capture mkdir "outputs/figures/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/country_sdid.log", text replace

local event = tm(2024m7)
local window_start = tm(2023m4)
local window_end = tm(2025m9)
local reference = tm(2024m6)

import delimited using "data/processed/eu_beef_hicp_country_month_panel.csv", ///
    varnames(1) stringcols(_all) encoding("utf-8") clear
rename *, lower
destring hicp, replace
assert coicop == "CP01121" & index_unit == "I15"
gen month_id = monthly(month, "YM")
format month_id %tm
gen double ln_price = ln(hicp)
gen byte denmark = geo == "DK"
gen byte post = month_id >= `event'
gen byte treated_post = denmark * post

keep if inrange(month_id, `window_start', `window_end')
assert month_id < `event' if inrange(month_id, `window_start', `reference')
assert month_id >= `event' if inrange(month_id, `event', `window_end')
isid geo month_id
* No interpolation or zero filling. Select complete positive country histories.
bysort geo: egen valid_months = total(hicp > 0 & hicp < .)
preserve
bysort geo: keep if _n == 1
keep geo country valid_months
gen byte included = valid_months == 30
export delimited "outputs/models/stata/country_hicp_coverage.csv", replace
restore
assert valid_months == 30 if denmark
keep if valid_months == 30
assert hicp > 0 & hicp < .
egen unit = group(geo), label
xtset unit month_id

bysort unit: egen byte pre_count = total(month_id < `event')
bysort unit: egen byte post_count = total(month_id >= `event')
assert pre_count == 15
assert post_count == 15
drop pre_count post_count

quietly count
local panel_observations = r(N)
quietly levelsof unit, local(all_units)
local panel_units : word count `all_units'
export delimited "outputs/models/stata/country_hicp_estimation_sample.csv", replace
quietly summarize hicp if denmark & !post, meanonly
local pre_denmark_price = r(mean)

* Main country-level synthetic difference-in-differences specification.
sdid ln_price unit month_id treated_post, vce(placebo) reps(200) seed(20260827)
local sdid_att = e(ATT)
local sdid_se = e(se)
local sdid_p = 2 * normal(-abs(`sdid_att' / `sdid_se'))
local sdid_low = e(ATT_l)
local sdid_high = e(ATT_r)
matrix sdid_series = e(series)

preserve
clear
svmat double sdid_series
rename sdid_series1 month_id
rename sdid_series2 synthetic
rename sdid_series3 treated
format month_id %tm
gen byte post = month_id >= `event'
gen double gap = treated-synthetic
quietly summarize gap if !post, meanonly
local pre_gap = r(mean)
gen double centered_gap_sq = (gap-`pre_gap')^2 if !post
quietly summarize centered_gap_sq, meanonly
local pre_rmse = sqrt(r(mean))
drop centered_gap_sq
* Display only: match Denmark's pre-treatment mean with an additive intercept.
gen double synthetic_aligned = synthetic+`pre_gap'
export delimited using "outputs/models/stata/country_sdid_series.csv", replace
twoway ///
    (line treated month_id, lcolor(black) lwidth(medthick)) ///
    (line synthetic_aligned month_id, lcolor(gs7) lpattern(dash) lwidth(medthick)), ///
    legend(order(1 "Denmark (beef and veal HICP)" 2 "Weighted donors") rows(1) position(6)) ///
    xline(`event', lcolor(gs9) lpattern(shortdash)) ///
    xtitle("") ytitle("Log consumer price index") ///
    graphregion(color(white)) plotregion(color(white))
graph export "outputs/figures/stata/country_sdid.png", width(2200) replace
restore

* Machine-readable estimate and sample metadata.
tempfile estimates
tempname estimates_post
postfile `estimates_post' str24 estimator double estimate std_error p_value conf_low conf_high ///
    long observations units periods double pre_treated_average pre_rmse ///
    str24 time_window str20 treatment_series str20 inference using `estimates', replace
post `estimates_post' ("country_sdid_HICP") (`sdid_att') (`sdid_se') (`sdid_p') (`sdid_low') (`sdid_high') ///
    (`panel_observations') (`panel_units') (30) (`pre_denmark_price') (`pre_rmse') ///
    ("2023m4-2025m9") ("Denmark") ("placebo")
postclose `estimates_post'
use `estimates', clear
export delimited using "outputs/models/stata/country_sdid_estimate.csv", replace

display as text "Country-level HICP SDiD ATT: " as result %9.6f `sdid_att'
display as text "Placebo SE: " as result %9.6f `sdid_se'
display as text "Normal-approximation p-value from placebo SE: " as result %9.6f `sdid_p'
display as text "Placebo interval: [" as result %9.6f `sdid_low' as text ", " as result %9.6f `sdid_high' as text "]"
display as text "Panel: " as result `panel_units' as text " countries x " as result 30 as text " months"

log close
