"""Check presentation-rounded manuscript claims against Stata CSV outputs.

This is a transcription check, not analytical computation. Run after Stata
master.do and before committing a revised paper.
"""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "outputs/models/stata"
PAPER = ROOT / "paper/main.tex"


def read_rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def one(name: str, **keys: str) -> dict[str, str]:
    found = [row for row in read_rows(name) if all(row.get(k) == v for k, v in keys.items())]
    if len(found) != 1:
        raise AssertionError(f"Expected one row in {name} for {keys}; found {len(found)}")
    return found[0]


def check(text: str, value: str, where: str) -> None:
    if value not in text:
        raise AssertionError(f"Manuscript {where} missing {value}")


def main() -> None:
    tex = PAPER.read_text(encoding="utf-8")
    main_table = tex.split(r"\label{tab:main}", 1)[1].split(r"\end{table}", 1)[0]
    descriptive_table = tex.split(r"\label{tab:descriptives}", 1)[1].split(r"\end{table}", 1)[0]

    for sample in ("all", "beef", "controls"):
        row = one("descriptive_statistics.csv", sample=sample, variable="Normalized price")
        check(descriptive_table, f"{int(row['observations']):,}", f"Table 1 {sample} count")
        check(descriptive_table, f"{float(row['mean']):,.2f}", f"Table 1 {sample} mean")

    for source, estimator in (
        ("aggregate_estimates.csv", "aggregate_did"),
        ("aggregate_estimates.csv", "aggregate_sdid"),
        ("country_sdid_estimate.csv", "country_sdid_HICP"),
    ):
        row = one(source, estimator=estimator)
        check(main_table, f"{float(row['estimate']):.4f}", f"Table 2 {estimator} ATT")
        check(main_table, f"({float(row['std_error']):.4f})", f"Table 2 {estimator} SE")

    grocery = one("micro_estimates.csv", estimator="micro_did")
    check(tex, f"{float(grocery['estimate']):.4f}", "grocery diagnostic")
    carcass = read_rows("production_carcass_weight_estimate.csv")[0]
    check(tex, f"{float(carcass['estimate']):.4f}", "direct carcass estimate")
    omitted = one("country_sdid_omit_june.csv", specification="country_hicp_omit_june_2024")
    check(tex, f"{float(omitted['estimate']):.4f}", "country June-omission estimate")
    for row in read_rows("aggregate_omit_june.csv"):
        check(tex, f"{float(row['estimate']):.4f}", f"{row['estimator']} June omission")
    unit_weights = read_rows("country_sdid_unit_weights.csv")
    check(tex, f"{float(unit_weights[0]['effective_donors']):.1f}", "effective country donor count")
    time_weights = one("country_sdid_time_weights.csv", month_id_numeric="2024m6")
    check(tex, f"{100*float(time_weights['weight']):.1f}", "June country time-weight percent")

    price = one("price_benchmark_summary.csv", block_months="2")
    check(tex, f"{float(price['point']):.2f}", "provisional level anchor")
    for field in ("low", "high"):
        check(tex, f"{float(price[field]):.2f}", f"price-resampling {field}")

    scc = read_rows("scc_meta_summary.csv")[0]
    check(tex, f"{float(scc['mean']):.2f}", "selected SCC mean")
    check(tex, f"{float(scc['log_price_gap_effective_120']):.3f}", "average-burden equivalent")
    check(tex, f"{float(scc['log_price_gap_marginal_300']):.3f}", "marginal-incentive equivalent")
    scenarios = one("calibration_scenarios.csv", persistence="1", taxable_share="1", incremental_pass_through="1")
    check(tex, f"{float(scenarios['announcement_dkk_kg']):.2f}", "mapped CPI increment")
    check(tex, f"{float(scenarios['remaining_gap_dkk_kg']):.2f}", "full-response difference")

    for stale in ("162.44", "10.80", "47.61", "139,332", "15,558"):
        if stale in tex:
            raise AssertionError(f"Stale prior-run number in manuscript: {stale}")
    print("Manuscript key numbers match Stata CSVs.")


if __name__ == "__main__":
    main()
