version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/grocery_history_audit.log", text replace

* Source records are change events. Missing intervening months may represent
* unchanged prices, exits or collection failures; none is imputed here.
use "data/processed/commodity_panel_stata.dta", clear
keep unit_id period treatment_group treated commodity
gen byte beef = treatment_group == "beef"
capture confirm string variable treated
if !_rc gen byte control = lower(treated) == "false"
else gen byte control = treated == 0
replace control = 0 if inlist(commodity, "poultry", "eggs")
keep if beef | control
capture confirm string variable period
if !_rc gen month = mofd(date(period, "YMD"))
else gen month = mofd(period)
keep if inrange(month, tm(2023m10), tm(2025m9)) & month != tm(2024m6)
egen unit = group(unit_id)
bysort unit: egen pre_months = total(month < tm(2024m6))
bysort unit: egen post_months = total(month >= tm(2024m7))
keep if pre_months >= 1 & post_months >= 1
bysort unit: egen first_month = min(month)
bysort unit: egen last_month = max(month)
bysort unit: gen observed_months = _N
bysort unit: keep if _n == 1
gen int possible_months = last_month - first_month + 1 - ///
    (first_month <= tm(2024m6) & last_month >= tm(2024m6))
gen int unrecorded_months = possible_months - observed_months
assert unrecorded_months >= 0
gen str12 sample = cond(beef, "beef", "controls")
collapse (count) units=unit (sum) observed_months possible_months unrecorded_months, by(sample)
gen double recorded_share_within_span = observed_months/possible_months
export delimited "outputs/models/stata/grocery_event_support.csv", replace
list, noobs
log close
