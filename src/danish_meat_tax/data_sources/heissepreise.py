from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import hashlib
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
    cached: bool = False


CACHE_MANIFEST = "heissepreise_cache_manifest.json"


def _fixture_records() -> list[dict[str, Any]]:
    products = [
        ("beef_minced", "Netto", "Hakket oksekoed 500 g", "beef", 45.0, 1.10, 500, "g"),
        ("pork_chop", "Netto", "Svinekotelet 500 g", "pork", 35.0, 1.06, 500, "g"),
        ("lamb_leg", "Netto", "Lammekolle 1 kg", "lamb", 70.0, 1.05, 1, "kg"),
        ("chicken_breast", "Netto", "Kyllingebryst 500 g", "poultry", 42.0, 1.02, 500, "g"),
        ("cod_fillet", "Netto", "Torskefilet 400 g", "fish", 55.0, 1.00, 400, "g"),
        ("milk", "Netto", "Letmaelk 1 liter", "dairy", 12.0, 1.00, 1, "l"),
        ("bread", "Netto", "Rugbroed 500 g", "bread", 18.0, 1.00, 500, "g"),
        ("beef_minced", "Fotex", "Hakket oksekoed 500 g", "beef", 47.0, 1.09, 500, "g"),
        ("pork_chop", "Fotex", "Svinekotelet 500 g", "pork", 37.0, 1.05, 500, "g"),
        ("lamb_leg", "Fotex", "Lammekolle 1 kg", "lamb", 74.0, 1.04, 1, "kg"),
        ("chicken_breast", "Fotex", "Kyllingebryst 500 g", "poultry", 44.0, 1.01, 500, "g"),
        ("cod_fillet", "Fotex", "Torskefilet 400 g", "fish", 58.0, 1.00, 400, "g"),
        ("milk", "Fotex", "Letmaelk 1 liter", "dairy", 13.0, 1.00, 1, "l"),
        ("bread", "Fotex", "Rugbroed 500 g", "bread", 19.0, 1.00, 500, "g"),
    ]
    start = date(2024, 6, 10)
    event = date(2024, 6, 24)
    rows: list[dict[str, Any]] = []
    for offset in range(29):
        current = start + timedelta(days=offset)
        if current == event:
            continue
        for product_id, store, name, category, base, post_multiplier, quantity, unit in products:
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
                    "quantity": quantity,
                    "unit": unit,
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


def _manifest_path(raw_dir: Path) -> Path:
    return raw_dir / CACHE_MANIFEST


def _read_manifest(raw_dir: Path) -> dict[str, Any] | None:
    path = _manifest_path(raw_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _cached_result(raw_dir: Path, max_age_days: int | None, source_urls: tuple[str, ...]) -> DownloadResult | None:
    manifest = _read_manifest(raw_dir)
    if not manifest:
        return None
    source_url = str(manifest.get("source_url", ""))
    if source_url and source_url not in source_urls:
        return None
    path = Path(str(manifest.get("path", "")))
    if not path.is_absolute():
        path = raw_dir / path
    if not path.exists():
        return None
    if max_age_days is not None:
        try:
            retrieved = datetime.fromisoformat(str(manifest["retrieved_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError):
            return None
        age = datetime.now(UTC) - retrieved
        if age.days > max_age_days:
            return None
    return DownloadResult(
        path=path,
        source_url=source_url or "cache",
        record_count=int(manifest.get("record_count", 0)),
        cached=True,
    )


def _write_manifest(raw_dir: Path, result: DownloadResult, content_hash: str) -> None:
    payload = {
        "source_url": result.source_url,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "path": result.path.name,
        "record_count": result.record_count,
        "sha256": content_hash,
    }
    _manifest_path(raw_dir).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def download_json(
    raw_dir: Path,
    source_urls: tuple[str, ...] = DEFAULT_SOURCE_URLS,
    timeout: int = 30,
    refresh: bool = False,
    max_age_days: int | None = None,
) -> DownloadResult:
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not refresh:
        cached = _cached_result(raw_dir, max_age_days, source_urls)
        if cached is not None:
            return cached
    errors: list[str] = []
    for url in source_urls:
        try:
            with urlopen(url, timeout=timeout) as response:
                data = response.read()
            content_hash = hashlib.sha256(data).hexdigest()
            payload = json.loads(data.decode("utf-8"))
            records = extract_source_items(payload)
            path = raw_dir / f"heissepreise_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
            envelope = {
                "source": url,
                "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "records": records,
            }
            path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
            result = DownloadResult(path=path, source_url=url, record_count=sum(len(row.get("priceHistory") or [None]) for row in records))
            _write_manifest(raw_dir, result, content_hash)
            return result
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
