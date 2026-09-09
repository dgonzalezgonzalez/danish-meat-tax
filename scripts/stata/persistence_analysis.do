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
local beta_se = std_error[1]
* The preferred newey regression has 30 monthly gaps and two coefficients.
local beta_df = periods[1]-2
assert `beta_df' == 28
local beta_low = conf_low[1]
local beta_high = conf_high[1]
* CPI has no DKK/kg units. Use the grocery mean as an explicit level anchor.
import delimited "outputs/models/stata/micro_estimates.csv", varnames(1) asdouble clear
keep if estimator == "micro_did"
local price = pre_treated_average[1]
import delimited "outputs/models/stata/scc_meta_summary.csv", varnames(1) asdouble clear
local damage = mean[1]*6.8953*59.6/1000
local tax = tax_effective_2024_dkk[1]*59.6/1000
* Combine the original SCC hierarchical draws with independent coefficient draws.
* Student t(28) matches the finite-df HAC interval used in the preferred model.
import delimited "outputs/models/stata/scc_meta_draws.csv", varnames(1) asdouble clear
assert _N == 10000
set seed 20260910
gen long draw = _n
gen double beta_draw = `beta' + `beta_se'*rt(`beta_df')
gen double damage_draw = pooled_mean*6.8953*59.6/1000
gen double announcement_draw = `price'*(exp(beta_draw)-1)
export delimited "outputs/models/stata/calibration_joint_draws.csv", replace
tempfile bounds
tempname bounds_post
postfile `bounds_post' int a_index double sensitivity_low double sensitivity_high using `bounds', replace
forvalues k = 0/50 {
    gen double r_draw = damage_draw-(`k'/50)*announcement_draw
    quietly centile r_draw, centile(2.5 97.5)
    post `bounds_post' (`k') (r(c_1)) (r(c_2))
    drop r_draw
}
postclose `bounds_post'
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
gen int a_index = round(persistence*50)
merge m:1 a_index using `bounds', assert(match) nogen
replace sensitivity_low = sensitivity_low-implementation_dkk_kg
replace sensitivity_high = sensitivity_high-implementation_dkk_kg
assert sensitivity_high > sensitivity_low
drop a_index
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
gen int a_index = round(persistence*50)
merge m:1 a_index using `bounds', keep(master match) assert(match using) nogen
replace sensitivity_low = sensitivity_low-implementation_dkk_kg
replace sensitivity_high = sensitivity_high-implementation_dkk_kg
drop a_index
export delimited "outputs/models/stata/calibration_scenarios.csv", replace
list if persistence == 1 & taxable_share == 1, noobs
log close
