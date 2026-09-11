version 19.5
clear all
set more off
set seed 20260911
capture mkdir "outputs/models/stata"
capture mkdir "outputs/diagnostics/stata"
capture log close
log using "outputs/diagnostics/stata/price_benchmark_analysis.log", text replace
* Match the pre-announcement arithmetic mean used by microdata_analysis.do.
use "data/processed/commodity_panel_stata.dta", clear
keep if treatment_group == "beef" & relative_time < 0
assert price > 0 & price < .
egen long u = group(unit_id)
egen int t = group(period)
isid u t
quietly summarize price, meanonly
local point = r(mean)
local n = r(N)
quietly summarize u, meanonly
local nu = r(max)
quietly summarize t, meanonly
local nt = r(max)
assert `nt' == 8
* Crossed resampling: complete unit histories and common circular month blocks.
* Missing cells contribute neither price nor observation weight.
mata:
real colvector benchmark_draws(real matrix A, real matrix N, real scalar L, real scalar B) {
    real scalar b, j, k, start, U, T
    real colvector result, units, months
    real rowvector totals, counts
    U=rows(A); T=cols(A)
    result=J(B,1,.)
    for (b=1; b<=B; b++) {
        units=1:+floor(U:*runiform(U,1))
        totals=colsum(A[units,.]); counts=colsum(N[units,.])
        months=J(T,1,.)
        k=1
        while (k<=T) {
            start=floor(T*runiform(1,1))
            for (j=0; j<L & k<=T; j++) {
                months[k]=1+mod(start+j,T)
                k++
            }
        }
        result[b]=sum(totals[months])/sum(counts[months])
    }
    return(result)
}
D=st_data(.,("u","t","price"))
A=J(max(D[,1]),max(D[,2]),0); N=A
for (i=1; i<=rows(D); i++) {
    A[D[i,1],D[i,2]]=D[i,3]
    N[D[i,1],D[i,2]]=1
}
assert(abs(sum(A)/sum(N)-strtoreal(st_local("point")))<1e-8)
P2=benchmark_draws(A,N,2,10000)
P1=benchmark_draws(A,N,1,10000)
P4=benchmark_draws(A,N,4,10000)
end
clear
set obs 10000
gen long draw = _n
gen double price_draw = .
gen double price_block1 = .
gen double price_block4 = .
mata: st_store(.,"price_draw",P2); st_store(.,"price_block1",P1); st_store(.,"price_block4",P4)
assert price_draw > 0 & price_draw < .
assert price_block1 > 0 & price_block1 < .
assert price_block4 > 0 & price_block4 < .
export delimited "outputs/models/stata/price_benchmark_draws.csv", replace
tempfile summaries
tempname result
postfile `result' byte block_months double point double low double high double sd ///
    long observations long units int months using `summaries', replace
foreach L in 1 2 4 {
    local v = cond(`L'==2,"price_draw","price_block`L'")
    quietly summarize `v'
    local sd = r(sd)
    quietly centile `v', centile(2.5 97.5)
    post `result' (`L') (`point') (r(c_1)) (r(c_2)) (`sd') (`n') (`nu') (`nt')
}
postclose `result'
use `summaries', clear
export delimited "outputs/models/stata/price_benchmark_summary.csv", replace
list, noobs
log close
