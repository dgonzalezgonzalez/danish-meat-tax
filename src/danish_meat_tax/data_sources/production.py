"""Download and reshape official production records; estimation belongs to Stata."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


PRODUCTION_URLS = {
    "statbank_pris04_total.csv": (
        "https://api.statbank.dk/v1/data/PRIS04/CSV?VAREGR=000005&ENHED=100&Tid=*&lang=en"
    ),
    "eurostat_bovine_slaughter_2020_2025.json": (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "apro_mt_pwgtm?lang=EN&meat=B1000&sinceTimePeriod=2020-01&untilTimePeriod=2025-09"
    ),
    "statbank_ani41.csv": (
        "https://api.statbank.dk/v1/data/ANI41/CSV?DYRKAT=*&ENHED=PROD,SLAGEKS&Tid=*&lang=en"
    ),
    "statbank_ani41_metadata.json": "https://api.statbank.dk/v1/tableinfo/ANI41?lang=en",
}


def download_production(raw_dir: Path, refresh: bool = False) -> None:
    """Cache official payloads and record retrieval provenance."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "production_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for filename, url in PRODUCTION_URLS.items():
        destination = raw_dir / filename
        if refresh or not destination.exists():
            with urlopen(url, timeout=120) as response:
                payload = response.read()
            destination.write_bytes(payload)
            retrieved = datetime.now(timezone.utc).isoformat()
        else:
            payload = destination.read_bytes()
            retrieved = manifest.get(filename, {}).get("retrieved_utc")
        manifest[filename] = {
            "url": url, "retrieved_utc": retrieved,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def jsonstat_rows(payload: dict) -> list[dict]:
    """Decode JSON-stat row-major cells, retaining missing values and flags."""
    ids, sizes = payload["id"], payload["size"]
    categories = []
    for dimension in ids:
        index = payload["dimension"][dimension]["category"]["index"]
        categories.append(sorted(index, key=index.get) if isinstance(index, dict) else index)
    values, flags = payload.get("value", {}), payload.get("status", {})
    rows = []
    for flat, coordinates in enumerate(itertools.product(*(range(n) for n in sizes))):
        row = {dim: categories[j][coordinates[j]] for j, dim in enumerate(ids)}
        row["value"] = values.get(str(flat)) if isinstance(values, dict) else values[flat]
        row["flag"] = flags.get(str(flat), "") if isinstance(flags, dict) else flags[flat]
        rows.append(row)
    return rows


def prepare_production_panel(root: Path) -> Path:
    """Write source cells unchanged; Stata selects units, windows and outcomes."""
    source = root / "data/raw/eurostat_bovine_slaughter_2020_2025.json"
    rows = jsonstat_rows(json.loads(source.read_text(encoding="utf-8-sig")))
    destination = root / "data/processed/eurostat_bovine_slaughter.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return destination
