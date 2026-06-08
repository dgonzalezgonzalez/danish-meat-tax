from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PanelResult:
    panel: pd.DataFrame
    diagnostics: dict[str, int | str]


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
            price=("price", "mean"),
            store=("store", "first"),
            product_id=("product_id", "first"),
            product_name=("product_name", "first"),
            commodity=("commodity", "first"),
            treated=("treated", "first"),
            treatment_group=("treatment_group", "first"),
            policy_confidence=("policy_confidence", "first"),
            event_period=("event_period", "first"),
        )
    )
    return grouped


def build_balanced_panel(
    products: pd.DataFrame,
    event_date: str = "2024-06-24",
    frequency: str = "daily",
    min_units: int = 2,
    require_complete_units: bool = False,
) -> PanelResult:
    event = pd.Timestamp(event_date)
    data = _aggregate(products, frequency, event)
    periods = sorted(pd.to_datetime(data["period"].unique()))
    event_period = pd.Timestamp(data["event_period"].iloc[0])
    pre = [period for period in periods if period < event_period]
    post = [period for period in periods if period > event_period]
    window = min(len(pre), len(post))
    if window == 0:
        raise ValueError("Insufficient data coverage: need at least one pre and one post period.")
    selected_periods = set(pre[-window:] + post[:window])
    selected = data[data["period"].isin(selected_periods)].copy()
    required_count = 2 * window
    if require_complete_units:
        valid_units = selected.groupby("unit_id")["period"].nunique().loc[lambda series: series == required_count].index
    else:
        unit_support = selected.assign(is_pre=selected["period"] < event_period, is_post=selected["period"] > event_period)
        valid_units = (
            unit_support.groupby("unit_id")
            .agg(pre=("is_pre", "sum"), post=("is_post", "sum"))
            .loc[lambda frame: (frame["pre"] > 0) & (frame["post"] > 0)]
            .index
        )
    selected = selected[selected["unit_id"].isin(valid_units)].copy()
    if selected["unit_id"].nunique() < min_units:
        raise ValueError("Insufficient balanced units after applying symmetric window.")
    ordered_periods = sorted(pd.to_datetime(selected["period"].unique()))
    period_to_relative = {
        period: index - window if index < window else index - window + 1
        for index, period in enumerate(ordered_periods)
    }
    selected["relative_time"] = selected["period"].map(period_to_relative).astype(int)
    selected["post"] = selected["relative_time"] > 0
    selected["treated"] = selected["treated"].astype(bool)
    selected["did"] = selected["treated"].astype(int) * selected["post"].astype(int)
    selected["log_price"] = np.log(selected["price"])
    selected["event_date"] = event.date().isoformat()
    selected["frequency"] = frequency
    diagnostics = {
        "frequency": frequency,
        "event_date": event.date().isoformat(),
        "balanced_periods_pre": window,
        "balanced_periods_post": window,
        "require_complete_units": str(require_complete_units),
        "units": int(selected["unit_id"].nunique()),
        "rows": int(len(selected)),
        "treated_units": int(selected.loc[selected["treated"], "unit_id"].nunique()),
        "control_units": int(selected.loc[~selected["treated"], "unit_id"].nunique()),
    }
    return PanelResult(selected.sort_values(["unit_id", "period"]).reset_index(drop=True), diagnostics)


def write_panel(products_path: Path, panel_path: Path, diagnostics_path: Path, **kwargs: object) -> PanelResult:
    products = pd.read_csv(products_path, parse_dates=["date"], dtype={"product_id": str}, low_memory=False)
    result = build_balanced_panel(products, **kwargs)
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    result.panel.to_csv(panel_path, index=False)
    pd.DataFrame([result.diagnostics]).to_csv(diagnostics_path, index=False)
    return result
