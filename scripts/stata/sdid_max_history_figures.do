version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/sdid_max_history_figures.log", text replace
tempfile members source estimates
tempname handle
postfile `handle' str12 figure str20 exercise int start_month pre_months units ///
    double att rmse_full rmse_recent using `estimates', replace

foreach exercise in production hicp trade {
    if "`exercise'" == "production" {
        import delimited "data/processed/sdid_max_production.csv", encoding("utf-8") clear
        keep if freq == "M" & meatitem == "SLAUGHT" & meat == "B1000" & unit == "THS_T"
        drop unit
        egen unit = group(geo)
        gen month = monthly(time, "YM")
        gen double outcome = ln(value)
        gen byte treated_unit = geo == "DK"
        gen str80 unit_key = geo
        local label "B1"
        local title "Bovine slaughter weight"
        local ytitle "Log bovine slaughter output (1,000 tonnes)"
    }
    if "`exercise'" == "hicp" {
        import delimited "data/processed/sdid_max_hicp.csv", asdouble encoding("utf-8") clear
        assert freq == "M" & unit == "I15" & coicop == "CP01121"
        drop unit
        egen unit = group(geo)
        gen month = monthly(time, "YM")
        gen double outcome = ln(value)
        gen byte treated_unit = geo == "DK"
        gen str80 unit_key = geo
        local label "B3"
        local title "Beef and veal HICP"
        local ytitle "Log consumer price index"
    }
    if "`exercise'" == "trade" {
        import delimited "data/processed/eu_beef_trade_pair_month_panel.csv", stringcols(_all) encoding("utf-8") clear
        keep pair_id
        assert strlen(pair_id) <= 244
        recast str244 pair_id, force
        duplicates drop
        save `members', replace
        import delimited "data/processed/sdid_max_trade.csv", stringcols(_all) encoding("utf-8") clear
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
        gen str80 unit_key = pair_id
        gen str1 flag = ""
        local label "B4"
        local title "Extra-EU beef imports"
        local ytitle "Log(1 + beef imports, carcase-weight tonnes)"
    }
    keep unit unit_key month outcome treated_unit flag
    keep if month <= tm(2025m9)
    isid unit month
    quietly levelsof unit, local(ids)
    local nu : word count `ids'
    assert `nu' == cond("`exercise'" == "trade", 383, 27)
    * Maximum continuous, complete, positive history with all original donors.
    bysort unit: egen first_valid = min(cond(!missing(outcome), month, .))
    bysort unit: egen last_missing = max(cond(missing(outcome), month, .))
    quietly summarize first_valid, meanonly
    local start = r(max)
    quietly summarize month if missing(outcome) & month >= `start', meanonly
    if r(N) > 0 local start = r(max) + 1
    assert `start' < tm(2023m4)
    preserve
    bysort unit: keep if _n == 1
    keep unit unit_key first_valid last_missing
    format first_valid last_missing %tm
    export delimited "outputs/models/stata/sdid_max_`exercise'_coverage.csv", replace
    restore
    keep if month >= `start'
    assert !missing(outcome)
    bysort unit: assert _N == tm(2025m9) - `start' + 1
    local npre = tm(2024m7) - `start'
    gen byte treatment = treated_unit * (month >= tm(2024m7))
    format month %tm
    export delimited "outputs/models/stata/sdid_max_`exercise'_sample.csv", replace
    * Author-review paths and point estimates; no inference requested for preview.
    sdid outcome unit month treatment, vce(noinference)
    local att = e(ATT)
    matrix series = e(series)
    clear
    svmat double series
    rename series1 month
    rename series2 synthetic
    rename series3 treated
    format month %tm
    gen double gap = treated - synthetic
    quietly summarize gap if month < tm(2024m7), meanonly
    gen double synthetic_aligned = synthetic + r(mean)
    gen double sq_full = (gap - r(mean))^2 if month < tm(2024m7)
    quietly summarize sq_full, meanonly
    local full = sqrt(r(mean))
    quietly summarize gap if inrange(month, tm(2023m4), tm(2024m6)), meanonly
    gen double sq_recent = (gap - r(mean))^2 if inrange(month, tm(2023m4), tm(2024m6))
    quietly summarize sq_recent, meanonly
    local recent = sqrt(r(mean))
    export delimited "outputs/models/stata/sdid_max_`exercise'_series.csv", replace
    post `handle' ("`label'") ("`exercise'") (`start') (`npre') (`nu') (`att') (`full') (`recent')
    foreach view in full recent {
        local condition ""
        if "`view'" == "recent" local condition "if month >= tm(2023m4)"
        local subtitle = cond("`view'" == "full", "Full estimation history", "Zoom: April 2023 onward (same weights)")
        twoway (line treated month `condition', lcolor(black) lwidth(medthick)) ///
            (line synthetic_aligned month `condition', lcolor(gs7) lpattern(dash) lwidth(medthick)), ///
            xline(774, lpattern(shortdash) lcolor(gs9)) ///
            legend(order(1 "Denmark" 2 "Weighted donors") rows(1) position(6) size(small)) ///
            xtitle("") ytitle("`ytitle'", size(small)) title("`subtitle'", size(medsmall)) ///
            xlabel(, labsize(small)) ylabel(, labsize(small)) ///
            graphregion(color(white)) plotregion(color(white)) name(`view', replace)
    }
    local start_text : display %tm `start'
    graph combine full recent, cols(2) ycommon xsize(14) ysize(5) ///
        title("`label': `title'", size(medium)) ///
        subtitle("`start_text'-2025m9 | `npre' pre-treatment months | `nu' units", size(small)) ///
        note("Review preview. Donor path shifted to match the full pre-treatment mean. Vertical line: July 2024.", size(vsmall)) ///
        graphregion(color(white))
    graph export "outputs/figures/stata/sdid_max_`label'.png", width(2800) replace
}
postclose `handle'
use `estimates', clear
format start_month %tm
gen double baseline_recent = .
forvalues row = 1/3 {
    local exercise = exercise[`row']
    local file = cond("`exercise'" == "production", "production_THS_T_main", cond("`exercise'" == "hicp", "country_sdid", "beef_trade_pair_sdid"))
    preserve
    import delimited "outputs/models/stata/`file'_series.csv", asdouble clear
    capture rename month_id month
    gen m = monthly(month, "YM")
    keep if inrange(m, tm(2023m4), tm(2024m6))
    gen double base_gap = treated - synthetic
    quietly summarize base_gap, meanonly
    gen double base_sq = (base_gap - r(mean))^2
    quietly summarize base_sq, meanonly
    local base = sqrt(r(mean))
    restore
    replace baseline_recent = `base' in `row'
}
gen double rmse_ratio = rmse_recent / baseline_recent
export delimited "outputs/models/stata/sdid_max_history_summary.csv", replace
list, noobs
log close
