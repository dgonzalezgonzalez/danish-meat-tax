version 19.5
clear all
set more off
import delimited using "data/raw/statbank_pris01.csv", delimiter(";") varnames(1) stringcols(_all) encoding("utf-8") clear
rename *, lower

gen str12 product_code_raw = substr(varegr, 1, strpos(varegr, " ") - 1)
gen str8 product_code = subinstr(product_code_raw, ".", "", .)
gen strL product_name = substr(varegr, strpos(varegr, " ") + 1, .)
gen month = monthly(tid, "YM")
format month %tm
replace indhold = "" if indhold == ".."
destring indhold, replace dpcomma force
rename indhold cpi

* Retain terminal food and non-alcoholic beverage indices under COICOP 2018.
gen byte food_leaf = ///
    (strlen(product_code) == 5 & inlist(substr(product_code, 1, 3), "011", "012") & product_code != "01122") | ///
    (strlen(product_code) == 6 & substr(product_code, 1, 3) == "011")
keep if food_leaf

* Beef is treated. Policy-exposed or compositionally ambiguous livestock foods
* are excluded from the donor pool, including poultry and eggs.
gen byte beef = product_code == "011221"
gen byte excluded_livestock = inlist(product_code, "011222", "011223", "01123", "01124", "01125")
replace excluded_livestock = 1 if inlist(product_code, "01141", "01142", "01143", "01145", "01146", "01147", "01152")
replace excluded_livestock = 1 if inlist(product_code, "011224", "01144")
drop if excluded_livestock
drop if missing(cpi, month)

egen unit = group(product_code), label
gen double outcome = ln(cpi)
gen byte treated_unit = beef
keep unit month outcome treated_unit
export delimited "data/processed/sdid_window_cpi.csv", replace
