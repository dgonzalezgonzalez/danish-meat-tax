# Methodology

## Research Question

Did the 2024-06-24 announcement of Denmark's livestock carbon tax change supermarket consumer prices for meat products?

## Identification

The main design is a two-way fixed effects difference-in-differences model on a balanced product-store panel:

```text
log(price_it) = beta * Treated_i * Post_t + product-store FE_i + period FE_t + error_it
```

The event-study model replaces the single post indicator with relative-time interactions for treated units, omitting period `-1` as the reference.

## Treatment Groups

The main treated groups are beef and pork. Lamb/sheep/goat products are coded as livestock-exposed because the policy is about livestock emissions, not only beef and pork retail products. Poultry is a sensitivity group. Fish, seafood, dairy, and non-meat foods are controls or robustness categories depending on the specification.

## Symmetric Window

The panel builder selects the largest symmetric pre/post window around 2024-06-24 supported by the observed data. The event period itself is excluded so the number of pre and post periods is equal.

By default, units are retained when they have at least one pre-announcement and one post-announcement observation inside that symmetric window. This keeps many more commodities and products from the large price-history source. A strict complete-unit panel is available with `--require-complete-units`, but it can drop nearly all real grocery products because historical price records are sparse rather than daily-complete.

## Inference

The included estimator residualizes outcomes and treatment variables by product-store and period fixed effects, then computes cluster-robust standard errors by `unit_id`. For final paper-grade inference, consider validating with `fixest` in R or `statsmodels`/`linearmodels` in Python when those dependencies are available.

## Limitations

- Estimates capture announcement effects, not statutory tax pass-through.
- Grocery price data coverage determines the feasible event window.
- Automated product classification can misclassify mixed products; ambiguous products should be reviewed in robustness checks.
- Food inflation and retailer pricing campaigns can still affect interpretation despite period fixed effects.
