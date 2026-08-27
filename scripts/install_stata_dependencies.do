clear all
set more off

capture which synth
if _rc ssc install synth, replace

capture which sdid
if _rc ssc install sdid, replace

capture which esttab
if _rc ssc install estout, replace
