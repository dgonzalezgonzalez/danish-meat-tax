version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/country_sdid_diagnostics.log", text replace

* The exact 27-country publication sample, with no imputation or donor changes.
import delimited "outputs/models/stata/country_hicp_estimation_sample.csv", varnames(1) clear
gen month_id_numeric = monthly(month, "YM")
format month_id_numeric %tm
egen unit_numeric = group(geo)
isid geo month_id_numeric
assert _N == 810
tempfile panel donor_names
save `panel'
preserve
bysort unit_numeric: keep if _n == 1
keep if geo != "DK"
keep unit_numeric geo country
save `donor_names'
restore

sdid ln_price unit_numeric month_id_numeric treated_post, vce(noinference)
local baseline_att = e(ATT)
matrix unit_weights = e(omega)
matrix time_weights = e(lambda)

preserve
clear
svmat double unit_weights
rename unit_weights1 weight
rename unit_weights2 unit_numeric
drop if missing(unit_numeric)
merge 1:1 unit_numeric using `donor_names', assert(match) nogen
assert weight >= 0 & weight < .
egen double total_weight = total(weight)
assert abs(total_weight-1) < 1e-7
gen double squared_weight = weight^2
egen double concentration_hhi = total(squared_weight)
gen double effective_donors = 1/concentration_hhi
gsort -weight geo
export delimited "outputs/models/stata/country_sdid_unit_weights.csv", replace
restore

preserve
clear
svmat double time_weights
rename time_weights1 weight
rename time_weights2 month_id_numeric
keep if weight < . & month_id_numeric < .
assert _N == 15
format month_id_numeric %tm
egen double total_weight = total(weight)
assert abs(total_weight-1) < 1e-7
sort month_id_numeric
export delimited "outputs/models/stata/country_sdid_time_weights.csv", replace
restore

* Leave out each donor in turn. These are point sensitivities without new SEs.
tempname loo_post
tempfile loo_results
postfile `loo_post' str2 omitted_geo double att difference_from_full using `loo_results', replace
levelsof geo if geo != "DK", local(donors)
foreach donor of local donors {
    preserve
    drop if geo == "`donor'"
    egen unit_loo = group(geo)
    sdid ln_price unit_loo month_id_numeric treated_post, vce(noinference)
    post `loo_post' ("`donor'") (e(ATT)) (e(ATT)-`baseline_att')
    restore
}
postclose `loo_post'
use `loo_results', clear
gen double full_att = `baseline_att'
export delimited "outputs/models/stata/country_sdid_leave_one_out.csv", replace

* Two descriptive holdouts: one wholly before the 2024 policy news, and one
* immediately before the July treatment cutoff (the latter already contains
* expert-tax and nitrate news and is not a clean no-news placebo).
use `panel', clear
keep if month_id_numeric <= tm(2023m12)
gen byte holdout = geo == "DK" & month_id_numeric >= tm(2023m10)
sdid ln_price unit_numeric month_id_numeric holdout, vce(noinference)
local early_gap = e(ATT)
use `panel', clear
keep if month_id_numeric <= tm(2024m6)
gen byte holdout = geo == "DK" & month_id_numeric >= tm(2024m4)
sdid ln_price unit_numeric month_id_numeric holdout, vce(noinference)
local late_gap = e(ATT)
clear
set obs 2
gen str12 design = "pre_news" in 1
replace design = "pre_july" in 2
gen str18 train = "2023m4-2023m9" in 1
replace train = "2023m4-2024m3" in 2
gen str18 holdout = "2023m10-2023m12" in 1
replace holdout = "2024m4-2024m6" in 2
gen double pseudo_att = `early_gap' in 1
replace pseudo_att = `late_gap' in 2
gen double full_att = `baseline_att'
export delimited "outputs/models/stata/country_sdid_pre_holdout.csv", replace

* June contains the 24 June announcement but is pre in the monthly design.
* Re-estimate with that month removed and a contiguous Stata time index.
use `panel', clear
drop if month_id_numeric == tm(2024m6)
egen t_omit_june = group(month_id_numeric)
sdid ln_price unit_numeric t_omit_june treated_post, vce(placebo) reps(200) seed(20260827)
local omitted_att = e(ATT)
local omitted_se = e(se)
local omitted_low = e(ATT_l)
local omitted_high = e(ATT_r)
clear
set obs 1
gen str28 specification = "country_hicp_omit_june_2024"
gen double estimate = `omitted_att'
gen double std_error = `omitted_se'
gen double conf_low = `omitted_low'
gen double conf_high = `omitted_high'
gen long observations = 783
gen int pre_months = 14
gen int post_months = 15
export delimited "outputs/models/stata/country_sdid_omit_june.csv", replace
log close
