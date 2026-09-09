version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/persistence_analysis.log", text replace
* Preferred official CPI DiD; preserve the original HAC confidence endpoints.
import delimited "outputs/models/stata/aggregate_estimates.csv", varnames(1) asdouble clear
keep if estimator == "aggregate_did"
assert _N == 1
local beta = estimate[1]
local beta_low = conf_low[1]
local beta_high = conf_high[1]
* CPI has no DKK/kg units. Use the grocery mean as an explicit level anchor.
import delimited "outputs/models/stata/micro_estimates.csv", varnames(1) asdouble clear
keep if estimator == "micro_did"
local price = pre_treated_average[1]
import delimited "outputs/models/stata/scc_meta_summary.csv", varnames(1) asdouble clear
local damage = mean[1]*6.8953*59.6/1000
local tax = tax_effective_2024_dkk[1]*59.6/1000
clear
set obs 10404
gen byte panel = ceil(_n/2601)
gen double x = mod(_n-1,51)/50
gen double y = floor(mod(_n-1,2601)/51)/50
gen double persistence = x
gen double taxable_share = panel/4
gen double incremental_pass_through = y
gen double beta = `beta'
gen double beta_low = `beta_low'
gen double beta_high = `beta_high'
gen double pre_price_dkk_kg = `price'
gen double damage_dkk_kg = `damage'
gen double announcement_dkk_kg = persistence*`price'*(exp(`beta')-1)
gen double implementation_dkk_kg = incremental_pass_through*taxable_share*`tax'
gen double remaining_gap_dkk_kg = damage_dkk_kg-announcement_dkk_kg-implementation_dkk_kg
* R decreases in beta. Reverse endpoints; no delta-method approximation.
gen double conf_low = damage_dkk_kg-persistence*`price'*(exp(`beta_high')-1)-implementation_dkk_kg
gen double conf_high = damage_dkk_kg-persistence*`price'*(exp(`beta_low')-1)-implementation_dkk_kg
assert conf_low <= remaining_gap_dkk_kg & remaining_gap_dkk_kg <= conf_high
assert conf_low == conf_high if persistence == 0
isid panel x y
export delimited "outputs/models/stata/calibration_surfaces.csv", replace
* Full factorial coarse grid for replication, including the interior a=f=lambda=.5.
clear
set obs 27
gen double persistence = floor((_n-1)/9)/2
gen double taxable_share = floor(mod(_n-1,9)/3)/2
gen double incremental_pass_through = mod(_n-1,3)/2
gen double damage_dkk_kg = `damage'
gen double announcement_dkk_kg = persistence*`price'*(exp(`beta')-1)
gen double implementation_dkk_kg = incremental_pass_through*taxable_share*`tax'
gen double remaining_gap_dkk_kg = damage_dkk_kg-announcement_dkk_kg-implementation_dkk_kg
gen double conf_low = damage_dkk_kg-persistence*`price'*(exp(`beta_high')-1)-implementation_dkk_kg
gen double conf_high = damage_dkk_kg-persistence*`price'*(exp(`beta_low')-1)-implementation_dkk_kg
export delimited "outputs/models/stata/calibration_scenarios.csv", replace
list if persistence == 1 & taxable_share == 1, noobs
log close
