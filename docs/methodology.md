# Methodology

## Research Question

Did the 2024-06-24 announcement of Denmark's livestock carbon tax change supermarket consumer prices for meat products?

## Identification

The main design is a two-way fixed effects difference-in-differences model on a commodity-store panel of identified food items:

```text
log(normalized_price_it) = beta * Treated_i * Post_t + commodity-store FE_i + period FE_t + error_it
```

The event-study model replaces the single post indicator with relative-time interactions for treated units, omitting period `-1` as the reference.

## Treatment Groups

The treated groups are products derived from livestock covered by the policy channel:

- Beef/veal.
- Pork.
- Lamb/sheep/goat.
- Dairy, coded separately as `dairy_cattle` because dairy-cattle emissions are covered by the livestock-emissions policy channel even though retail dairy is not meat.

Food controls are identified non-treated food categories: poultry, fish/seafood, eggs, fruit/vegetables, grains/bread, fats/oils, sweets/snacks, beverages, and plant proteins. `unknown` and non-food products are excluded from the main econometric sample.

## Price Normalization

The source package price is preserved, but the model outcome uses normalized prices. Grams and kilograms convert to DKK/kg; milliliters, centiliters, and liters convert to DKK/liter. Rows without parseable physical units are excluded from the main panel and counted in diagnostics.

## Event Window

The default panel keeps all available pre/post periods after filters, allowing more post periods than pre periods when the data support it. The default unit level is `commodity_store`, meaning each commodity within each supermarket chain. `product_store` and all-store `commodity` panels are available as robustness options. Units are retained when they satisfy minimum pre/post observation support. The older equal-period design is available with `--symmetric-window`, and a strict complete-unit panel is available with `--require-complete-units`.

The event period itself is excluded from pre/post support. For weekly panels, periods are calendar weeks beginning Monday; the event week begins on 2024-06-24.

## Parallel Trends

The output stage produces event-study plots, aggregate normalized-price trend plots, period-support diagnostics, and `pretrend_summary.csv`. Pre-period coefficients should be inspected before interpreting ATE estimates. If pretrends remain poor, the next robustness steps are to restrict to stable stores/commodities, validate against official food price indices, and consider matched food controls.

## Inference

The included estimator residualizes outcomes and treatment variables by product-store and period fixed effects, then computes cluster-robust standard errors by `unit_id`. For final paper-grade inference, consider validating with `fixest` in R or `statsmodels`/`linearmodels` in Python when those dependencies are available.

## Limitations

- Estimates capture announcement effects, not statutory tax pass-through.
- Grocery price data coverage determines the feasible event window.
- Automated product classification can misclassify mixed products; ambiguous products should be reviewed in robustness checks.
- Food inflation and retailer pricing campaigns can still affect interpretation despite period fixed effects.
