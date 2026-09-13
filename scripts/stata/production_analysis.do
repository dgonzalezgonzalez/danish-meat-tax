version 19.5
clear all
set more off
set seed 20260909
capture log close
log using "outputs/diagnostics/stata/production_analysis.log", text replace

* Same bovine product in other EU countries: no other Danish livestock donors.
import delimited "data/processed/eurostat_bovine_slaughter.csv", varnames(1) clear
keep if freq == "M" & meatitem == "SLAUGHT" & meat == "B1000"
gen byte eu27 = strpos(" AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK ", " " + geo + " ") > 0
keep if eu27
gen month = monthly(time, "YM")
format month %tm
rename unit measure
egen unit = group(geo), label
gen byte denmark = geo == "DK"
gen byte treatment = denmark * (month >= tm(2024m7))
destring value, replace
tempfile source estimates
save `source'
tempname results
postfile `results' str24 specification str8 measure double att se low high p_value pre_rmse ///
    long observations units pre_months post_months using `estimates', replace

foreach measure in THS_T THS_HD {
    foreach window in main long_pre omit_june {
        use `source', clear
        keep if measure == "`measure'"
        local start = cond("`window'" == "long_pre", tm(2020m1), tm(2023m4))
        keep if inrange(month, `start', tm(2025m9))
        if "`window'" == "omit_june" drop if month == tm(2024m6)
        local npre = cond("`window'" == "long_pre", 54, cond("`window'" == "omit_june", 14, 15))
        * Missing or zero production is not imputed. Membership uses coverage only.
        bysort unit: egen nvalid = total(value > 0 & value < .)
        keep if nvalid == `npre' + 15
        isid unit month
        assert value > 0 & value < .
        quietly count if denmark
        assert r(N) == `npre' + 15
        gen double ln_output = ln(value)
        * Remove country-specific seasonality estimated strictly before treatment.
        * Main and June-omission specifications use raw log levels for comparability.
        if "`window'" == "long_pre" {
            gen calendar_month = month(dofm(month))
            bysort unit: egen pre_mean = mean(cond(month < tm(2024m7), ln_output, .))
            bysort unit calendar_month: egen season_mean = mean(cond(month < tm(2024m7), ln_output, .))
            replace ln_output = ln_output - season_mean + pre_mean
        }
        quietly count
        local n = r(N)
        quietly levelsof unit, local(units)
        local nu : word count `units'
        egen t = group(month)
        sdid ln_output unit t treatment, vce(placebo) reps(200) seed(20260909)
        local att = e(ATT)
        local se = e(se)
        local lo = e(ATT_l)
        local hi = e(ATT_r)
        matrix series = e(series)
        export delimited geo month measure value flag using "outputs/models/stata/production_`measure'_`window'_sample.csv", replace
        clear
        svmat double series
        rename series1 t
        rename series2 synthetic
        rename series3 treated
        gen month = `start' + t - 1
        if "`window'" == "omit_june" replace month = month + 1 if t > 14
        format month %tm
        gen double gap = treated - synthetic
        quietly summarize gap if t <= `npre', meanonly
        gen double synthetic_aligned = synthetic + r(mean)
        gen double centered_gap_sq = (gap - r(mean))^2 if t <= `npre'
        quietly summarize centered_gap_sq, meanonly
        local rmse = sqrt(r(mean))
        post `results' ("`window'") ("`measure'") (`att') (`se') (`lo') (`hi') ///
            (2*normal(-abs(`att'/`se'))) (`rmse') (`n') (`nu') (`npre') (15)
        export delimited using "outputs/models/stata/production_`measure'_`window'_series.csv", replace
        if "`window'" == "main" & "`measure'" == "THS_T" {
            twoway (line treated month, lcolor(black)) (line synthetic_aligned month, lcolor(gs7) lpattern(dash)), ///
                xline(774, lpattern(shortdash) lcolor(gs9)) ///
                legend(order(1 "Denmark" 2 "Weighted donors") rows(1) position(6)) ///
                xtitle("") ytitle("Log bovine slaughter output (1,000 tonnes)") ///
                graphregion(color(white)) plotregion(color(white))
            graph export "outputs/figures/stata/production_sdid.png", width(2200) replace
        }
    }
}
postclose `results'
use `estimates', clear
export delimited using "outputs/models/stata/production_estimates.csv", replace
list, noobs
* National source: production includes the slaughter-equivalent contribution
* of live trade. Preserve its definition separately from Eurostat slaughterhouses.
import delimited "data/raw/statbank_ani41.csv", delimiter(";") varnames(1) stringcols(_all) clear
keep if dyrkat == "Cattle, total" & enhed == "Production (m kg)"
gen month = monthly(tid, "YM")
format month %tm
destring indhold, replace
rename indhold production_million_kg
keep if inrange(month, tm(2020m1), tm(2025m9))
isid month
tsset month
gen double yoy_percent = 100 * (production_million_kg / L12.production_million_kg - 1)
export delimited "outputs/models/stata/denmark_cattle_production.csv", replace
log close

do "scripts/stata/production_descriptives.do"
