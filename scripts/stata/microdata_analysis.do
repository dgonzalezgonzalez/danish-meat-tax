version 19.5
clear all
set more off
set linesize 120
set seed 20260827

capture mkdir "outputs/models/stata"
capture mkdir "outputs/figures/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/microdata_analysis.log", text replace

use "data/processed/commodity_panel_stata.dta", clear

capture confirm string variable treated
if !_rc {
    gen byte untreated_control = lower(treated) == "false"
}
else {
    gen byte untreated_control = treated == 0
}
gen byte beef = treatment_group == "beef"
keep if beef | untreated_control
destring relative_time did log_price price, replace force
keep if relative_time <= 15

capture confirm string variable period
if !_rc {
    gen daily_period = date(period, "YMD")
    gen month = mofd(daily_period)
}
else {
    gen month = mofd(period)
}
format month %tm
egen unit = group(unit_id), label
gen byte treated_post = beef * (relative_time > 0)
replace did = treated_post

quietly summarize month, meanonly
local micro_start = r(min)
local micro_end = r(max)
quietly levelsof month, local(micro_period_values)
local micro_periods : word count `micro_period_values'
quietly levelsof unit, local(micro_unit_values)
local micro_units : word count `micro_unit_values'
quietly summarize price if beef & relative_time < 0, meanonly
local pre_beef_price = r(mean)

* Main product-store DiD with product-store and month fixed effects.
areg log_price treated_post i.month, absorb(unit) vce(cluster unit)
local did_att = _b[treated_post]
local did_se = _se[treated_post]
local did_p = 2 * ttail(e(df_r), abs(`did_att' / `did_se'))
local did_low = `did_att' - invttail(e(df_r), .025) * `did_se'
local did_high = `did_att' + invttail(e(df_r), .025) * `did_se'
local did_n = e(N)
local did_r2 = e(r2)

* Beef event study. June 2024 is excluded from the source panel and month -1
* (May 2024) is the omitted reference period. July 2024, the first complete
* post-announcement month, is displayed as event time zero.
gen int event_time = relative_time
replace event_time = relative_time - 1 if relative_time > 0
local event_variables
local pretest_variables
quietly levelsof event_time, local(relative_periods)
foreach relative_period of local relative_periods {
    if `relative_period' != -1 {
        if `relative_period' < 0 local event_name event_m`=abs(`relative_period')'
        if `relative_period' == 0 local event_name event_0
        if `relative_period' > 0 local event_name event_p`relative_period'
        gen byte `event_name' = beef * (event_time == `relative_period')
        local event_variables `event_variables' `event_name'
        if `relative_period' < -1 local pretest_variables `pretest_variables' `event_name'
    }
}
areg log_price `event_variables' i.month, absorb(unit) vce(cluster unit)
test `pretest_variables'
local pretrend_p = r(p)

tempfile event_results
tempname event_post
postfile `event_post' int relative_time double estimate std_error conf_low conf_high using `event_results', replace
foreach relative_period of local relative_periods {
    if `relative_period' == -1 {
        post `event_post' (`relative_period') (0) (.) (.) (.)
    }
    else {
        if `relative_period' < 0 local event_name event_m`=abs(`relative_period')'
        if `relative_period' == 0 local event_name event_0
        if `relative_period' > 0 local event_name event_p`relative_period'
        local event_estimate = _b[`event_name']
        local event_se = _se[`event_name']
        post `event_post' (`relative_period') (`event_estimate') (`event_se') ///
            (`event_estimate' - invttail(e(df_r), .025) * `event_se') ///
            (`event_estimate' + invttail(e(df_r), .025) * `event_se')
    }
}
postclose `event_post'
preserve
use `event_results', clear
export delimited using "outputs/models/stata/micro_event_study.csv", replace
twoway ///
    (rcap conf_low conf_high relative_time, lcolor(gs8) lwidth(thin)) ///
    (scatter estimate relative_time, mcolor(black) msymbol(O) msize(small)), ///
    legend(off) yline(0, lcolor(gs6) lpattern(dash)) xline(0, lcolor(gs9) lpattern(shortdash)) ///
    xtitle("Months relative to the announcement") ytitle("Log price effect and 95% CI") ///
    xlabel(-8(4)12 14) graphregion(color(white)) plotregion(color(white))
graph export "outputs/figures/stata/micro_event_study.png", width(2200) replace
restore

* Descriptive statistics from the main beef-versus-untreated sample.
tempfile descriptives
tempname desc_post
postfile `desc_post' str12 sample str28 variable long observations double mean sd p25 median p75 using `descriptives', replace
foreach sample in all beef controls {
    local condition
    if "`sample'" == "beef" local condition if beef
    if "`sample'" == "controls" local condition if untreated_control
    quietly summarize price `condition', detail
    post `desc_post' ("`sample'") ("Normalized price") (r(N)) (r(mean)) (r(sd)) (r(p25)) (r(p50)) (r(p75))
}
preserve
bysort unit: gen byte first_unit = _n == 1
bysort unit: gen int months_observed = _N
foreach sample in all beef controls {
    local condition if first_unit
    if "`sample'" == "beef" local condition if first_unit & beef
    if "`sample'" == "controls" local condition if first_unit & untreated_control
    quietly summarize months_observed `condition', detail
    post `desc_post' ("`sample'") ("Months per product-store") (r(N)) (r(mean)) (r(sd)) (r(p25)) (r(p50)) (r(p75))
}
restore
postclose `desc_post'
preserve
use `descriptives', clear
export delimited using "outputs/models/stata/descriptive_statistics.csv", replace
restore

tempfile estimates
tempname estimates_post
postfile `estimates_post' str12 estimator double estimate std_error p_value conf_low conf_high ///
    long observations units periods double pre_treated_average r_squared ///
    str24 time_window str3 lags_only str3 covariates str28 inference using `estimates', replace
post `estimates_post' ("micro_did") (`did_att') (`did_se') (`did_p') (`did_low') (`did_high') ///
    (`did_n') (`micro_units') (`micro_periods') (`pre_beef_price') (`did_r2') ("2023m11-2025m9") ("No") ("No") ("clustered by product-store")
postclose `estimates_post'
use `estimates', clear
gen double pretrend_p_value = `pretrend_p' if estimator == "micro_did"
export delimited using "outputs/models/stata/micro_estimates.csv", replace

log close
