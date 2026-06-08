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
    meat = np.zeros((x.shape[1], x.shape[1]))
    for cluster in clusters.unique():
        mask = clusters == cluster
        score = x[mask.to_numpy()].T @ residuals[mask.to_numpy()]
        meat += np.outer(score, score)
    cov = xtx_inv @ meat @ xtx_inv
    g = clusters.nunique()
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
    columns: list[str] = []
    labels: list[str] = []
    for rel in sorted(data["relative_time"].unique()):
        if rel == reference:
            continue
        col = f"event_{rel}"
        data[col] = ((data["relative_time"] == rel) & data["treated"]).astype(int)
        columns.append(col)
        labels.append(str(rel))
    result = _fit_twfe(data, columns, labels)
    result.coefficients["relative_time"] = result.coefficients["term"].astype(int)
    return result


def run_estimations(panel_path: Path, models_dir: Path) -> dict[str, RegressionResult]:
    models_dir.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(panel_path, parse_dates=["period"])
    results = {
        "ate": estimate_ate(panel),
        "heterogeneity": estimate_heterogeneity(panel),
        "event_study": estimate_event_study(panel),
    }
    for name, result in results.items():
        result.coefficients.to_csv(models_dir / f"{name}.csv", index=False)
        pd.DataFrame([result.metadata]).to_csv(models_dir / f"{name}_metadata.csv", index=False)
    return results
