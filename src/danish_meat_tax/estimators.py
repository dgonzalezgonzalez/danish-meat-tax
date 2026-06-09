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


@dataclass(frozen=True)
class SyntheticDiDResult:
    coefficients: pd.DataFrame
    metadata: dict[str, str | int | float]
    trends: pd.DataFrame
    unit_weights: pd.DataFrame
    time_weights: pd.DataFrame


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


def _project_simplex(values: np.ndarray) -> np.ndarray:
    if values.size == 1:
        return np.ones_like(values)
    sorted_values = np.sort(values)[::-1]
    cumulative = np.cumsum(sorted_values)
    support = sorted_values * np.arange(1, values.size + 1) > (cumulative - 1)
    if not support.any():
        return np.full_like(values, 1 / values.size)
    rho = np.nonzero(support)[0][-1]
    theta = (cumulative[rho] - 1) / (rho + 1)
    return np.maximum(values - theta, 0)


def _fit_simplex_weights(features: np.ndarray, target: np.ndarray, ridge: float = 1e-6, max_iter: int = 4000) -> np.ndarray:
    weights = np.full(features.shape[1], 1 / features.shape[1])
    lipschitz = 2 * (np.linalg.norm(features, ord=2) ** 2 + ridge)
    step = 1 / max(lipschitz, 1e-8)
    for _ in range(max_iter):
        gradient = 2 * (features.T @ (features @ weights - target) + ridge * weights)
        updated = _project_simplex(weights - step * gradient)
        if np.linalg.norm(updated - weights) < 1e-10:
            weights = updated
            break
        weights = updated
    return weights


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
    ss_resid = float(residuals.T @ residuals)
    ss_total = float(((y_resid - y_resid.mean()) ** 2).sum())
    r_squared = 1 - ss_resid / ss_total if ss_total > 0 else np.nan
    pre_treated_average = data.loc[data["treated"].astype(bool) & ~data["post"].astype(bool), "price"].mean()
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
            "r_squared": float(r_squared),
            "pre_treated_average": float(pre_treated_average) if pd.notna(pre_treated_average) else np.nan,
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
    result = _fit_twfe(data, columns, labels)
    pre_averages = {
        f"{group} x post": data.loc[(data["treatment_group"] == group) & ~data["post"].astype(bool), "price"].mean()
        for group in sorted(data.loc[data["treated"], "treatment_group"].dropna().unique())
    }
    result.coefficients["pre_treated_average"] = result.coefficients["term"].map(pre_averages)
    return result


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
    reference_row = pd.DataFrame(
        [
            {
                "term": str(reference),
                "estimate": 0.0,
                "std_error": np.nan,
                "conf_low": np.nan,
                "conf_high": np.nan,
                "t_stat": np.nan,
                "p_value": np.nan,
                "relative_time": int(reference),
                "pre_period": True,
            }
        ]
    )
    coefficients = (
        pd.concat([result.coefficients, reference_row], ignore_index=True)
        .sort_values("relative_time")
        .reset_index(drop=True)
    )
    return RegressionResult(coefficients=coefficients, metadata=result.metadata)


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


def _commodity_store_panel(panel: pd.DataFrame) -> pd.DataFrame:
    data = panel.copy()
    if data["unit_id"].astype(str).str.contains("::").all() and data["unit_id"].nunique() <= 500:
        return data
    keys = ["store", "commodity", "treatment_group", "period"]
    grouped = (
        data.groupby(keys, as_index=False)
        .agg(
            log_price=("log_price", "mean"),
            price=("price", "mean"),
            treated=("treated", "first"),
            relative_time=("relative_time", "first"),
            post=("post", "first"),
        )
    )
    grouped["unit_id"] = grouped["store"].astype(str) + "::" + grouped["commodity"].astype(str)
    return grouped


def _bootstrap_sdid_estimates(
    balanced: pd.DataFrame,
    treated_units: list[str],
    control_units: list[str],
    seed: int,
    reps: int,
) -> list[float]:
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    for rep in range(reps):
        sampled_units: list[pd.DataFrame] = []
        for arm, units in (("treated", treated_units), ("control", control_units)):
            draws = rng.choice(units, size=len(units), replace=True)
            for draw_index, unit in enumerate(draws):
                copy = balanced[balanced["unit_id"] == unit].copy()
                copy["unit_id"] = f"{arm}_boot{rep}_{draw_index}::{unit}"
                sampled_units.append(copy)
        boot = pd.concat(sampled_units, ignore_index=True)
        try:
            estimates.append(_synthetic_did_point(boot))
        except ValueError:
            continue
    return estimates


def _synthetic_did_core(data: pd.DataFrame, bootstrap_seed: int = 20240624, bootstrap_reps: int = 25) -> SyntheticDiDResult:
    panel = _commodity_store_panel(data)
    period_count = panel["period"].nunique()
    support = panel.groupby("unit_id")["period"].nunique()
    complete_units = support[support == period_count].index
    balanced = panel[panel["unit_id"].isin(complete_units)].copy()
    if balanced.empty:
        raise ValueError("Synthetic DiD needs at least one complete unit.")
    unit_flags = balanced.groupby("unit_id")["treated"].first().astype(bool)
    treated_units = list(unit_flags[unit_flags].index)
    control_units = list(unit_flags[~unit_flags].index)
    if len(treated_units) < 1 or len(control_units) < 2:
        raise ValueError("Synthetic DiD needs complete treated and control units.")

    wide = balanced.pivot(index="unit_id", columns="period", values="log_price").sort_index(axis=1)
    periods = list(wide.columns)
    rel = balanced.drop_duplicates("period").set_index("period")["relative_time"].reindex(periods)
    pre_periods = [period for period in periods if int(rel.loc[period]) < 0]
    post_periods = [period for period in periods if int(rel.loc[period]) > 0]
    if len(pre_periods) < 2 or len(post_periods) < 1:
        raise ValueError("Synthetic DiD needs at least two pre periods and one post period.")

    y_treated = wide.loc[treated_units]
    y_control = wide.loc[control_units]
    treated_pre = y_treated[pre_periods].mean(axis=0).to_numpy()
    treated_post = y_treated[post_periods].mean(axis=0).to_numpy()
    control_pre = y_control[pre_periods].to_numpy()
    control_post = y_control[post_periods].to_numpy()

    unit_weights = _fit_simplex_weights(control_pre.T, treated_pre)
    time_weights = _fit_simplex_weights(control_pre, control_post.mean(axis=1))
    synth_pre = unit_weights @ control_pre
    synth_post = unit_weights @ control_post
    pre_gap = float(time_weights @ (treated_pre - synth_pre))
    estimate = float(treated_post.mean() - synth_post.mean() - pre_gap)

    bootstrap_estimates = _bootstrap_sdid_estimates(balanced, treated_units, control_units, bootstrap_seed, bootstrap_reps)
    std_error = float(np.std(bootstrap_estimates, ddof=1)) if len(bootstrap_estimates) > 1 else np.nan
    t_stat = estimate / std_error if std_error and not np.isnan(std_error) else np.nan
    p_value = erfc(abs(float(t_stat)) / sqrt(2)) if pd.notna(t_stat) else np.nan
    coefficients = pd.DataFrame(
        [
            {
                "term": "synthetic DiD",
                "estimate": estimate,
                "std_error": std_error,
                "p_value": p_value,
                "conf_low": estimate - 1.96 * std_error if pd.notna(std_error) else np.nan,
                "conf_high": estimate + 1.96 * std_error if pd.notna(std_error) else np.nan,
                "t_stat": t_stat,
            }
        ]
    )
    treated_path = y_treated[periods].mean(axis=0).to_numpy()
    synth_path = unit_weights @ y_control[periods].to_numpy()
    trends = pd.DataFrame(
        {
            "period": periods,
            "relative_time": [int(rel.loc[period]) for period in periods],
            "treated_mean": treated_path,
            "synthetic_control": synth_path,
            "synthetic_control_adjusted": synth_path + pre_gap,
            "gap": treated_path - (synth_path + pre_gap),
        }
    )
    return SyntheticDiDResult(
        coefficients=coefficients,
        metadata={
            "n_obs": int(len(balanced)),
            "n_units": int(balanced["unit_id"].nunique()),
            "n_treated_units": int(len(treated_units)),
            "n_control_units": int(len(control_units)),
            "n_periods": int(len(periods)),
            "n_pre_periods": int(len(pre_periods)),
            "n_post_periods": int(len(post_periods)),
            "pre_gap_adjustment": pre_gap,
            "bootstrap_reps": int(len(bootstrap_estimates)),
            "bootstrap_seed": int(bootstrap_seed),
            "inference": "nonparametric bootstrap over complete treated and control units",
            "unit_level": "commodity_store_complete",
            "pre_treated_average": float(balanced.loc[balanced["treated"].astype(bool) & balanced["period"].isin(pre_periods), "price"].mean()),
        },
        trends=trends,
        unit_weights=pd.DataFrame({"unit_id": control_units, "weight": unit_weights}),
        time_weights=pd.DataFrame({"period": pre_periods, "weight": time_weights}),
    )


def _synthetic_did_point(data: pd.DataFrame) -> float:
    panel = _commodity_store_panel(data)
    period_count = panel["period"].nunique()
    complete_units = panel.groupby("unit_id")["period"].nunique().loc[lambda series: series == period_count].index
    balanced = panel[panel["unit_id"].isin(complete_units)].copy()
    unit_flags = balanced.groupby("unit_id")["treated"].first().astype(bool)
    treated_units = list(unit_flags[unit_flags].index)
    control_units = list(unit_flags[~unit_flags].index)
    if len(treated_units) < 1 or len(control_units) < 2:
        raise ValueError("insufficient complete units")
    wide = balanced.pivot(index="unit_id", columns="period", values="log_price").sort_index(axis=1)
    rel = balanced.drop_duplicates("period").set_index("period")["relative_time"].reindex(wide.columns)
    pre_periods = [period for period in wide.columns if int(rel.loc[period]) < 0]
    post_periods = [period for period in wide.columns if int(rel.loc[period]) > 0]
    y_treated = wide.loc[treated_units]
    y_control = wide.loc[control_units]
    control_pre = y_control[pre_periods].to_numpy()
    control_post = y_control[post_periods].to_numpy()
    treated_pre = y_treated[pre_periods].mean(axis=0).to_numpy()
    treated_post = y_treated[post_periods].mean(axis=0).to_numpy()
    unit_weights = _fit_simplex_weights(control_pre.T, treated_pre)
    time_weights = _fit_simplex_weights(control_pre, control_post.mean(axis=1))
    pre_gap = float(time_weights @ (treated_pre - unit_weights @ control_pre))
    return float(treated_post.mean() - (unit_weights @ control_post).mean() - pre_gap)


def estimate_synthetic_did(panel: pd.DataFrame) -> SyntheticDiDResult:
    return _synthetic_did_core(panel)


def estimate_synthetic_did_for_group(panel: pd.DataFrame, treatment_group: str) -> SyntheticDiDResult:
    data = panel[(~panel["treated"]) | (panel["treatment_group"] == treatment_group)].copy()
    data["treated"] = data["treatment_group"] == treatment_group
    data["did"] = data["treated"].astype(int) * data["post"].astype(int)
    result = _synthetic_did_core(data)
    coefficients = result.coefficients.copy()
    coefficients["treatment_group"] = treatment_group
    return SyntheticDiDResult(
        coefficients=coefficients,
        metadata={**result.metadata, "treatment_group": treatment_group},
        trends=result.trends.assign(treatment_group=treatment_group),
        unit_weights=result.unit_weights.assign(treatment_group=treatment_group),
        time_weights=result.time_weights.assign(treatment_group=treatment_group),
    )


def _clear_generated_model_outputs(models_dir: Path) -> None:
    patterns = (
        "ate*.csv",
        "heterogeneity*.csv",
        "event_study*.csv",
        "pretrend_summary.csv",
        "aggregate_trends.csv",
        "skipped_event_study_groups.csv",
        "synthetic_did*.csv",
    )
    for pattern in patterns:
        for path in models_dir.glob(pattern):
            path.unlink()


def run_estimations(panel_path: Path, models_dir: Path) -> dict[str, RegressionResult]:
    models_dir.mkdir(parents=True, exist_ok=True)
    did_dir = models_dir / "did"
    sdid_dir = models_dir / "sdid"
    did_dir.mkdir(parents=True, exist_ok=True)
    sdid_dir.mkdir(parents=True, exist_ok=True)
    _clear_generated_model_outputs(models_dir)
    _clear_generated_model_outputs(did_dir)
    _clear_generated_model_outputs(sdid_dir)
    panel = pd.read_csv(panel_path, parse_dates=["period"], dtype={"product_id": str}, low_memory=False)
    results = {
        "ate": estimate_ate(panel),
        "heterogeneity": estimate_heterogeneity(panel),
        "event_study": estimate_event_study(panel),
    }
    skipped_groups: list[dict[str, str]] = []
    for group in sorted(panel.loc[panel["treated"], "treatment_group"].dropna().unique()):
        try:
            result = estimate_event_study_for_group(panel, group)
        except ValueError as exc:
            skipped_groups.append({"treatment_group": group, "reason": str(exc)})
            continue
        results[f"event_study_{group}"] = result
    for name, result in results.items():
        result.coefficients.to_csv(did_dir / f"{name}.csv", index=False)
        pd.DataFrame([result.metadata]).to_csv(did_dir / f"{name}_metadata.csv", index=False)
    try:
        sdid = estimate_synthetic_did(panel)
    except ValueError as exc:
        pd.DataFrame([{"specification": "overall", "reason": str(exc)}]).to_csv(sdid_dir / "synthetic_did_skipped.csv", index=False)
    else:
        sdid.coefficients.to_csv(sdid_dir / "synthetic_did.csv", index=False)
        pd.DataFrame([sdid.metadata]).to_csv(sdid_dir / "synthetic_did_metadata.csv", index=False)
        sdid.trends.to_csv(sdid_dir / "synthetic_did_trends.csv", index=False)
        sdid.unit_weights.to_csv(sdid_dir / "synthetic_did_unit_weights.csv", index=False)
        sdid.time_weights.to_csv(sdid_dir / "synthetic_did_time_weights.csv", index=False)
    skipped_sdid_groups: list[dict[str, str]] = []
    for group in sorted(panel.loc[panel["treated"], "treatment_group"].dropna().unique()):
        try:
            sdid_group = estimate_synthetic_did_for_group(panel, group)
        except ValueError as exc:
            skipped_sdid_groups.append({"treatment_group": group, "reason": str(exc)})
            continue
        sdid_group.coefficients.to_csv(sdid_dir / f"synthetic_did_{group}.csv", index=False)
        pd.DataFrame([sdid_group.metadata]).to_csv(sdid_dir / f"synthetic_did_{group}_metadata.csv", index=False)
        sdid_group.trends.to_csv(sdid_dir / f"synthetic_did_{group}_trends.csv", index=False)
        sdid_group.unit_weights.to_csv(sdid_dir / f"synthetic_did_{group}_unit_weights.csv", index=False)
        sdid_group.time_weights.to_csv(sdid_dir / f"synthetic_did_{group}_time_weights.csv", index=False)
    if skipped_groups:
        pd.DataFrame(skipped_groups).to_csv(did_dir / "skipped_event_study_groups.csv", index=False)
    if skipped_sdid_groups:
        pd.DataFrame(skipped_sdid_groups).to_csv(sdid_dir / "skipped_sdid_groups.csv", index=False)
    summaries = [make_pretrend_summary(results["event_study"].coefficients, "overall")]
    summaries.extend(
        make_pretrend_summary(result.coefficients, name.replace("event_study_", ""))
        for name, result in results.items()
        if name.startswith("event_study_")
    )
    pd.concat(summaries, ignore_index=True).to_csv(did_dir / "pretrend_summary.csv", index=False)
    make_aggregate_trends(panel).to_csv(did_dir / "aggregate_trends.csv", index=False)
    return results
