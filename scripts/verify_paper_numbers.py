"""Check keyed manuscript table cells and current summaries against Stata CSVs."""
from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "outputs/models/stata"
PAPER = ROOT / "paper/main.tex"
README = ROOT / "README.md"


def read_rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def one(name: str, **keys: str) -> dict[str, str]:
    found = [row for row in read_rows(name) if all(row.get(k) == v for k, v in keys.items())]
    if len(found) != 1:
        raise AssertionError(f"Expected one row in {name} for {keys}; found {len(found)}")
    return found[0]


def table(tex: str, label: str) -> str:
    marker = rf"\label{{{label}}}"
    if tex.count(marker) != 1:
        raise AssertionError(f"Expected one table label {label}")
    return tex.split(marker, 1)[1].split(r"\end{table}", 1)[0]


def cells(line: str) -> list[str]:
    return [re.sub(r"\\\\.*$", "", part.strip()).strip() for part in line.split("&")]


def row(table_text: str, label: str, columns: int) -> list[str]:
    found = [cells(line) for line in table_text.splitlines() if line.strip().startswith(label + " &")]
    if len(found) != 1 or len(found[0]) != columns:
        raise AssertionError(f"Expected one {columns}-cell row {label!r}; found {found}")
    return found[0]


def expect_cells(actual: list[str], expected: list[str], context: str) -> None:
    if actual != expected:
        raise AssertionError(f"{context}: expected {expected}, found {actual}")


def formatted(value: str, decimals: int = 2) -> str:
    return f"{float(value):,.{decimals}f}"


def verify_main_table(tex: str) -> None:
    main = table(tex, "tab:main")
    lines = main.splitlines()
    number_lines = [line for line in lines if line.strip().startswith("& (1) &")]
    if len(number_lines) != 1:
        raise AssertionError("Table 2 needs one separate (1)--(4) number header")
    expect_cells(cells(number_lines[0]), ["", "(1)", "(2)", "(3)", "(4)"], "Table 2 numbers")
    header = next((line.split("&") for line in lines if "Grocery change" in line and "CPI DiD" in line), None)
    if header is None or len(header) != 5 or not all(
        term in header[index] for index, term in enumerate(("", "Grocery change", "CPI DiD", "CPI SDiD", "EU beef HICP"))
    ):
        raise AssertionError("Table 2 estimator names need a separate ordered header row")

    sources = (
        ("micro_estimates.csv", "micro_did"),
        ("aggregate_estimates.csv", "aggregate_did"),
        ("aggregate_estimates.csv", "aggregate_sdid"),
        ("country_sdid_estimate.csv", "country_sdid_HICP"),
    )
    estimates = [one(name, estimator=estimator) for name, estimator in sources]
    att_lines = [i for i, line in enumerate(lines) if line.strip().startswith("ATT (descriptive contrast) &")]
    if len(att_lines) != 1:
        raise AssertionError("Table 2 needs one ATT (descriptive contrast) row")
    index = att_lines[0]
    att, se = cells(lines[index]), cells(lines[index + 1])
    def stars(p_value: str) -> str:
        p = float(p_value)
        return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""

    expect_cells(att[1:],
                 [formatted(item["estimate"], 3) + stars(item["p_value"]) for item in estimates],
                 "Table 2 ATT columns and significance stars")
    expect_cells(se[1:], [f"({formatted(item['std_error'], 3)})" for item in estimates],
                 "Table 2 standard-error columns")
    expect_cells(row(main, "Regression observations", 5)[1:],
                 [f"{int(item['observations']):,}" for item in estimates], "Table 2 regression observations")
    expect_cells(row(main, "Underlying event/series--months", 5)[1:],
                 [f"{int(item.get('underlying_series_months') or item['observations']):,}" for item in estimates],
                 "Table 2 underlying observations")
    expect_cells(row(main, "Units", 5)[1:], [f"{int(item['units']):,}" for item in estimates], "Table 2 units")
    expect_cells(row(main, "Periods", 5)[1:], [str(int(item["periods"])) for item in estimates], "Table 2 periods")
    expect_cells(row(main, "Pre-treatment beef level/index", 5)[1:],
                 [formatted(item["pre_treated_average"]) for item in estimates], "Table 2 baseline means")
    expect_cells(row(main, "HAC maximum lag", 5)[1:], ["---", "2", "---", "---"], "Table 2 HAC lags")
    expect_cells(row(main, "Time window", 5)[1:],
                 [item["time_window"].replace("-", "--", 1) for item in estimates], "Table 2 windows")


def verify_descriptive_table(tex: str) -> None:
    descriptive = table(tex, "tab:descriptives")
    for sample in ("all", "beef", "controls"):
        for variable in ("Normalized price", "Months per product-store"):
            result = one("descriptive_statistics.csv", sample=sample, variable=variable)
            display_sample = "All" if sample == "all" else "Beef" if sample == "beef" else "Controls"
            display_variable = "Months per product--store" if variable.startswith("Months") else variable
            data = row(descriptive, f"{display_sample} & {display_variable}", 8)
            is_price = variable == "Normalized price"
            quantiles = [formatted(result[key]) if is_price else f"{float(result[key]):g}"
                         for key in ("p25", "median", "p75")]
            expected = [f"{int(result['observations']):,}", formatted(result["mean"]),
                        formatted(result["sd"]), *quantiles]
            expect_cells(data[2:], expected, f"Table 1 {sample} {variable}")


def verify_magnitude_table(tex: str) -> None:
    magnitude = table(tex, "tab:model_magnitude")
    expect_cells(row(magnitude, "Level-price scenario", 4),
                 ["Level-price scenario", "Anchor, DKK/kg", "Domestic CPI DiD", "Country beef HICP SDiD"],
                 "Table 3 estimator headings")
    for key, label in (
        ("illustrative_100", "Illustrative low level"),
        ("provisional_event_mean", "Provisional grocery event mean"),
        ("illustrative_200", "Illustrative high level"),
    ):
        result = one("model_magnitude_scenarios.csv", scenario=key)
        expect_cells(row(magnitude, label, 4)[1:],
                     [formatted(result[field]) for field in
                      ("anchor_dkk_kg", "national_cpi_dkk_kg", "country_hicp_dkk_kg")],
                     f"Table 3 {key}")


def verify_window_table(tex: str) -> None:
    """Bind every appendix sensitivity estimate and fit measure to its cell."""
    sensitivity = table(tex, "tab:window_sensitivity")
    expect_cells(row(sensitivity, "Pre-treatment months", 5),
                 ["Pre-treatment months", "15", "24", "36", "54"],
                 "Appendix window headings")
    panel_a, panel_b = sensitivity.split(r"\multicolumn{5}{l}{\textit{Panel B.", 1)
    sources = (
        ("Danish beef versus food CPI", "cpi"),
        ("Denmark versus EU beef HICP", "hicp"),
        ("Slaughter weight", "production_weight"),
        ("Slaughter heads", "production_heads"),
        ("Extra-EU bilateral imports", "trade"),
    )
    for label, exercise in sources:
        rows = [one("sdid_window_audit.csv", exercise=exercise, pre_months=str(months))
                for months in (15, 24, 36, 54)]
        for panel, field, name in ((panel_a, "att", "ATT"), (panel_b, "rmse_recent", "RMSE")):
            actual = [item.replace("$", "") for item in row(panel, label, 5)[1:]]
            expect_cells(actual, [formatted(result[field], 3) for result in rows],
                         f"Appendix window {name}: {label}")
    hicp = [one("sdid_window_audit.csv", exercise="hicp", pre_months=str(months))
            for months in (15, 24, 36, 54)]
    expect_cells(row(panel_b, "HICP RMSE / 15-month RMSE", 5)[1:],
                 [formatted(result["rmse_ratio"], 3) for result in hicp],
                 "Appendix HICP RMSE ratios")


def require_in(text: str, value: str, context: str) -> None:
    if value not in text:
        raise AssertionError(f"{context} missing {value}")


def main() -> None:
    tex = PAPER.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    four_place_results = re.findall(r"(?<![\d.])[-+]?\d+\.\d{4}(?!\d)", tex)
    if four_place_results:
        raise AssertionError(f"Manuscript still contains four-decimal results: {four_place_results}")
    verify_main_table(tex)
    verify_descriptive_table(tex)
    verify_magnitude_table(tex)
    verify_window_table(tex)
    results = tex.split(r"\section{Results}\label{sec:results}", 1)[1].split(r"\section{Discussion of the Results}", 1)[0]
    for key in ("2024m7-2024m12", "2025m1-2025m9"):
        country = one("country_sdid_timing.csv", period=key)
        require_in(results, formatted(country["gap_vs_weighted_pre"], 3), f"country timing {key}")
    weights = read_rows("country_sdid_time_weights.csv")
    require_in(results, f"{100 * float(weights[0]['may_june_weight']):.1f}", "May–June country time weight")
    require_in(results, f"{float(weights[0]['inverse_squared_weight_sum']):.2f}",
               "country time-weight concentration")
    unit_weights = read_rows("country_sdid_unit_weights.csv")
    require_in(results, f"{float(unit_weights[0]['effective_donors']):.1f}",
               "effective country donor count")
    require_in(results, formatted(read_rows("production_carcass_weight_estimate.csv")[0]["estimate"], 3),
               "direct carcass estimate")
    omitted = one("country_sdid_omit_june.csv", specification="country_hicp_omit_june_2024")
    require_in(results, formatted(omitted["estimate"], 3), "country June omission")
    price = one("price_benchmark_summary.csv", block_months="2")
    calibration = tex.split(r"\section{Conditional Environmental-Price Accounting}\label{sec:calibration}", 1)[1]
    for field in ("point", "low", "high"):
        require_in(calibration, formatted(price[field]), f"grocery anchor {field}")
    scc = read_rows("scc_meta_summary.csv")[0]
    require_in(calibration, formatted(scc["mean"]), "selected SCC mean")
    for field in ("log_price_gap_effective_120", "log_price_gap_marginal_300"):
        require_in(calibration, formatted(scc[field], 3), f"SCC {field}")
    scenario = one("calibration_scenarios.csv", persistence="1", taxable_share="1", incremental_pass_through="1")
    for field in ("announcement_dkk_kg", "remaining_gap_dkk_kg"):
        require_in(calibration, formatted(scenario[field]), f"full scenario {field}")
    require_in(readme, "Before the Levy: Beef Prices During Denmark's Cattle-Policy Transition", "README title")
    require_in(readme, "Revision:** 30 September 2026", "README revision")
    grocery = one("micro_estimates.csv", estimator="micro_did")
    require_in(readme, f"Grocery change-event DiD is {formatted(grocery['estimate'], 3)} "
                       f"(SE {formatted(grocery['std_error'], 3)})", "README grocery summary")
    if "0.0278 (SE 0.0144)" in readme:
        raise AssertionError("README contains stale grocery coefficient")
    print("Key manuscript table cells and current summaries match Stata CSVs.")


if __name__ == "__main__":
    main()
