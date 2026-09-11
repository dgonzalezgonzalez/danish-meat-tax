"""Retrieve and reshape Eurostat consumer-price indices; estimation is in Stata."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from .production import jsonstat_rows


HICP_FILENAME = "eurostat_beef_hicp_2023m04_2025m09.json"
# Frozen ECOICOP release covers the complete pre-2026 study window consistently.
HICP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "prc_hicp_midx?lang=EN&freq=M&unit=I15&coicop=CP01121"
    "&sinceTimePeriod=2023-04&untilTimePeriod=2025-09"
)
EU27 = frozenset("AT BE BG HR CY CZ DK EE FI FR DE EL HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split())


def download_hicp(raw_dir: Path, refresh: bool = False) -> Path:
    """Cache the exact response with its query, timestamp and checksum."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / HICP_FILENAME
    if destination.exists() and not refresh:
        return destination
    with urlopen(HICP_URL, timeout=120) as response:
        payload = response.read()
    parsed = json.loads(payload)
    if parsed.get("class") != "dataset" or "value" not in parsed:
        raise ValueError("Eurostat did not return a JSON-stat dataset")
    destination.write_bytes(payload)
    metadata = {
        "url": HICP_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source_updated": parsed.get("updated"),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    (raw_dir / "hicp_manifest.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    return destination


def prepare_hicp_panel(root: Path) -> Path:
    """Preserve EU27 source values and status flags, including missing cells."""
    source = root / "data/raw" / HICP_FILENAME
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = jsonstat_rows(payload)
    labels = payload["dimension"]["geo"]["category"].get("label", {})
    output = []
    for row in rows:
        if row["geo"] not in EU27:
            continue
        if (row["freq"], row["unit"], row["coicop"]) != ("M", "I15", "CP01121"):
            raise ValueError("Unexpected HICP frequency, unit or product")
        output.append({
            "geo": row["geo"], "country": labels.get(row["geo"], row["geo"]),
            "month": row["time"], "hicp": row["value"], "flag": row["flag"],
            "coicop": row["coicop"], "index_unit": row["unit"],
        })
    if not output:
        raise ValueError("No EU27 HICP observations returned")
    destination = root / "data/processed/eu_beef_hicp_country_month_panel.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    return destination
