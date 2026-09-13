version 19.5
clear all
set more off
args window_audit
local requested_window_audit "`window_audit'"

do "scripts/stata/microdata_analysis.do"
do "scripts/stata/aggregate_analysis.do"
do "scripts/stata/country_sdid.do"
do "scripts/stata/beef_trade_pair_sdid.do"
do "scripts/stata/beef_trade_pair_sdid_bootstrap.do"
do "scripts/stata/production_analysis.do"
do "scripts/stata/scc_meta_analysis.do"

* Optional diagnostic; prepare its separate histories as documented first.
if "`requested_window_audit'" == "audit" {
    do "scripts/stata/prepare_sdid_window_cpi.do"
    do "scripts/stata/sdid_window_audit.do"
    do "scripts/stata/verify_sdid_revision.do"
}
if "`requested_window_audit'" == "maxhistory" {
    do "scripts/stata/sdid_max_history_figures.do"
}
