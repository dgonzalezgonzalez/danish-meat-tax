version 19.5
clear all
set more off
set linesize 120
set seed 20260828

capture mkdir "outputs/models/stata"
capture mkdir "outputs/figures/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/beef_trade_pair_sdid.log", text replace

local event = tm(2024m7)
local window_start = tm(2023m4)
local window_end = tm(2025m9)

import delimited using "data/processed/eu_beef_trade_pair_month_panel.csv", ///
    varnames(1) stringcols(_all) encoding("utf-8") clear
rename *, lower
destring product_weight_tonnes, replace dpcomma
destring carcase_weight_tonnes, replace dpcomma
destring value_thousand_euro, replace dpcomma
destring n_product_rows, replace

gen month_id = monthly(month, "YM")
format month_id %tm
gen double ln_imports = ln(carcase_weight_tonnes + 1)
gen byte denmark_importer = member_state == "Denmark"
gen byte post = month_id >= `event'
gen byte treated_post = denmark_importer * post

keep if inrange(month_id, `window_start', `window_end')
isid pair_id month_id
egen unit = group(pair_id), label
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
quietly levelsof unit if denmark_importer, local(treated_units)
local treated_unit_count : word count `treated_units'
quietly summarize carcase_weight_tonnes if denmark_importer & !post, meanonly
local pre_denmark_imports = r(mean)

* Denmark-importer pairs are treated; all other EU-importer/external-partner
* pairs are controls. Outcome is log(1 + carcase-weight tonnes).
sdid ln_imports unit month_id treated_post, vce(placebo) reps(200) seed(20260828)
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
export delimited using "outputs/models/stata/beef_trade_pair_sdid_series.csv", replace
twoway ///
    (line treated month_id, lcolor(black) lwidth(medthick)) ///
    (line synthetic month_id, lcolor(gs7) lpattern(dash) lwidth(medthick)), ///
    legend(order(1 "Denmark-importer pairs" 2 "Weighted donors") rows(1) position(6)) ///
    xline(`event', lcolor(gs9) lpattern(shortdash)) ///
    xtitle("") ytitle("Log(1 + beef imports, carcase-weight tonnes)") ///
    graphregion(color(white)) plotregion(color(white))
graph export "outputs/figures/stata/beef_trade_pair_sdid.png", width(2200) replace
restore

tempfile estimates
tempname estimates_post
postfile `estimates_post' str32 estimator double estimate std_error p_value conf_low conf_high ///
    long observations units treated_units periods double pre_treated_average ///
    str24 time_window str30 outcome str20 inference using `estimates', replace
post `estimates_post' ("beef_trade_pair_sdid") (`sdid_att') (`sdid_se') (`sdid_p') (`sdid_low') (`sdid_high') ///
    (`panel_observations') (`panel_units') (`treated_unit_count') (30) (`pre_denmark_imports') ///
    ("2023m4-2025m9") ("ln(1+carcase_weight_tonnes)") ("placebo")
postclose `estimates_post'
use `estimates', clear
export delimited using "outputs/models/stata/beef_trade_pair_sdid_estimate.csv", replace

display as text "Beef import-pair SDiD ATT: " as result %9.6f `sdid_att'
display as text "Placebo SE: " as result %9.6f `sdid_se'
display as text "Normal-approximation p-value from placebo SE: " as result %9.6f `sdid_p'
display as text "Placebo interval: [" as result %9.6f `sdid_low' as text ", " as result %9.6f `sdid_high' as text "]"
display as text "Panel: " as result `panel_units' as text " importer-partner pairs (" as result `treated_unit_count' as text " Denmark treated) x " as result 30 as text " months"

log close
