version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/verify_sdid_revision.log", text replace

foreach file in aggregate_sdid country_sdid beef_trade_pair_sdid production_THS_T_main {
    import delimited "outputs/models/stata/`file'_series.csv", asdouble clear
    capture rename month_id month
    rename month month_text
    gen month = monthly(month_text, "YM")
    gen double adjustment = synthetic_aligned - synthetic
    quietly summarize adjustment
    assert r(max) - r(min) < 1e-10
    gen double pre_gap = treated - synthetic_aligned if month < tm(2024m7)
    quietly summarize pre_gap, meanonly
    assert abs(r(mean)) < 1e-10
}

* Report fit outcome by outcome. No cross-outcome veto or selection rule.
import delimited "outputs/models/stata/sdid_window_audit.csv", asdouble clear
isid exercise pre_months
assert _N == 20
bysort exercise: assert units == units[1] & treated_units == treated_units[1]
preserve
keep if pre_months > 15
keep exercise pre_months rmse_recent rmse_ratio fit_improves
sort exercise pre_months
export delimited "outputs/models/stata/sdid_window_decision.csv", replace
restore
list exercise pre_months att rmse_recent rmse_ratio, noobs sepby(exercise)
log close
