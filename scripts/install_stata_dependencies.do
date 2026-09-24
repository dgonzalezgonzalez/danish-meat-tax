clear all
set more off

capture which sdid
if _rc ssc install sdid, replace

do "scripts/stata/check_dependencies.do"
