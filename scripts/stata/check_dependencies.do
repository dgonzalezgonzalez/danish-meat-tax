version 19.5

* The published estimates were produced with sdid 2.0.2. Refuse a silent
* substitution if SSC later serves a different implementation.
capture findfile sdid.ado
if _rc {
    display as error "Required Stata package sdid 2.0.2 is missing. Run scripts/install_stata_dependencies.do."
    exit 499
}

local sdid_path "`r(fn)'"
tempname sdid_file
file open `sdid_file' using "`sdid_path'", read text
file read `sdid_file' sdid_header
file read `sdid_file' sdid_header
file close `sdid_file'

if strpos("`sdid_header'", "Version 2.0.2") == 0 {
    display as error "Expected sdid 2.0.2; installed sdid.ado has a different version."
    exit 459
}
