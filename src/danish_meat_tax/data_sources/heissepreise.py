from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from ..config import DEFAULT_SOURCE_URLS


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    source_url: str
    record_count: int
    fixture: bool = False


def _fixture_records() -> list[dict[str, Any]]:
    products = [
        ("beef_minced", "Netto", "Hakket oksekød 8-12%", "beef", 45.0, 1.10),
        ("pork_chop", "Netto", "Svinekotelet", "pork", 35.0, 1.06),
        ("lamb_leg", "Netto", "Lammekølle", "lamb", 70.0, 1.05),
        ("chicken_breast", "Netto", "Kyllingebryst", "poultry", 42.0, 1.02),
        ("cod_fillet", "Netto", "Torskefilet", "fish", 55.0, 1.00),
        ("milk", "Netto", "Letmælk 1 liter", "dairy", 12.0, 1.00),
        ("beef_minced", "Føtex", "Hakket oksekød 8-12%", "beef", 47.0, 1.09),
        ("pork_chop", "Føtex", "Svinekotelet", "pork", 37.0, 1.05),
        ("lamb_leg", "Føtex", "Lammekølle", "lamb", 74.0, 1.04),
        ("chicken_breast", "Føtex", "Kyllingebryst", "poultry", 44.0, 1.01),
        ("cod_fillet", "Føtex", "Torskefilet", "fish", 58.0, 1.00),
        ("milk", "Føtex", "Letmælk 1 liter", "dairy", 13.0, 1.00),
    ]
    start = date(2024, 6, 10)
    event = date(2024, 6, 24)
    rows: list[dict[str, Any]] = []
    for offset in range(29):
        current = start + timedelta(days=offset)
        if current == event:
            continue
        for product_id, store, name, category, base, post_multiplier in products:
            trend = 1 + 0.001 * offset
            multiplier = post_multiplier if current > event else 1.0
            rows.append(
                {
                    "date": current.isoformat(),
                    "store": store,
                    "product_id": f"{store.lower()}_{product_id}",
                    "product_name": name,
                    "category": category,
                    "price": round(base * trend * multiplier, 2),
                    "currency": "DKK",
                    "unit": "package",
                    "source": "fixture",
                }
            )
    return rows


def write_fixture(raw_dir: Path) -> DownloadResult:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / "heissepreise_fixture.json"
    payload = {
        "source": "fixture",
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "records": _fixture_records(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return DownloadResult(path=path, source_url="fixture", record_count=len(payload["records"]), fixture=True)


def download_json(raw_dir: Path, source_urls: tuple[str, ...] = DEFAULT_SOURCE_URLS, timeout: int = 30) -> DownloadResult:
    raw_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in source_urls:
        try:
            with urlopen(url, timeout=timeout) as response:
                data = response.read()
            payload = json.loads(data.decode("utf-8"))
            records = extract_source_items(payload)
            path = raw_dir / f"heissepreise_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
            envelope = {
                "source": url,
                "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "records": records,
            }
            path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
            return DownloadResult(path=path, source_url=url, record_count=sum(len(row.get("priceHistory") or [None]) for row in records))
        except Exception as exc:  # noqa: BLE001 - preserve source-specific failure detail.
            errors.append(f"{url}: {exc}")
    raise RuntimeError("Could not download structured price data. Tried: " + " | ".join(errors))


def extract_source_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("records", "products", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        flattened: list[dict[str, Any]] = []
        for store, value in payload.items():
            if isinstance(value, list):
                for row in value:
                    if isinstance(row, dict):
                        item = dict(row)
                        item.setdefault("store", store)
                        flattened.append(item)
        if flattened:
            return flattened
    raise ValueError("Unsupported price-data JSON shape")


def extract_records(payload: Any) -> list[dict[str, Any]]:
    def expanded(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows:
            history = row.get("priceHistory")
            base = {key: value for key, value in row.items() if key != "priceHistory"}
            if isinstance(history, list) and history:
                for entry in history:
                    if not isinstance(entry, dict):
                        continue
                    item = dict(base)
                    item["date"] = entry.get("date")
                    item["price"] = entry.get("price", base.get("price"))
                    item["quantity"] = entry.get("quantity", base.get("quantity"))
                    item["unit"] = entry.get("unit", base.get("unit"))
                    item["price_history_observation"] = True
                    out.append(item)
            else:
                item = dict(base)
                item["price_history_observation"] = False
                out.append(item)
        return out

    if isinstance(payload, list):
        return expanded([row for row in payload if isinstance(row, dict)])
    if isinstance(payload, dict):
        return expanded(extract_source_items(payload))
    raise ValueError("Unsupported price-data JSON shape")
