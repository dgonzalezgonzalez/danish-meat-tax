version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/model_magnitude_scenarios.log", text replace

import delimited "outputs/models/stata/aggregate_estimates.csv", varnames(1) clear
quietly summarize estimate if estimator == "aggregate_did", meanonly
assert r(N) == 1
local national_beta = r(mean)
import delimited "outputs/models/stata/country_sdid_estimate.csv", varnames(1) clear
quietly summarize estimate if estimator == "country_sdid_HICP", meanonly
assert r(N) == 1
local country_beta = r(mean)
import delimited "outputs/models/stata/micro_estimates.csv", varnames(1) clear
quietly summarize pre_treated_average if estimator == "micro_did", meanonly
assert r(N) == 1
local observed_anchor = r(mean)
import delimited "outputs/models/stata/scc_meta_summary.csv", varnames(1) clear
assert _N == 1
local average_rate = tax_effective_2024_dkk[1]
local broad_intensity = 59.6

clear
set obs 3
gen str28 scenario = "illustrative_100" in 1
replace scenario = "provisional_event_mean" in 2
replace scenario = "illustrative_200" in 3
gen double anchor_dkk_kg = 100 in 1
replace anchor_dkk_kg = `observed_anchor' in 2
replace anchor_dkk_kg = 200 in 3
gen double national_cpi_dkk_kg = anchor_dkk_kg * (exp(`national_beta') - 1)
gen double country_hicp_dkk_kg = anchor_dkk_kg * (exp(`country_beta') - 1)
gen double broad_output_wedge_dkk_kg = `average_rate' * `broad_intensity' / 1000
gen double two_date_bound_delta1_dkk_kg = broad_output_wedge_dkk_kg / 2
gen double break_even_scc_usd_tco2 = ///
    (national_cpi_dkk_kg + broad_output_wedge_dkk_kg) * 1000 / (6.8953 * `broad_intensity')
gen double national_beta = `national_beta'
gen double country_beta = `country_beta'
export delimited "outputs/models/stata/model_magnitude_scenarios.csv", replace
list scenario anchor_dkk_kg national_cpi_dkk_kg country_hicp_dkk_kg, noobs
log close
