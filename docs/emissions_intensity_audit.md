# Emissions-intensity uncertainty audit

Checked 11 September 2026. The calibration retains the OECD-presented 59.6 kg CO2e/kg beef-herd lifecycle benchmark. This is not a direct estimate of Danish taxable farm emissions: Figure 4 applies an assumed taxable fraction f. Neither intensity nor f receives a stochastic distribution in the present calculations.

## Sources inspected

1. [OECD (2025), Chapter 2](https://www.oecd.org/en/publications/measuring-carbon-footprints-of-agri-food-products_8eb75706-en/full-report/background-four-findings-about-ghg-emissions-in-food-systems_afc47f82.html), Figures 2.2 and 2.3. Figure 2.2 presents average footprints. Figure 2.3 describes heterogeneity across producers, showing medians and the 10th–90th percentile span, in kg CO2e per 100 g protein. It does not report confidence limits for the 59.6 kg/kg benchmark.
2. [Poore and Nemecek (2018), supplementary materials](https://josephpoore.com/data/science2018/Science%20360%206392%20987%20-%20SUPPLEMENTARY%20MATERIALS.pdf), together with the author's [Data S2 workbook](https://josephpoore.com/data/science2018/Data%20S2.xls). The workbook reports means, medians, and 5th/10th/90th/95th percentiles of resampled/randomized producer footprints, and original-study minima/maxima. It does not provide a standard error or confidence interval for the specific OECD benchmark.

The distinction is material. In Data S2, sheet `Results - Retail Weight`, Excel row 37 (`Bovine Meat (beef herd)`), IPCC 2013 including carbon-cycle feedbacks gives a mean of 99.48 and producer 10th/90th percentiles of 40.37/209.85 kg CO2e/kg. The IPCC 2007 block gives a mean of 85.19 and percentiles of 33.03/179.95. These are differently defined distributional summaries, not a matched uncertainty interval around 59.6. The `Results - Nutritional Units` sheet changes the functional unit again. The word “resampled” in the header does not turn the reported producer percentiles into percentiles of an estimated mean.

Consequently, drawing intensity from one of these producer distributions would change the target of the calibration and require additional choices about Danish production weights, lifecycle boundaries, and greenhouse-gas characterization. Dividing their spread by a square root of the number of farms would also impose an unsupported independent-sampling design. No such conversion is made. This finding does not imply that the intensity is known without error; Figures 2–4 remain conditional on the selected lifecycle benchmark and do not quantify uncertainty in Danish taxable intensity.

## Audit fingerprints

The downloaded files were inspected as source documentation, not added as computational inputs. Existing replication input hashes are unchanged.

| Source file | SHA-256 |
|---|---|
| Data S2.xls | `2fac998ebe2560233e214651c3c52b30603ad9ac3bc9c14a342be038343a594b` |
| Science 360 6392 987 - SUPPLEMENTARY MATERIALS.pdf | `241e4ed155a644eebe4e99bafb1ae4d63e7b80abcaeda1e53271ab76f49fe1c3` |
