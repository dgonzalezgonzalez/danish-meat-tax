from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
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


def _to_float(value: Any) -> float | None:
    try:
        parsed = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return parsed if pd.notna(parsed) else None


def _normalize_unit(unit: Any) -> str:
    text = str(unit or "").casefold().strip()
    replacements = {"æ": "ae", "ø": "o", "å": "aa", "Ã¦": "ae", "Ã¸": "o", "Ã¥": "aa"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(".", "")
    aliases = {
        "kg": "kg",
        "kilo": "kg",
        "kilogram": "kg",
        "g": "g",
        "gram": "g",
        "l": "l",
        "liter": "l",
        "litre": "l",
        "ml": "ml",
        "cl": "cl",
        "stk": "stk",
        "styk": "stk",
        "pcs": "stk",
        "pack": "stk",
        "pak": "stk",
    }
    return aliases.get(text, text)


def _parse_quantity_from_name(name: str) -> tuple[float | None, str]:
    text = name.casefold().replace(",", ".")
    patterns = (
        r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|kilo|kilogram)\b",
        r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>g|gram)\b",
        r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>l|liter|litre)\b",
        r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>ml|cl)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group("qty")), _normalize_unit(match.group("unit"))
    return None, ""


def normalize_price(price: float, quantity: Any, unit: Any, product_name: str) -> tuple[float | None, str, float | None, str, str]:
    quantity_value = _to_float(quantity)
    quantity_unit = _normalize_unit(unit)
    if quantity_value is None or quantity_value <= 0 or quantity_unit in {"", "stk", "pcs", "pak"}:
        parsed_qty, parsed_unit = _parse_quantity_from_name(product_name)
        if parsed_qty is not None:
            quantity_value = parsed_qty
            quantity_unit = parsed_unit
    if quantity_value is None or quantity_value <= 0:
        return None, "", quantity_value, quantity_unit, "missing_unit"
    if quantity_unit == "g":
        return price / (quantity_value / 1000), "dkk_per_kg", quantity_value, quantity_unit, "ok"
    if quantity_unit == "kg":
        return price / quantity_value, "dkk_per_kg", quantity_value, quantity_unit, "ok"
    if quantity_unit == "ml":
        return price / (quantity_value / 1000), "dkk_per_liter", quantity_value, quantity_unit, "ok"
    if quantity_unit == "cl":
        return price / (quantity_value / 100), "dkk_per_liter", quantity_value, quantity_unit, "ok"
    if quantity_unit == "l":
        return price / quantity_value, "dkk_per_liter", quantity_value, quantity_unit, "ok"
    return None, "", quantity_value, quantity_unit, "unsupported_unit"


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
        price_float = _to_float(price)
        if price_float is None:
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
        quantity = _first(row, "quantity", "amount_quantity", "size")
        raw_unit = _first(row, "unit", "package_size")
        normalized_price, normalized_unit, quantity_value, quantity_unit, normalization_status = normalize_price(
            price_float,
            quantity,
            raw_unit,
            name_text,
        )
        rows.append(
            {
                "row_id": index,
                "date": parsed_date.isoformat() if parsed_date is not None else "",
                "store": str(store or "unknown"),
                "product_id": str(product_id or f"row_{index}"),
                "product_name": name_text,
                "category_raw": category_text,
                "price": price_float,
                "raw_price": price_float,
                "currency": str(_first(row, "currency") or "DKK"),
                "unit": str(raw_unit or ""),
                "raw_unit": str(raw_unit or ""),
                "quantity_value": quantity_value,
                "quantity_unit": quantity_unit,
                "normalized_price": normalized_price,
                "normalized_price_unit": normalized_unit,
                "normalization_status": normalization_status,
                "commodity": assignment.commodity,
                "treated": assignment.treated,
                "treatment_group": assignment.treatment_group,
                "policy_confidence": assignment.policy_confidence,
                "matched_terms": "|".join(assignment.matched_terms),
                "food_status": assignment.food_status,
                "analysis_role": assignment.analysis_role,
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
