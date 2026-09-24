version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/aggregate_omit_june.log", text replace

use "data/processed/statbank_cpi_panel.dta", clear
drop if month == tm(2024m6)
egen t = group(month)
sdid ln_cpi unit t treated_post, vce(placebo) reps(200) seed(20260827)
local sdid_att = e(ATT)
local sdid_se = e(se)

preserve
drop if beef
collapse (mean) ln_cpi, by(month)
rename ln_cpi donor_mean
tempfile donor_month
save `donor_month'
restore
keep if beef
keep month ln_cpi post
merge 1:1 month using `donor_month', assert(match) nogen
gen double gap = ln_cpi-donor_mean
egen t = group(month)
tsset t
newey gap post, lag(2)
local did_att = _b[post]
local did_se = _se[post]

clear
set obs 2
gen str24 estimator = "aggregate_did" in 1
replace estimator = "aggregate_sdid" in 2
gen double estimate = `did_att' in 1
replace estimate = `sdid_att' in 2
gen double std_error = `did_se' in 1
replace std_error = `sdid_se' in 2
gen long observations = 29 in 1
replace observations = 1479 in 2
gen int pre_months = 14
gen int post_months = 15
export delimited "outputs/models/stata/aggregate_omit_june.csv", replace
log close
