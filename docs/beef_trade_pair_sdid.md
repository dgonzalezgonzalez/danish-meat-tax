# Beef-import pair SDiD robustness check

This check asks whether Denmark's livestock-tax announcement was followed by an increase in beef imports from external partner countries. The unit is an importer--partner pair. All pairs whose importer is Denmark are treated units; every other EU Member State--external-partner pair is a control unit.

## Source and construction

- Source page: European Commission, [Beef statistics](https://agriculture.ec.europa.eu/data-and-analysis/markets/overviews/market-observatories/meat/beef-statistics_en).
- Dashboard: [Beef trade](https://agridata.ec.europa.eu/extensions/DashboardBeef/BeefTrade.html).
- Download: the dashboard's Data Explorer bulk CSV, `data/raw/eu_beef_trade_data_en.csv`.
- The dashboard describes monthly EU beef imports and exports by Member State and external partner, sourced from Eurostat COMEXT under statistical regime 4. Intra-EU trade is excluded. The data are provided at CN8 product-code level in the Data Explorer.
- The April 2023--September 2025 window is aggregated across all product groups in the beef dashboard to monthly carcase-weight tonnes. Missing pair-months are explicit zero-import cells.
- The resulting balanced panel contains 383 importer--partner pairs (17 Denmark-importer treated pairs and 366 controls), 30 months, and 11,490 observations. There are 7,775 zero-import pair-months.

## Estimation

The outcome is `ln(1 + carcase_weight_tonnes)`, which retains zero-import months. Treatment begins in July 2024, matching the paper's first full post-announcement month. The Stata command is:

```stata
sdid ln_imports unit month_id treated_post, vce(placebo) reps(200) seed(20260828)
sdid ln_imports unit month_id treated_post, vce(bootstrap) reps(200) seed(20260828)
```

Run `scripts/prepare_beef_trade_pair_panel.ps1` to rebuild the panel and then run `scripts/stata/beef_trade_pair_sdid.do` and `scripts/stata/beef_trade_pair_sdid_bootstrap.do` in Stata 19.5. The graph is written to `outputs/figures/stata/beef_trade_pair_sdid.png`; estimates are written to the two corresponding CSV files in `outputs/models/stata/`.

The placebo estimate is -0.0801 with SE 0.1167 and normal-approximation p-value 0.4922. The bootstrap estimate is identical, with bootstrap SE 0.0782 and normal-approximation p-value 0.3058; its 95% interval is [-0.2335, 0.0732]. Both intervals include zero. Because the outcome is log-one-plus volume and the pair panel is sparse, the coefficient is not a direct percentage change in positive importers.
