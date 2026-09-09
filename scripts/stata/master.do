version 19.5
clear all
set more off

do "scripts/stata/microdata_analysis.do"
do "scripts/stata/aggregate_analysis.do"
do "scripts/stata/country_sdid.do"
do "scripts/stata/beef_trade_pair_sdid.do"
do "scripts/stata/beef_trade_pair_sdid_bootstrap.do"
do "scripts/stata/production_analysis.do"
do "scripts/stata/scc_meta_analysis.do"
