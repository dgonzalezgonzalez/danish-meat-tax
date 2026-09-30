"""Rebuild the core official-price and bovine-production evidence only.

This target needs the frozen official inputs and Stata, but no grocery history,
Commission trade extract, or conditional carbon-accounting inputs.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from danish_meat_tax.data_sources.hicp import prepare_hicp_panel
from danish_meat_tax.data_sources.production import prepare_production_panel
from danish_meat_tax.stata_runner import run_stata


ROOT = Path(__file__).resolve().parents[1]
NON_CORE_INPUTS = {
    "heissepreise_20260609T092146Z.json",
    "eu_beef_trade_data_en.csv",
    "statbank_pris04_total.csv",
}


def restore_frozen_official_inputs(root: Path) -> None:
    """Restore absent inputs from the hash-checked, versioned official deposit."""
    manifest = json.loads((root / "data/reference/replication_input_manifest.json").read_text(encoding="utf-8"))
    records = [record for record in manifest["files"]
               if Path(record["path"]).name not in NON_CORE_INPUTS]
    cache = root / "data/reference/frozen_official"
    if any(not (cache / Path(record["path"]).name).is_file() for record in records):
        deposit = json.loads((cache / "archive_manifest.json").read_text(encoding="utf-8"))
        request = urllib.request.Request(deposit["url"], headers={"User-Agent": "danish-meat-tax-replication"})
        with urllib.request.urlopen(request, timeout=60) as stream:
            payload = stream.read()
        if len(payload) != deposit["bytes"] or hashlib.sha256(payload).hexdigest() != deposit["sha256"]:
            raise RuntimeError("Frozen official deposit checksum mismatch")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            blobs = {Path(record["path"]).name: archive.read(Path(record["path"]).name)
                     for record in records}
        for record in records:
            name = Path(record["path"]).name
            blob = blobs[name]
            if len(blob) != record["bytes"] or hashlib.sha256(blob).hexdigest() != record["sha256"]:
                raise RuntimeError(f"Frozen official deposit member mismatch: {name}")
        cache.mkdir(parents=True, exist_ok=True)
        for name, blob in blobs.items():
            if not (cache / name).exists():
                (cache / name).write_bytes(blob)
    for record in records:
        target = root / record["path"]
        source = cache / target.name
        if not source.is_file() or source.stat().st_size != record["bytes"]:
            raise RuntimeError(f"Missing or incomplete frozen official input: {source}")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            raise RuntimeError(f"Frozen official input hash mismatch: {source}")
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


def main() -> None:
    restore_frozen_official_inputs(ROOT)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_inputs.py"), "--official-only"],
        cwd=ROOT, check=True,
    )
    prepare_hicp_panel(ROOT)
    prepare_production_panel(ROOT)
    for name in (
        "check_dependencies.do", "aggregate_analysis.do", "aggregate_omit_june.do",
        "country_sdid.do", "country_sdid_diagnostics.do", "production_analysis.do",
    ):
        run_stata(ROOT, Path("scripts/stata") / name)
    print("Official price and production analyses rebuilt; grocery and calibration are separate.")


if __name__ == "__main__":
    main()
