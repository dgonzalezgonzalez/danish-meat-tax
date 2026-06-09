from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def make_event_study_plot(event_study_csv: Path, output_path: Path, title: str = "Event-study: livestock meat prices") -> Path:
    data = pd.read_csv(event_study_csv)
    data = data.sort_values("relative_time")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="firebrick", linestyle="--", linewidth=0.9)
    ax.errorbar(
        data["relative_time"],
        data["estimate"],
        yerr=[data["estimate"] - data["conf_low"], data["conf_high"] - data["estimate"]],
        fmt="o-",
        color="#1f4e79",
        ecolor="#6f8fb3",
        capsize=3,
    )
    ax.set_title(title)
    ax.set_xlabel("Periods relative to 2024-06-24 announcement")
    ax.set_ylabel("Log price effect")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def make_group_event_study_plot(event_study_by_group_csv: Path, output_path: Path) -> Path:
    data = pd.read_csv(event_study_by_group_csv).sort_values(["treatment_group", "relative_time"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="firebrick", linestyle="--", linewidth=0.9)
    for group, group_data in data.groupby("treatment_group"):
        ax.plot(group_data["relative_time"], group_data["estimate"], marker="o", linewidth=1.2, markersize=3, label=group)
    ax.set_title("Event-study heterogeneity by livestock product group")
    ax.set_xlabel("Periods relative to 2024-06-24 announcement")
    ax.set_ylabel("Log price effect")
    ax.grid(axis="y", alpha=0.25)
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
    ax.set_title("Aggregate normalized food-price trends")
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
    return f"{row['estimate']:.4f}{stars}"


def make_latex_table(ate_csv: Path, heterogeneity_csv: Path, metadata_csv: Path, output_path: Path) -> Path:
    ate = pd.read_csv(ate_csv)
    heterogeneity = pd.read_csv(heterogeneity_csv)
    metadata = pd.read_csv(metadata_csv).iloc[0].to_dict()
    rows = []
    for label, data in (("Overall", ate), ("Heterogeneity", heterogeneity)):
        for _, row in data.iterrows():
            rows.append(
                f"{label}: {row['term']} & {_format_coef(row)} & ({row['std_error']:.4f}) & "
                f"{row['p_value']:.4f} & [{row['conf_low']:.4f}, {row['conf_high']:.4f}] \\\\"
            )
    note = (
        "Unit and period fixed effects included. Standard errors clustered by unit_id. "
        "Outcome is log normalized food price. Event date is 2024-06-24. "
        "Main sample excludes non-food and unknown products."
    )
    table = "\n".join(
        [
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Announcement effects on Danish grocery meat prices}",
            "\\begin{tabular}{lcccc}",
            "\\hline",
            "Specification & Estimate & Std. error & p-value & 95\\% CI \\\\",
            "\\hline",
            *rows,
            "\\hline",
            f"Observations & \\multicolumn{{4}}{{c}}{{{int(metadata['n_obs'])}}} \\\\",
            f"Units & \\multicolumn{{4}}{{c}}{{{int(metadata['n_units'])}}} \\\\",
            f"Fixed effects & \\multicolumn{{4}}{{c}}{{{metadata['fixed_effects']}}} \\\\",
            "\\hline",
            "\\end{tabular}",
            f"\\begin{{minipage}}{{0.9\\linewidth}}\\footnotesize Notes: {note}\\end{{minipage}}",
            "\\end{table}",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(table, encoding="utf-8")
    return output_path


def make_outputs(models_dir: Path, figures_dir: Path, tables_dir: Path) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    event_plot = make_event_study_plot(models_dir / "event_study.csv", figures_dir / "event_study_overall.png")
    outputs["event_study_plot"] = event_plot
    by_group = models_dir / "event_study_by_group.csv"
    if by_group.exists():
        outputs["event_study_by_group_plot"] = make_group_event_study_plot(
            by_group, figures_dir / "event_study_by_group.png"
        )
        for group in pd.read_csv(by_group, usecols=["treatment_group"])["treatment_group"].dropna().unique():
            group_csv = models_dir / f"event_study_{group}.csv"
            if group_csv.exists():
                outputs[f"event_study_{group}_plot"] = make_event_study_plot(
                    group_csv,
                    figures_dir / f"event_study_{group}.png",
                    title=f"Event-study: {group}",
                )
    trends = models_dir / "aggregate_trends.csv"
    if trends.exists():
        outputs["aggregate_trends_plot"] = make_aggregate_trends_plot(
            trends,
            figures_dir / "aggregate_trends.png",
        )
    latex_table = make_latex_table(
        models_dir / "ate.csv",
        models_dir / "heterogeneity.csv",
        models_dir / "ate_metadata.csv",
        tables_dir / "ate_results.tex",
    )
    outputs["ate_table"] = latex_table
    return outputs
