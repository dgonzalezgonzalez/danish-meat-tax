version 19.5
clear all
set more off
capture log close
log using "outputs/diagnostics/stata/production_descriptives.log", text replace
tempfile descriptives
tempname results
postfile `results' str12 sample str8 measure long observations double mean sd p25 median p75 using `descriptives', replace
foreach measure in THS_T THS_HD {
    import delimited "outputs/models/stata/production_`measure'_main_sample.csv", varnames(1) clear
    isid geo month
    assert _N == 810
    foreach sample in all denmark donors {
        local condition
        if "`sample'" == "denmark" local condition if geo == "DK"
        if "`sample'" == "donors" local condition if geo != "DK"
        quietly summarize value `condition', detail
        post `results' ("`sample'") ("`measure'") (r(N)) (r(mean)) (r(sd)) (r(p25)) (r(p50)) (r(p75))
    }
}
postclose `results'
use `descriptives', clear
export delimited "outputs/models/stata/production_descriptive_statistics.csv", replace
log close
