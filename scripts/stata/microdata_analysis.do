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
* is the omitted reference period, matching the paper's existing design.
local event_variables
local pretest_variables
quietly levelsof relative_time, local(relative_periods)
foreach relative_period of local relative_periods {
    if `relative_period' != -1 {
        if `relative_period' < 0 local event_name event_m`=abs(`relative_period')'
        if `relative_period' > 0 local event_name event_p`relative_period'
        gen byte `event_name' = beef * (relative_time == `relative_period')
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
    xlabel(-8(4)16) graphregion(color(white)) plotregion(color(white))
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
    quietly summarize log_price `condition', detail
    post `desc_post' ("`sample'") ("Log normalized price") (r(N)) (r(mean)) (r(sd)) (r(p25)) (r(p50)) (r(p75))
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

* Synthetic DiD robustness estimate at the complete commodity-store level.
preserve
collapse (mean) log_price price (firstnm) beef relative_time, by(store commodity month)
egen commodity_store = group(store commodity), label
bysort commodity_store: gen int support = _N
keep if support == `micro_periods'
gen byte sdid_treatment = beef * (relative_time > 0)
quietly levelsof commodity_store, local(sdid_unit_values)
local sdid_units : word count `sdid_unit_values'
quietly count
local sdid_observations = r(N)
quietly summarize price if beef & relative_time < 0, meanonly
local sdid_pre_price = r(mean)
sdid log_price commodity_store month sdid_treatment, vce(placebo) reps(200) seed(20260827)
local sdid_att = e(ATT)
local sdid_se = e(se)
local sdid_p = 2 * normal(-abs(`sdid_att' / `sdid_se'))
local sdid_low = e(ATT_l)
local sdid_high = e(ATT_r)
matrix micro_sdid_series = e(series)
tempfile sdid_panel
save `sdid_panel'
clear
svmat double micro_sdid_series
rename micro_sdid_series1 month
rename micro_sdid_series2 synthetic
rename micro_sdid_series3 treated
format month %tm
export delimited using "outputs/models/stata/micro_sdid_series.csv", replace
twoway ///
    (line treated month, lcolor(black) lwidth(medthick)) ///
    (line synthetic month, lcolor(gs7) lpattern(dash) lwidth(medthick)), ///
    legend(order(1 "Beef" 2 "Synthetic control") rows(1) position(6)) ///
    xtitle("") ytitle("Log normalized price") graphregion(color(white)) plotregion(color(white))
graph export "outputs/figures/stata/micro_sdid.png", width(2200) replace
use `sdid_panel', clear
restore

tempfile estimates
tempname estimates_post
postfile `estimates_post' str12 estimator double estimate std_error p_value conf_low conf_high ///
    long observations units periods double pre_treated_average r_squared ///
    str24 time_window str3 lags_only str3 covariates str28 inference using `estimates', replace
post `estimates_post' ("micro_did") (`did_att') (`did_se') (`did_p') (`did_low') (`did_high') ///
    (`did_n') (`micro_units') (`micro_periods') (`pre_beef_price') (`did_r2') ("2023m11-2025m9") ("No") ("No") ("clustered by product-store")
post `estimates_post' ("micro_sdid") (`sdid_att') (`sdid_se') (`sdid_p') (`sdid_low') (`sdid_high') ///
    (`sdid_observations') (`sdid_units') (`micro_periods') (`sdid_pre_price') (.) ("2023m11-2025m9") ("No") ("No") ("placebo")
postclose `estimates_post'
use `estimates', clear
gen double pretrend_p_value = `pretrend_p' if estimator == "micro_did"
export delimited using "outputs/models/stata/micro_estimates.csv", replace

log close
