from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PanelResult:
    panel: pd.DataFrame
    diagnostics: dict[str, int | str]


def _relative_time(period: pd.Timestamp, event_period: pd.Timestamp, frequency: str) -> int:
    if frequency == "weekly":
        return int((period - event_period).days // 7)
    return int((period - event_period).days)


def _filter_analysis_sample(
    frame: pd.DataFrame,
    food_only: bool,
    exclude_unknown: bool,
    include_dairy_as_treated: bool,
) -> pd.DataFrame:
    data = frame.copy()
    if "food_status" not in data:
        data["food_status"] = "food"
    if "analysis_role" not in data:
        data["analysis_role"] = np.where(data["treated"].astype(bool), "treated_livestock_meat", "control_food")
    if "normalization_status" not in data:
        data["normalization_status"] = "ok"
    if "normalized_price" not in data:
        data["normalized_price"] = data["price"]
    if "normalized_price_unit" not in data:
        data["normalized_price_unit"] = "raw_price"
    if food_only:
        data = data[data["food_status"] == "food"].copy()
    if exclude_unknown:
        data = data[(data["commodity"] != "unknown") & (data["treatment_group"] != "unknown")].copy()
    data = data[(data["normalization_status"] == "ok") & data["normalized_price"].notna() & (data["normalized_price"] > 0)].copy()
    if not include_dairy_as_treated:
        dairy = data["treatment_group"] == "dairy_cattle"
        data.loc[dairy, "treated"] = False
        data.loc[dairy, "treatment_group"] = "control_animal_products"
        data.loc[dairy, "analysis_role"] = "control_food"
    return data


def _aggregate(frame: pd.DataFrame, frequency: str, event_date: pd.Timestamp) -> pd.DataFrame:
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    if frequency == "weekly":
        data["period"] = data["date"].dt.to_period("W-SUN").dt.start_time
        data["event_period"] = event_date.to_period("W-SUN").start_time
    elif frequency == "daily":
        data["period"] = data["date"]
        data["event_period"] = event_date
    else:
        raise ValueError("frequency must be daily or weekly")
    grouped = (
        data.groupby(["unit_id", "period"], as_index=False)
        .agg(
            price=("normalized_price", "mean"),
            raw_price=("price", "mean"),
            store=("store", "first"),
            product_id=("product_id", "first"),
            product_name=("product_name", "first"),
            commodity=("commodity", "first"),
            treated=("treated", "first"),
            treatment_group=("treatment_group", "first"),
            policy_confidence=("policy_confidence", "first"),
            food_status=("food_status", "first"),
            analysis_role=("analysis_role", "first"),
            normalized_price_unit=("normalized_price_unit", "first"),
            event_period=("event_period", "first"),
        )
    )
    return grouped


def _aggregate_unit_level(data: pd.DataFrame, unit_level: str) -> pd.DataFrame:
    if unit_level == "product_store":
        return data
    if unit_level == "commodity_store":
        keys = ["store", "commodity", "treatment_group", "period"]
    elif unit_level == "commodity":
        data = data.copy()
        data["store"] = "all_stores"
        keys = ["commodity", "treatment_group", "period"]
    else:
        raise ValueError("unit_level must be product_store, commodity_store, or commodity")
    grouped = (
        data.groupby(keys, as_index=False)
        .agg(
            price=("price", "mean"),
            raw_price=("raw_price", "mean"),
            treated=("treated", "first"),
            product_id=("commodity", "first"),
            product_name=("commodity", "first"),
            policy_confidence=("policy_confidence", "first"),
            food_status=("food_status", "first"),
            analysis_role=("analysis_role", "first"),
            normalized_price_unit=("normalized_price_unit", "first"),
            event_period=("event_period", "first"),
            source_units=("unit_id", "nunique"),
        )
    )
    if unit_level == "commodity_store":
        grouped["unit_id"] = grouped["store"].astype(str) + "::" + grouped["commodity"].astype(str)
    else:
        grouped["unit_id"] = grouped["commodity"].astype(str)
        grouped["store"] = "all_stores"
    return grouped


def build_balanced_panel(
    products: pd.DataFrame,
    event_date: str = "2024-06-24",
    frequency: str = "daily",
    min_units: int = 2,
    require_complete_units: bool = False,
    food_only: bool = True,
    exclude_unknown: bool = True,
    include_dairy_as_treated: bool = True,
    min_pre_periods: int = 1,
    min_post_periods: int = 1,
    max_pre_periods: int | None = None,
    max_post_periods: int | None = None,
    symmetric_window: bool = False,
    unit_level: str = "commodity_store",
) -> PanelResult:
    event = pd.Timestamp(event_date)
    filtered = _filter_analysis_sample(products, food_only, exclude_unknown, include_dairy_as_treated)
    data = _aggregate_unit_level(_aggregate(filtered, frequency, event), unit_level)
    if data.empty:
        raise ValueError("No food/control treatment sample remains after filters.")
    periods = sorted(pd.to_datetime(data["period"].unique()))
    event_period = pd.Timestamp(data["event_period"].iloc[0])
    pre = [period for period in periods if period < event_period]
    post = [period for period in periods if period > event_period]
    if len(pre) < min_pre_periods or len(post) < min_post_periods:
        raise ValueError("Insufficient data coverage: need at least one pre and one post period.")
    if symmetric_window:
        window = min(len(pre), len(post))
        selected_pre = pre[-window:]
        selected_post = post[:window]
    else:
        selected_pre = pre[-max_pre_periods:] if max_pre_periods else pre
        selected_post = post[:max_post_periods] if max_post_periods else post
        window = min(len(selected_pre), len(selected_post))
    selected_periods = set(selected_pre + selected_post)
    selected = data[data["period"].isin(selected_periods)].copy()
    required_count = len(selected_periods)
    if require_complete_units:
        valid_units = selected.groupby("unit_id")["period"].nunique().loc[lambda series: series == required_count].index
    else:
        unit_support = selected.assign(is_pre=selected["period"] < event_period, is_post=selected["period"] > event_period)
        valid_units = (
            unit_support.groupby("unit_id")
            .agg(pre=("is_pre", "sum"), post=("is_post", "sum"))
            .loc[lambda frame: (frame["pre"] >= min_pre_periods) & (frame["post"] >= min_post_periods)]
            .index
        )
    selected = selected[selected["unit_id"].isin(valid_units)].copy()
    if selected["unit_id"].nunique() < min_units:
        raise ValueError("Insufficient balanced units after applying symmetric window.")
    if not selected["treated"].astype(bool).any():
        raise ValueError("No treated food units remain after filters.")
    if selected["treated"].astype(bool).all():
        raise ValueError("No control food units remain after filters.")
    selected["relative_time"] = selected["period"].map(lambda value: _relative_time(pd.Timestamp(value), event_period, frequency)).astype(int)
    selected["post"] = selected["relative_time"] > 0
    selected["treated"] = selected["treated"].astype(bool)
    selected["did"] = selected["treated"].astype(int) * selected["post"].astype(int)
    selected["log_price"] = np.log(selected["price"])
    selected["event_date"] = event.date().isoformat()
    selected["frequency"] = frequency
    diagnostics = {
        "frequency": frequency,
        "event_date": event.date().isoformat(),
        "balanced_periods_pre": len(selected_pre),
        "balanced_periods_post": len(selected_post),
        "symmetric_window": str(symmetric_window),
        "require_complete_units": str(require_complete_units),
        "food_only": str(food_only),
        "exclude_unknown": str(exclude_unknown),
        "include_dairy_as_treated": str(include_dairy_as_treated),
        "unit_level": unit_level,
        "min_pre_periods": int(min_pre_periods),
        "min_post_periods": int(min_post_periods),
        "units": int(selected["unit_id"].nunique()),
        "rows": int(len(selected)),
        "treated_units": int(selected.loc[selected["treated"], "unit_id"].nunique()),
        "control_units": int(selected.loc[~selected["treated"], "unit_id"].nunique()),
        "commodities": int(selected["commodity"].nunique()),
        "stores": int(selected["store"].nunique()),
    }
    return PanelResult(selected.sort_values(["unit_id", "period"]).reset_index(drop=True), diagnostics)


def write_panel(products_path: Path, panel_path: Path, diagnostics_path: Path, **kwargs: object) -> PanelResult:
    products = pd.read_csv(products_path, parse_dates=["date"], dtype={"product_id": str}, low_memory=False)
    result = build_balanced_panel(products, **kwargs)
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    result.panel.to_csv(panel_path, index=False)
    pd.DataFrame([result.diagnostics]).to_csv(diagnostics_path, index=False)
    diagnostics_dir = diagnostics_path.parent
    result.panel.groupby(["commodity", "treatment_group", "treated"], as_index=False).agg(
        units=("unit_id", "nunique"),
        rows=("unit_id", "size"),
    ).to_csv(diagnostics_dir / "panel_commodity_counts.csv", index=False)
    result.panel.groupby(["relative_time", "treated"], as_index=False).agg(
        units=("unit_id", "nunique"),
        rows=("unit_id", "size"),
    ).to_csv(diagnostics_dir / "panel_period_support.csv", index=False)
    return result
