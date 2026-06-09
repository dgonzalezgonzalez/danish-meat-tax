from __future__ import annotations

from dataclasses import dataclass
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RegressionResult:
    coefficients: pd.DataFrame
    metadata: dict[str, str | int]


def _within_transform(values: np.ndarray, units: pd.Series, periods: pd.Series) -> np.ndarray:
    value_columns = [f"v{i}" for i in range(values.shape[1])]
    frame = pd.DataFrame(values, columns=value_columns)
    frame["unit"] = units.to_numpy()
    frame["period"] = periods.to_numpy()
    unit_means = frame.groupby("unit")[value_columns].transform("mean").to_numpy()
    period_means = frame.groupby("period")[value_columns].transform("mean").to_numpy()
    overall = np.nanmean(values, axis=0)
    return values - unit_means - period_means + overall


def _cluster_se(x: np.ndarray, residuals: np.ndarray, clusters: pd.Series) -> np.ndarray:
    xtx_inv = np.linalg.pinv(x.T @ x)
    codes, uniques = pd.factorize(clusters, sort=False)
    scores = np.zeros((len(uniques), x.shape[1]))
    np.add.at(scores, codes, x * residuals[:, None])
    meat = scores.T @ scores
    cov = xtx_inv @ meat @ xtx_inv
    g = len(uniques)
    n, k = x.shape
    if g > 1 and n > k:
        cov *= (g / (g - 1)) * ((n - 1) / (n - k))
    return np.sqrt(np.maximum(np.diag(cov), 0))


def _fit_twfe(panel: pd.DataFrame, columns: list[str], labels: list[str]) -> RegressionResult:
    data = panel.dropna(subset=["log_price", *columns]).copy()
    y = data[["log_price"]].to_numpy()
    x = data[columns].astype(float).to_numpy()
    y_resid = _within_transform(y, data["unit_id"], data["period"]).ravel()
    x_resid = _within_transform(x, data["unit_id"], data["period"])
    keep = np.linalg.norm(x_resid, axis=0) > 1e-10
    x_resid = x_resid[:, keep]
    kept_labels = [label for label, flag in zip(labels, keep) if flag]
    if not kept_labels:
        raise ValueError("No treatment variation remains after fixed effects.")
    beta = np.linalg.pinv(x_resid.T @ x_resid) @ (x_resid.T @ y_resid)
    residuals = y_resid - x_resid @ beta
    se = _cluster_se(x_resid, residuals, data["unit_id"])
    out = pd.DataFrame(
        {
            "term": kept_labels,
            "estimate": beta,
            "std_error": se,
            "conf_low": beta - 1.96 * se,
            "conf_high": beta + 1.96 * se,
        }
    )
    out["t_stat"] = out["estimate"] / out["std_error"].replace(0, np.nan)
    out["p_value"] = out["t_stat"].abs().map(lambda value: erfc(float(value) / sqrt(2)) if pd.notna(value) else np.nan)
    return RegressionResult(
        coefficients=out,
        metadata={
            "n_obs": int(len(data)),
            "n_units": int(data["unit_id"].nunique()),
            "n_periods": int(data["period"].nunique()),
            "fixed_effects": "unit_id + period",
            "cluster": "unit_id",
        },
    )


def estimate_ate(panel: pd.DataFrame) -> RegressionResult:
    return _fit_twfe(panel, ["did"], ["treated x post"])


def estimate_heterogeneity(panel: pd.DataFrame) -> RegressionResult:
    data = panel.copy()
    columns: list[str] = []
    labels: list[str] = []
    for group in sorted(data.loc[data["treated"], "treatment_group"].dropna().unique()):
        col = f"did_{group}"
        data[col] = ((data["treatment_group"] == group) & data["post"]).astype(int)
        columns.append(col)
        labels.append(f"{group} x post")
    return _fit_twfe(data, columns, labels)


def estimate_event_study(panel: pd.DataFrame, reference: int = -1) -> RegressionResult:
    data = panel.copy()
    rel_values = [rel for rel in sorted(data["relative_time"].unique()) if rel != reference]
    columns = [f"event_{rel}" for rel in rel_values]
    labels = [str(rel) for rel in rel_values]
    event_columns = {
        col: ((data["relative_time"] == rel) & data["treated"]).astype(int)
        for col, rel in zip(columns, rel_values)
    }
    data = pd.concat([data, pd.DataFrame(event_columns, index=data.index)], axis=1)
    result = _fit_twfe(data, columns, labels)
    result.coefficients["relative_time"] = result.coefficients["term"].astype(int)
    result.coefficients["pre_period"] = result.coefficients["relative_time"] < 0
    return result


def estimate_event_study_for_group(panel: pd.DataFrame, treatment_group: str, reference: int = -1) -> RegressionResult:
    data = panel[(~panel["treated"]) | (panel["treatment_group"] == treatment_group)].copy()
    if data.loc[data["treatment_group"] == treatment_group, "unit_id"].nunique() < 2:
        raise ValueError(f"Too few treated units for {treatment_group}.")
    data["treated"] = data["treatment_group"] == treatment_group
    data["did"] = data["treated"].astype(int) * data["post"].astype(int)
    result = estimate_event_study(data, reference=reference)
    coefficients = result.coefficients.copy()
    coefficients["treatment_group"] = treatment_group
    return RegressionResult(
        coefficients=coefficients,
        metadata={**result.metadata, "treatment_group": treatment_group},
    )


def make_pretrend_summary(event_study: pd.DataFrame, label: str) -> pd.DataFrame:
    pre = event_study[(event_study["relative_time"] < 0) & (event_study["relative_time"] != -1)].copy()
    if pre.empty:
        return pd.DataFrame(
            [
                {
                    "specification": label,
                    "n_pre_coefficients": 0,
                    "mean_abs_pre_estimate": np.nan,
                    "max_abs_pre_estimate": np.nan,
                    "max_abs_pre_t": np.nan,
                    "passes_individual_pretrend_screen": False,
                    "diagnostic": "no_pre_coefficients",
                }
            ]
        )
    max_abs_t = float(pre["t_stat"].abs().max())
    return pd.DataFrame(
        [
            {
                "specification": label,
                "n_pre_coefficients": int(len(pre)),
                "mean_abs_pre_estimate": float(pre["estimate"].abs().mean()),
                "max_abs_pre_estimate": float(pre["estimate"].abs().max()),
                "max_abs_pre_t": max_abs_t,
                "passes_individual_pretrend_screen": max_abs_t < 1.96,
                "diagnostic": "inspect_joint_pretrend",
            }
        ]
    )


def make_aggregate_trends(panel: pd.DataFrame) -> pd.DataFrame:
    data = panel.copy()
    data["series"] = np.where(data["treated"].astype(bool), data["treatment_group"], "control_food")
    return (
        data.groupby(["period", "relative_time", "series"], as_index=False)
        .agg(
            mean_log_price=("log_price", "mean"),
            mean_price=("price", "mean"),
            units=("unit_id", "nunique"),
        )
        .sort_values(["series", "period"])
    )


def run_estimations(panel_path: Path, models_dir: Path) -> dict[str, RegressionResult]:
    models_dir.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(panel_path, parse_dates=["period"], dtype={"product_id": str}, low_memory=False)
    results = {
        "ate": estimate_ate(panel),
        "heterogeneity": estimate_heterogeneity(panel),
        "event_study": estimate_event_study(panel),
    }
    group_event_studies: list[pd.DataFrame] = []
    skipped_groups: list[dict[str, str]] = []
    for group in sorted(panel.loc[panel["treated"], "treatment_group"].dropna().unique()):
        try:
            result = estimate_event_study_for_group(panel, group)
        except ValueError as exc:
            skipped_groups.append({"treatment_group": group, "reason": str(exc)})
            continue
        results[f"event_study_{group}"] = result
        group_event_studies.append(result.coefficients)
    for name, result in results.items():
        result.coefficients.to_csv(models_dir / f"{name}.csv", index=False)
        pd.DataFrame([result.metadata]).to_csv(models_dir / f"{name}_metadata.csv", index=False)
    if group_event_studies:
        pd.concat(group_event_studies, ignore_index=True).to_csv(models_dir / "event_study_by_group.csv", index=False)
    if skipped_groups:
        pd.DataFrame(skipped_groups).to_csv(models_dir / "skipped_event_study_groups.csv", index=False)
    summaries = [make_pretrend_summary(results["event_study"].coefficients, "overall")]
    summaries.extend(
        make_pretrend_summary(result.coefficients, name.replace("event_study_", ""))
        for name, result in results.items()
        if name.startswith("event_study_")
    )
    pd.concat(summaries, ignore_index=True).to_csv(models_dir / "pretrend_summary.csv", index=False)
    make_aggregate_trends(panel).to_csv(models_dir / "aggregate_trends.csv", index=False)
    return results
