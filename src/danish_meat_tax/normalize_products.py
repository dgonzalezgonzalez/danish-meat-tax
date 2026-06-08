from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .data_sources.heissepreise import extract_records
from .policy_taxonomy import classify_product


def load_raw_records(raw_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    try:
        return extract_records(payload)
    except ValueError as exc:
        raise ValueError(f"Unsupported raw data file shape: {raw_path}") from exc


def _first(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def normalize_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    assignment_cache: dict[tuple[str, str], Any] = {}
    for index, row in enumerate(records):
        name = _first(row, "product_name", "name", "title", "label")
        price = _first(row, "price", "current_price", "amount", "unit_price")
        observed_date = _first(row, "date", "observed_at", "timestamp", "valid_from")
        store = _first(row, "store", "supermarket", "chain", "merchant")
        category = _first(row, "category", "department", "group")
        product_id = _first(row, "product_id", "id", "sku", "ean")
        reason = ""
        try:
            price_float = float(str(price).replace(",", "."))
        except (TypeError, ValueError):
            price_float = float("nan")
            reason = "invalid_price"
        if pd.notna(price_float) and price_float <= 0:
            reason = "nonpositive_price" if not reason else f"{reason};nonpositive_price"
        try:
            parsed_date = date.fromisoformat(str(observed_date)[:10])
        except (TypeError, ValueError):
            parsed_date = None
        if parsed_date is None:
            reason = "invalid_date" if not reason else f"{reason};invalid_date"
        name_text = str(name or "")
        category_text = str(category or "")
        cache_key = (name_text, category_text)
        assignment = assignment_cache.get(cache_key)
        if assignment is None:
            assignment = classify_product(name_text, category_text)
            assignment_cache[cache_key] = assignment
        rows.append(
            {
                "row_id": index,
                "date": parsed_date.isoformat() if parsed_date is not None else "",
                "store": str(store or "unknown"),
                "product_id": str(product_id or f"row_{index}"),
                "product_name": name_text,
                "category_raw": category_text,
                "price": price_float,
                "currency": str(_first(row, "currency") or "DKK"),
                "unit": str(_first(row, "unit", "package_size") or ""),
                "commodity": assignment.commodity,
                "treated": assignment.treated,
                "treatment_group": assignment.treatment_group,
                "policy_confidence": assignment.policy_confidence,
                "matched_terms": "|".join(assignment.matched_terms),
                "quality_flag": reason or "ok",
            }
        )
    frame = pd.DataFrame(rows)
    frame = frame[(frame["quality_flag"] == "ok") & frame["price"].notna() & (frame["price"] > 0) & (frame["date"] != "")]
    frame["unit_id"] = frame["store"] + "::" + frame["product_id"]
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values(["unit_id", "date"]).reset_index(drop=True)


def build_processed_products(raw_path: Path, output_path: Path) -> pd.DataFrame:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = normalize_records(load_raw_records(raw_path))
    frame.to_csv(output_path, index=False)
    return frame
