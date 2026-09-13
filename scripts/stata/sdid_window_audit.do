version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/sdid_window_audit.log", text replace

* Prespecified candidate histories: 15 (published), 24, 36, and 54 months.
* Compare centered fit over the SAME April 2023--June 2024 months.
* Hold donor membership and outcome transformation fixed across windows.
* This diagnostic never overwrites publication estimates.
tempfile results source members
tempname handle
postfile `handle' str20 exercise int pre_months units treated_units ///
    double att rmse_recent rmse_full using `results', replace

foreach exercise in cpi hicp production_weight production_heads trade {
    if "`exercise'" == "cpi" {
        import delimited "data/processed/sdid_window_cpi.csv", asdouble clear
        rename month month_text
        gen month = monthly(month_text, "YM")
    }
    if "`exercise'" == "hicp" {
        import delimited "data/processed/sdid_window_hicp.csv", asdouble clear
        egen unit_id = group(geo)
        drop unit
        rename unit_id unit
        gen month = monthly(time, "YM")
        gen double outcome = ln(value)
        gen byte treated_unit = geo == "DK"
    }
    if inlist("`exercise'", "production_weight", "production_heads") {
        import delimited "data/processed/eurostat_bovine_slaughter.csv", clear
        local measure = cond("`exercise'" == "production_weight", "THS_T", "THS_HD")
        keep if freq == "M" & meatitem == "SLAUGHT" & meat == "B1000" & unit == "`measure'"
        keep if strpos(" AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK ", " " + geo + " ") > 0
        drop unit
        egen unit = group(geo)
        gen month = monthly(time, "YM")
        gen double outcome = ln(value)
        gen byte treated_unit = geo == "DK"
    }
    if "`exercise'" == "trade" {
        import delimited "data/processed/eu_beef_trade_pair_month_panel.csv", stringcols(_all) encoding("utf-8") clear
        keep pair_id
        assert strlen(pair_id) <= 244
        recast str244 pair_id, force
        duplicates drop
        save `members', replace
        import delimited "data/processed/sdid_window_trade.csv", stringcols(_all) encoding("utf-8") clear
        assert strlen(pair_id) <= 244
        recast str244 pair_id, force
        merge m:1 pair_id using `members', keep(3) assert(1 3) nogen
        destring carcase_weight_tonnes, replace dpcomma
        egen unit = group(pair_id)
        gen month_id = monthly(month, "YM")
        drop month
        rename month_id month
        gen double outcome = ln(1 + carcase_weight_tonnes)
        gen byte treated_unit = member_state == "Denmark"
    }
    keep unit month outcome treated_unit
    keep if inrange(month, tm(2020m1), tm(2025m9))
    isid unit month
    bysort unit: egen valid_main = total(inrange(month, tm(2023m4), tm(2025m9)) & !missing(outcome))
    keep if valid_main == 30
    * Fail rather than silently changing the donor pool for longer histories.
    bysort unit: egen valid_long = total(!missing(outcome))
    assert valid_long == 69
    gen byte treatment = treated_unit * (month >= tm(2024m7))
    save `source', replace
    foreach npre in 15 24 36 54 {
        use `source', clear
        local start = tm(2024m7) - `npre'
        keep if month >= `start'
        quietly levelsof unit, local(ids)
        local nu : word count `ids'
        quietly levelsof unit if treated_unit, local(ids)
        local nt : word count `ids'
        sdid outcome unit month treatment, vce(noinference)
        local att = e(ATT)
        matrix series = e(series)
        clear
        svmat double series
        rename series1 month
        rename series2 synthetic
        rename series3 treated
        gen double gap = treated - synthetic
        quietly summarize gap if month < tm(2024m7), meanonly
        gen double sq_full = (gap - r(mean))^2 if month < tm(2024m7)
        quietly summarize sq_full, meanonly
        local rmse_full = sqrt(r(mean))
        quietly summarize gap if inrange(month, tm(2023m4), tm(2024m6)), meanonly
        gen double sq_recent = (gap - r(mean))^2 if inrange(month, tm(2023m4), tm(2024m6))
        quietly summarize sq_recent, meanonly
        local rmse_recent = sqrt(r(mean))
        format month %tm
        export delimited "outputs/models/stata/sdid_window_`exercise'_`npre'_series.csv", replace
        post `handle' ("`exercise'") (`npre') (`nu') (`nt') (`att') (`rmse_recent') (`rmse_full')
    }
}
postclose `handle'
use `results', clear
bysort exercise (pre_months): gen double rmse_ratio = rmse_recent / rmse_recent[1]
gen byte fit_improves = rmse_ratio < 1 if pre_months > 15
export delimited "outputs/models/stata/sdid_window_audit.csv", replace
list, noobs
log close
