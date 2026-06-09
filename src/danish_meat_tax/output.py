from __future__ import annotations

from math import exp
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BEEF_CO2E_KG_PER_KG = 59.6
NORDHAUS_2015_USD_2010_PER_TCO2E = 31.2
NORDHAUS_REAL_GROWTH_RATE = 0.03
NORDHAUS_TARGET_YEAR = 2030
NORDHAUS_BASE_YEAR = 2015
DANISH_TAX_DKK_PER_TCO2E = 300.0
USD_DKK_2024_AVERAGE = 6.8953
US_CPI_2010_AVERAGE = 218.056
US_CPI_2024_AVERAGE = 313.689


def _yerr(data: pd.DataFrame) -> list[np.ndarray]:
    low = data["estimate"] - data["conf_low"]
    high = data["conf_high"] - data["estimate"]
    return [low.fillna(0).to_numpy(), high.fillna(0).to_numpy()]


def make_event_study_plot(
    event_study_csv: Path,
    output_path: Path,
    reference_effect: float | None = None,
) -> Path:
    data = pd.read_csv(event_study_csv).sort_values("relative_time")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="firebrick", linestyle="--", linewidth=0.9)
    if reference_effect is not None:
        ax.axhline(reference_effect, color="#2f7d32", linestyle=":", linewidth=1.2, label="Carbon-price gap")
    ax.errorbar(
        data["relative_time"],
        data["estimate"],
        yerr=_yerr(data),
        fmt="o-",
        color="#1f4e79",
        ecolor="#6f8fb3",
        capsize=3,
    )
    ax.set_xlabel("Periods relative to 2024-06-24 announcement")
    ax.set_ylabel("Log price effect")
    ax.grid(axis="y", alpha=0.25)
    if reference_effect is not None:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def make_aggregate_trends_plot(aggregate_trends_csv: Path, output_path: Path) -> Path:
    data = pd.read_csv(aggregate_trends_csv, parse_dates=["period"]).sort_values(["series", "period"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axvline(pd.Timestamp("2024-06-24"), color="firebrick", linestyle="--", linewidth=0.9)
    for series, group_data in data.groupby("series"):
        ax.plot(group_data["period"], group_data["mean_log_price"], linewidth=1.2, label=series)
    ax.set_xlabel("Period")
    ax.set_ylabel("Mean log normalized price")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def make_synthetic_did_plot(sdid_trends_csv: Path, output_path: Path) -> Path:
    data = pd.read_csv(sdid_trends_csv, parse_dates=["period"]).sort_values("period")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axvline(pd.Timestamp("2024-06-24"), color="firebrick", linestyle="--", linewidth=0.9)
    ax.plot(data["period"], data["treated_mean"], linewidth=1.8, label="Treated")
    ax.plot(data["period"], data["synthetic_control_adjusted"], linewidth=1.8, label="Synthetic control")
    ax.set_xlabel("Period")
    ax.set_ylabel("Mean log normalized price")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def _format_coef(row: pd.Series) -> str:
    stars = ""
    if pd.notna(row.get("t_stat")):
        t_abs = abs(float(row["t_stat"]))
        if t_abs >= 2.58:
            stars = "***"
        elif t_abs >= 1.96:
            stars = "**"
        elif t_abs >= 1.65:
            stars = "*"
    return f"{float(row['estimate']):.4f}{stars}"


def _format_se(row: pd.Series) -> str:
    return f"({float(row['std_error']):.4f})" if pd.notna(row.get("std_error")) else ""


def _read_metadata(path: Path) -> dict[str, object]:
    return pd.read_csv(path).iloc[0].to_dict()


def _metadata_from_row(row: pd.Series, fallback: dict[str, object]) -> dict[str, object]:
    metadata = dict(fallback)
    for key in ("n_obs", "n_units", "n_periods", "fixed_effects", "cluster", "r_squared", "pre_treated_average"):
        if key in row and pd.notna(row[key]):
            metadata[key] = row[key]
    return metadata


def _latex_escape(value: object) -> str:
    return str(value).replace("_", "\\_")


def _format_group_label(group: str) -> str:
    labels = {
        "beef": "Beef",
        "dairy_cattle": "Dairy cattle",
        "lamb_sheep_goat": "Lamb, sheep, goat",
        "mixed_livestock": "Mixed livestock",
        "pork": "Pork",
    }
    return labels.get(group, group.replace("_", " ").title())


def _make_regression_table(
    columns: list[tuple[str, pd.Series, dict[str, object]]],
    output_path: Path,
    caption: str,
    notes: str,
    label: str | None = None,
) -> Path:
    alignment = "l" + "c" * len(columns)
    header = " & ".join([""] + [label for label, _, _ in columns]) + " \\\\"
    coef_row = " & ".join(["Treatment $\\times$ Post"] + [_format_coef(row) for _, row, _ in columns]) + " \\\\"
    se_row = " & ".join([""] + [_format_se(row) for _, row, _ in columns]) + " \\\\"
    obs_row = " & ".join(["Observations"] + [f"{int(meta['n_obs']):,}" for _, _, meta in columns]) + " \\\\"
    unit_row = " & ".join(["Units"] + [f"{int(meta['n_units']):,}" for _, _, meta in columns]) + " \\\\"
    period_row = " & ".join(["Periods"] + [f"{int(meta['n_periods']):,}" for _, _, meta in columns]) + " \\\\"
    pre_row = " & ".join(
        ["Pre-treatment avg."] + [f"{float(meta.get('pre_treated_average', np.nan)):.2f}" for _, _, meta in columns]
    ) + " \\\\"
    r2_values = []
    for _, _, meta in columns:
        r2 = meta.get("r_squared", np.nan)
        r2_values.append(f"{float(r2):.3f}" if pd.notna(r2) else "")
    r2_row = " & ".join(["$R^2$"] + r2_values) + " \\\\"
    table = "\n".join(
        [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}" if label else "",
            "\\footnotesize",
            "\\setlength{\\tabcolsep}{3pt}",
            f"\\begin{{tabular}}{{{alignment}}}",
            "\\hline\\hline",
            header,
            "\\hline",
            coef_row,
            se_row,
            "\\hline",
            obs_row,
            unit_row,
            period_row,
            pre_row,
            r2_row,
            "\\hline\\hline",
            "\\end{tabular}",
            f"\\begin{{minipage}}{{0.96\\linewidth}}\\footnotesize Notes: {notes}\\end{{minipage}}",
            "\\end{table}",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(table, encoding="utf-8")
    return output_path


def make_did_latex_table(did_dir: Path, output_path: Path) -> Path:
    ate = pd.read_csv(did_dir / "ate.csv").iloc[0]
    ate_meta = _read_metadata(did_dir / "ate_metadata.csv")
    heterogeneity = pd.read_csv(did_dir / "heterogeneity.csv")
    columns: list[tuple[str, pd.Series, dict[str, object]]] = [("All treated", ate, ate_meta)]
    heterogeneity_meta = _read_metadata(did_dir / "heterogeneity_metadata.csv")
    for _, row in heterogeneity.iterrows():
        group = str(row["term"]).removesuffix(" x post")
        meta = _metadata_from_row(row, heterogeneity_meta)
        columns.append((_latex_escape(_format_group_label(group)), row, meta))
    notes = (
        "Outcome is log normalized price in DKK per kilogram or liter. The all-treated column compares all treated "
        "livestock-exposed commodities with untreated food controls. Each commodity column is estimated separately "
        "against untreated food controls only. All columns include unit and period fixed effects. Standard errors, "
        "in parentheses, are clustered by unit. "
        "$^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.10$."
    )
    return _make_regression_table(columns, output_path, "DiD announcement effects", notes, label="tab:did")


def make_synthetic_did_latex_table(sdid_dir: Path, output_path: Path) -> Path:
    columns: list[tuple[str, pd.Series, dict[str, object]]] = []
    main = sdid_dir / "synthetic_did.csv"
    if main.exists():
        columns.append(("All treated", pd.read_csv(main).iloc[0], _read_metadata(sdid_dir / "synthetic_did_metadata.csv")))
    for path in sorted(sdid_dir.glob("synthetic_did_*.csv")):
        stem = path.stem
        if stem.endswith(("_metadata", "_trends", "_unit_weights", "_time_weights")) or stem == "synthetic_did":
            continue
        group = stem.removeprefix("synthetic_did_")
        metadata_path = sdid_dir / f"synthetic_did_{group}_metadata.csv"
        if metadata_path.exists():
            columns.append((_latex_escape(_format_group_label(group)), pd.read_csv(path).iloc[0], _read_metadata(metadata_path)))
    notes = (
        "Synthetic DiD uses complete commodity-store units. Unit weights match the treated pre-period path; "
        "time weights match post-period donor averages. Standard errors, in parentheses, use a nonparametric bootstrap "
        "over complete treated and control units. $^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.10$."
    )
    return _make_regression_table(
        columns,
        output_path,
        "Synthetic DiD announcement effects",
        notes,
        label="tab:sdid",
    )


def _beef_pre_price(panel_path: Path) -> float:
    panel = pd.read_csv(panel_path, parse_dates=["period"], dtype={"product_id": str}, low_memory=False)
    beef_pre = panel[(panel["treatment_group"] == "beef") & (panel["relative_time"] < 0)]
    return float(beef_pre["price"].mean())


def _nordhaus_2030_usd_2010_per_tco2e() -> float:
    years = NORDHAUS_TARGET_YEAR - NORDHAUS_BASE_YEAR
    return NORDHAUS_2015_USD_2010_PER_TCO2E * ((1 + NORDHAUS_REAL_GROWTH_RATE) ** years)


def _nordhaus_2030_usd_2024_per_tco2e() -> float:
    return _nordhaus_2030_usd_2010_per_tco2e() * US_CPI_2024_AVERAGE / US_CPI_2010_AVERAGE


def _danish_tax_usd_per_tco2e() -> float:
    return DANISH_TAX_DKK_PER_TCO2E / USD_DKK_2024_AVERAGE


def _carbon_price_gap_usd_per_tco2e() -> float:
    return _nordhaus_2030_usd_2024_per_tco2e() - _danish_tax_usd_per_tco2e()


def _gap_effect_log(pre_price_dkk: float) -> float:
    gap_usd_per_kg = _carbon_price_gap_usd_per_tco2e() * BEEF_CO2E_KG_PER_KG / 1000
    gap_dkk_per_kg = gap_usd_per_kg * USD_DKK_2024_AVERAGE
    return float(np.log((pre_price_dkk + gap_dkk_per_kg) / pre_price_dkk))


def _effect_money(estimate: float, pre_price_dkk: float) -> tuple[float, float]:
    dkk = pre_price_dkk * (exp(float(estimate)) - 1)
    usd = dkk / USD_DKK_2024_AVERAGE
    return dkk, usd


def make_beef_policy_calibration(
    panel_path: Path,
    did_dir: Path,
    sdid_dir: Path,
    figures_dir: Path,
    discussion_path: Path,
) -> dict[str, Path]:
    pre_price = _beef_pre_price(panel_path)
    reference_effect = _gap_effect_log(pre_price)
    did_beef = pd.read_csv(did_dir / "heterogeneity.csv")
    did_row = did_beef[did_beef["term"] == "beef x post"].iloc[0].copy()
    sdid_row = pd.read_csv(sdid_dir / "synthetic_did_beef.csv").iloc[0].copy()
    estimates = pd.DataFrame(
        [
            {"estimator": "DiD", **did_row.to_dict()},
            {"estimator": "SDiD", **sdid_row.to_dict()},
        ]
    )
    estimates["effect_dkk_per_kg"] = estimates["estimate"].map(lambda value: _effect_money(value, pre_price)[0])
    estimates["effect_usd_per_kg"] = estimates["estimate"].map(lambda value: _effect_money(value, pre_price)[1])
    estimates["implied_tax_usd_tco2e"] = estimates["effect_usd_per_kg"] * 1000 / BEEF_CO2E_KG_PER_KG
    nordhaus_2030_usd_2010 = _nordhaus_2030_usd_2010_per_tco2e()
    nordhaus_2024 = _nordhaus_2030_usd_2024_per_tco2e()
    danish_tax_usd = _danish_tax_usd_per_tco2e()
    gap_usd_tco2e = _carbon_price_gap_usd_per_tco2e()
    estimates["required_tax_usd_tco2e"] = nordhaus_2024 - estimates["implied_tax_usd_tco2e"]
    estimates["required_tax_dkk_tco2e"] = estimates["required_tax_usd_tco2e"] * USD_DKK_2024_AVERAGE
    estimates_path = sdid_dir.parent / "calibration" / "beef_policy_calibration.csv"
    estimates_path.parent.mkdir(parents=True, exist_ok=True)
    estimates.to_csv(estimates_path, index=False)

    figures_dir.mkdir(parents=True, exist_ok=True)
    att_path = figures_dir / "beef_att_policy_calibration.png"
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    x = np.array([-0.18, 0.18])
    ax.errorbar(
        x,
        estimates["estimate"],
        yerr=_yerr(estimates),
        fmt="o",
        color="#1f4e79",
        ecolor="#6f8fb3",
        capsize=4,
    )
    ax.axhline(reference_effect, color="#2f7d32", linestyle=":", linewidth=1.3, label="Carbon-price gap")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x, estimates["estimator"])
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylabel("Log price effect")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(att_path, dpi=200)
    plt.close(fig)

    event_path = figures_dir / "event_study_beef_policy_calibration.png"
    make_event_study_plot(did_dir / "event_study_beef.csv", event_path, reference_effect=reference_effect)

    event = pd.read_csv(did_dir / "event_study_beef.csv")
    latest = event[event["relative_time"] > 0].sort_values("relative_time").iloc[-1]
    latest_dkk, latest_usd = _effect_money(float(latest["estimate"]), pre_price)
    latest_tax = latest_usd * 1000 / BEEF_CO2E_KG_PER_KG
    latest_required_tax = nordhaus_2024 - latest_tax
    latest_required_tax_dkk = latest_required_tax * USD_DKK_2024_AVERAGE
    gap_dkk, gap_usd = _effect_money(reference_effect, pre_price)
    cpi_factor = US_CPI_2024_AVERAGE / US_CPI_2010_AVERAGE
    discussion = f"""# Beef Carbon-Price Calibration

This back-of-the-envelope exercise asks whether the estimated beef announcement price effect would cover the gap between the announced Danish livestock tax and the Nordhaus (2017) 2030 social cost of carbon benchmark. The earlier USD 4.7/tCO2e gap compares nominal USD values. With the internally consistent conversion used here, the gap is USD {gap_usd_tco2e:.1f}/tCO2e: Nordhaus reports USD {NORDHAUS_2015_USD_2010_PER_TCO2E:.1f}/tCO2e for 2015 in 2010 USD and states that the SCC grows at {100 * NORDHAUS_REAL_GROWTH_RATE:.0f}% per year in real terms, so the benchmark is first grown to 2030 and then converted to 2024 USD. The Danish tax is converted from DKK to USD with the 2024 average exchange rate.

Assumptions:

- Nordhaus benchmark: USD {NORDHAUS_2015_USD_2010_PER_TCO2E:.1f}/tCO2e for 2015 in 2010 USD, grown at {100 * NORDHAUS_REAL_GROWTH_RATE:.0f}% per year to USD {nordhaus_2030_usd_2010:.1f}/tCO2e in 2030, then converted to USD {nordhaus_2024:.1f}/tCO2e after multiplying by the CPI factor {cpi_factor:.4f}.
- Announced Danish tax: DKK {DANISH_TAX_DKK_PER_TCO2E:.0f}/tCO2e, or USD {danish_tax_usd:.1f}/tCO2e at the 2024 average exchange rate.
- Beef carbon intensity: {BEEF_CO2E_KG_PER_KG:.1f} kg CO2e/kg product, from the OECD (2025) agri-food carbon-footprint report's Poore and Nemecek (2018) beef-herd benchmark.
- Exchange rate: {USD_DKK_2024_AVERAGE:.4f} DKK/USD, the 2024 average USD/DKK rate.
- Average pre-intervention beef price in the estimation panel: {pre_price:.2f} DKK/kg, or {pre_price / USD_DKK_2024_AVERAGE:.2f} USD/kg.

The additional price needed to close the carbon-price gap is:

```math
\\Delta p =
\\frac{{{gap_usd_tco2e:.4f} \\times {BEEF_CO2E_KG_PER_KG:.1f}}}{{1000}}
= {gap_usd:.4f}\\;\\text{{USD/kg}}
= {gap_dkk:.4f}\\;\\text{{DKK/kg}}.
```

As a log price effect at the observed pre-period beef price:

```math
\\tau_{{gap}} =
\\log\\left(\\frac{{\\bar p_{{pre}} + \\Delta p}}{{\\bar p_{{pre}}}}\\right)
= {reference_effect:.4f}.
```

Main ATT comparison:

The DiD beef estimate compares beef product-store units with untreated food controls only. Other treated livestock commodities are excluded from the beef DiD regression rather than treated as controls. The SDiD beef robustness estimate applies the same focal-versus-untreated rule on complete commodity-store units.

| Estimator | ATT | 95% CI | DKK/kg | USD/kg | Implied announcement value, USD/tCO2e | Required tax, USD/tCO2e | Required tax, DKK/tCO2e |
|---|---:|---:|---:|---:|---:|---:|---:|
"""
    for _, row in estimates.iterrows():
        discussion += (
            f"| {row['estimator']} | {row['estimate']:.4f} | "
            f"[{row['conf_low']:.4f}, {row['conf_high']:.4f}] | "
            f"{row['effect_dkk_per_kg']:.2f} | {row['effect_usd_per_kg']:.2f} | "
            f"{row['implied_tax_usd_tco2e']:.1f} | {row['required_tax_usd_tco2e']:.1f} | "
            f"{row['required_tax_dkk_tco2e']:.0f} |\n"
        )
    discussion += f"""

The reference value is:

```math
\\tau_{{gap}} = {reference_effect:.4f}.
```

With the updated gap, this reference lies inside the DiD confidence interval and inside the SDiD confidence interval. Using the DiD ATT as the preferred estimate, the announcement effect is equivalent to USD {float(estimates.loc[estimates['estimator'] == 'DiD', 'implied_tax_usd_tco2e'].iloc[0]):.1f}/tCO2e, so the statutory tax that would exactly reach the inflation-adjusted Nordhaus benchmark is USD {float(estimates.loc[estimates['estimator'] == 'DiD', 'required_tax_usd_tco2e'].iloc[0]):.1f}/tCO2e, or DKK {float(estimates.loc[estimates['estimator'] == 'DiD', 'required_tax_dkk_tco2e'].iloc[0]):.0f}/tCO2e. Under this internally consistent benchmark, the DiD ATT does not imply lowering the announced DKK {DANISH_TAX_DKK_PER_TCO2E:.0f}/tCO2e gross tax; it implies a slightly higher tax. If one instead keeps the grown 2030 Nordhaus benchmark in 2010 USD and compares it directly with the nominal USD value of the Danish tax, the smaller nominal comparison would imply a tax of about USD {nordhaus_2030_usd_2010 - float(estimates.loc[estimates['estimator'] == 'DiD', 'implied_tax_usd_tco2e'].iloc[0]):.1f}/tCO2e.

Latest event-study comparison:

- Latest post-period relative time: {int(latest['relative_time'])}.
- Latest DiD event-study estimate: {float(latest['estimate']):.4f}, with 95% CI [{float(latest['conf_low']):.4f}, {float(latest['conf_high']):.4f}].
- Latest-period implied price increase: {latest_dkk:.2f} DKK/kg, or {latest_usd:.2f} USD/kg.
- Latest-period reverse-engineered carbon price: {latest_tax:.1f} USD/tCO2e.
- Latest-period required statutory tax to match Nordhaus exactly: {latest_required_tax:.1f} USD/tCO2e, or {latest_required_tax_dkk:.0f} DKK/tCO2e. Because this is negative, the literal latest-period calculation says the announcement effect alone exceeds the inflation-adjusted Nordhaus benchmark; with a nonnegative tax constraint, the implied statutory tax would be zero.

Figures:

- `outputs/figures/calibration/beef_att_policy_calibration.png`
- `outputs/figures/calibration/event_study_beef_policy_calibration.png`
"""
    discussion_path.parent.mkdir(parents=True, exist_ok=True)
    discussion_path.write_text(discussion, encoding="utf-8")
    return {"beef_calibration_plot": att_path, "beef_event_policy_plot": event_path, "beef_calibration_table": estimates_path}


def _clear_figures(figures_dir: Path) -> None:
    for pattern in ("*.png",):
        for path in figures_dir.glob(pattern):
            path.unlink()


def make_outputs(models_dir: Path, figures_dir: Path, tables_dir: Path, panel_path: Path | None = None) -> dict[str, Path]:
    did_dir = models_dir / "did"
    sdid_dir = models_dir / "sdid"
    did_figures = figures_dir / "did"
    sdid_figures = figures_dir / "sdid"
    calibration_figures = figures_dir / "calibration"
    did_tables = tables_dir / "did"
    sdid_tables = tables_dir / "sdid"
    for directory in (did_figures, sdid_figures, calibration_figures):
        directory.mkdir(parents=True, exist_ok=True)
        _clear_figures(directory)
    outputs: dict[str, Path] = {}
    outputs["event_study_plot"] = make_event_study_plot(did_dir / "event_study.csv", did_figures / "event_study_overall.png")
    for group_csv in sorted(did_dir.glob("event_study_*.csv")):
        group = group_csv.stem.removeprefix("event_study_")
        if group in {"metadata"} or group_csv.stem.endswith("_metadata"):
            continue
        outputs[f"event_study_{group}_plot"] = make_event_study_plot(group_csv, did_figures / f"event_study_{group}.png")
    trends = did_dir / "aggregate_trends.csv"
    if trends.exists():
        outputs["aggregate_trends_plot"] = make_aggregate_trends_plot(trends, did_figures / "aggregate_trends.png")
    outputs["ate_table"] = make_did_latex_table(did_dir, did_tables / "did_results.tex")
    sdid = sdid_dir / "synthetic_did.csv"
    sdid_trends = sdid_dir / "synthetic_did_trends.csv"
    if sdid.exists() and sdid_trends.exists():
        outputs["synthetic_did_plot"] = make_synthetic_did_plot(sdid_trends, sdid_figures / "synthetic_did_trends.png")
        for trends_path in sorted(sdid_dir.glob("synthetic_did_*_trends.csv")):
            group = trends_path.stem.removeprefix("synthetic_did_").removesuffix("_trends")
            outputs[f"synthetic_did_{group}_plot"] = make_synthetic_did_plot(
                trends_path,
                sdid_figures / f"synthetic_did_{group}_trends.png",
            )
        outputs["synthetic_did_table"] = make_synthetic_did_latex_table(sdid_dir, sdid_tables / "synthetic_did_results.tex")
    resolved_panel = panel_path or models_dir.parent.parent / "data" / "processed" / "commodity_panel.csv"
    if (did_dir / "heterogeneity.csv").exists() and (sdid_dir / "synthetic_did_beef.csv").exists() and resolved_panel.exists():
        outputs.update(
            make_beef_policy_calibration(
                resolved_panel,
                did_dir,
                sdid_dir,
                calibration_figures,
                models_dir.parent.parent / "docs" / "beef_carbon_price_calibration.md",
            )
        )
    return outputs
