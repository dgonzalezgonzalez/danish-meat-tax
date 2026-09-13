"""Cache and reshape complete official histories for author-review figures."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from danish_meat_tax.data_sources.hicp import EU27, HICP_URL
from danish_meat_tax.data_sources.production import PRODUCTION_URLS, jsonstat_rows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    queries = {
        "hicp": HICP_URL.replace("&sinceTimePeriod=2023-04", ""),
        "production": PRODUCTION_URLS["eurostat_bovine_slaughter_2020_2025.json"].replace("&sinceTimePeriod=2020-01", ""),
    }
    for name, url in queries.items():
        source = root / f"data/raw/eurostat_{name}_full_to_2025m09.json"
        if not source.exists():
            with urlopen(url, timeout=120) as response:
                payload = response.read()
            parsed = json.loads(payload)
            if parsed.get("class") != "dataset" or "value" not in parsed:
                raise ValueError("Expected Eurostat JSON-stat dataset")
            source.write_bytes(payload)
            source.with_suffix(".manifest.json").write_text(json.dumps({
                "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                "source_updated": parsed.get("updated"),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }, indent=2) + "\n", encoding="utf-8")
        rows = [row for row in jsonstat_rows(json.loads(source.read_text(encoding="utf-8"))) if row["geo"] in EU27]
        with (root / f"data/processed/sdid_max_{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
