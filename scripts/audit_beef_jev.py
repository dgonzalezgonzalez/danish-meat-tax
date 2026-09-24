"""Audit rule-labeled beef names with Jev; never treat model labels as ground truth.

Requires TYPESAFE_API_KEY in the process environment, or --key-stdin for an
ephemeral key. Sends product names from the public grocery snapshot to TypeSafe.
The CSV records model labels and probabilities. The frozen estimation screen
requires a core-beef label with probability at least 0.90 and applies explicit
manual exclusions for identified false positives.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
CRITERIA = {
    "core_beef": "Human food: plain beef or veal meat, including fresh, frozen, minced, steaks and unseasoned cuts; no other animal meat or prepared dish.",
    "prepared_beef": "Human food containing beef or veal as a main ingredient, but cooked, seasoned, cured or processed beyond a plain cut.",
    "mixed_food": "Mixed dish, sauce, snack, noodles or flavoring; beef may be only one ingredient or flavor.",
    "plant_product": "Vegan or plant-based substitute, even if the label says beef or meat.",
    "animal_feed": "Pet food, animal feed, treats or chews; not food for human consumption.",
    "other": "No reliable evidence of a human beef or veal meat product; includes unrelated goods and unclear names.",
}


def candidates(path: Path) -> list[tuple[str, int]]:
    counts: dict[str, set[str]] = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["treatment_group"] == "beef":
                counts.setdefault(row["product_name"], set()).add(row["unit_id"])
    return sorted((name, len(units)) for name, units in counts.items())


def classify_batch(key: str, names: list[str]) -> dict:
    state = {"products": [{"name": name} for name in names]}
    questions = {
        f"p{i}": {
            "type": "choice",
            "instructions": (
                f"Which single category best describes `products[{i}].name`? "
                "Use the product identity, not incidental recipe suggestions in its description. "
                "When contents are unclear, choose other."
            ),
            "criteria": CRITERIA,
        }
        for i in range(len(names))
    }
    payload = json.dumps({"state": state, "model": MODEL, "questions": questions}, ensure_ascii=False).encode("utf-8")
    request = Request(
        API_URL, data=payload, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urlopen(request, timeout=120) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code not in (429, 529) or attempt == 3:
                raise RuntimeError(f"TypeSafe HTTP {exc.code}: {exc.read(500).decode('utf-8', errors='replace')}") from None
            time.sleep(2 ** attempt)
        except URLError as exc:
            if attempt == 3:
                raise RuntimeError(f"TypeSafe connection failed: {exc.reason}") from None
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=Path("data/processed/commodity_panel.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/reference/grocery_beef_jev_audit.csv"))
    parser.add_argument("--key-stdin", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    key = getpass.getpass("TypeSafe API key: ").strip() if args.key_stdin else os.environ.get("TYPESAFE_API_KEY", "")
    if not key:
        raise SystemExit("TYPESAFE_API_KEY missing")
    names = candidates(args.panel)
    if args.limit is not None:
        names = names[: args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    previous: dict[str, dict] = {}
    if args.output.exists():
        with args.output.open(newline="", encoding="utf-8") as stream:
            previous = {row["product_name"]: row for row in csv.DictReader(stream)}
    fields = ["product_name", "unit_count", "jev_label", "core_probability", "confidence", "model"]
    pending = [(name, units) for name, units in names if name not in previous]
    for offset in range(0, len(pending), 20):
        batch = pending[offset : offset + 20]
        response = classify_batch(key, [name for name, _ in batch])
        for index, (name, units) in enumerate(batch):
            answer = response["answers"][f"p{index}"]
            previous[name] = {
                "product_name": name,
                "unit_count": units,
                "jev_label": answer["choice"],
                "core_probability": answer["probabilities"]["core_beef"],
                "confidence": answer["confidence"],
                "model": response["model"],
            }
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(previous[name] for name in sorted(previous))
        print(f"audited {min(offset + 20, len(pending))}/{len(pending)} pending names", flush=True)


if __name__ == "__main__":
    main()
