version 19.5
clear all
set more off
set linesize 120
set seed 20260828

capture mkdir "outputs/models/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/beef_trade_pair_sdid_bootstrap.log", text replace

local event = tm(2024m7)
local window_start = tm(2023m4)
local window_end = tm(2025m9)

import delimited using "data/processed/eu_beef_trade_pair_month_panel.csv", ///
    varnames(1) stringcols(_all) encoding("utf-8") clear
rename *, lower
destring carcase_weight_tonnes, replace dpcomma
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

quietly levelsof unit, local(all_units)
local panel_units : word count `all_units'
quietly levelsof unit if denmark_importer, local(treated_units)
local treated_unit_count : word count `treated_units'
quietly count
local panel_observations = r(N)
quietly summarize carcase_weight_tonnes if denmark_importer & !post, meanonly
local pre_denmark_imports = r(mean)

sdid ln_imports unit month_id treated_post, vce(bootstrap) reps(200) seed(20260828)
local sdid_att = e(ATT)
local sdid_se = e(se)
local sdid_p = 2 * normal(-abs(`sdid_att' / `sdid_se'))
local sdid_low = e(ATT_l)
local sdid_high = e(ATT_r)

tempfile estimates
tempname estimates_post
postfile `estimates_post' str42 estimator double estimate std_error p_value conf_low conf_high ///
    long observations units treated_units periods double pre_treated_average ///
    str24 time_window str30 outcome str20 inference using `estimates', replace
post `estimates_post' ("beef_trade_pair_sdid_bootstrap") (`sdid_att') (`sdid_se') (`sdid_p') (`sdid_low') (`sdid_high') ///
    (`panel_observations') (`panel_units') (`treated_unit_count') (30) (`pre_denmark_imports') ///
    ("2023m4-2025m9") ("ln(1+carcase_weight_tonnes)") ("bootstrap")
postclose `estimates_post'
use `estimates', clear
export delimited using "outputs/models/stata/beef_trade_pair_sdid_bootstrap_estimate.csv", replace

display as text "Beef import-pair bootstrap SDiD ATT: " as result %9.6f `sdid_att'
display as text "Bootstrap SE: " as result %9.6f `sdid_se'
display as text "Normal-approximation p-value from bootstrap SE: " as result %9.6f `sdid_p'
display as text "Bootstrap interval: [" as result %9.6f `sdid_low' as text ", " as result %9.6f `sdid_high' as text "]"
display as text "Panel: " as result `panel_units' as text " importer-partner pairs (" as result `treated_unit_count' as text " Denmark treated) x " as result 30 as text " months"

log close
