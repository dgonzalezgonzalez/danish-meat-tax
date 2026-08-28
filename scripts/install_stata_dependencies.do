clear all
set more off

capture which sdid
if _rc ssc install sdid, replace

capture which esttab
if _rc ssc install estout, replace
