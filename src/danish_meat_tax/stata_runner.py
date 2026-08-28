from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pandas as pd


STATA_CANDIDATES = (
    Path(r"C:\Program Files\StataNow19\StataMP-64.exe"),
    Path(r"C:\Program Files\Stata19\StataMP-64.exe"),
    Path(r"C:\Program Files\Stata18\StataMP-64.exe"),
)


def prepare_micro_panel(panel_path: Path, destination: Path) -> Path:
    """Convert preprocessing output to a compact Stata file; no estimation."""
    columns = [
        "unit_id",
        "period",
        "price",
        "store",
        "commodity",
        "treated",
        "treatment_group",
        "relative_time",
        "did",
        "log_price",
    ]
    panel = pd.read_csv(panel_path, usecols=columns, low_memory=False)
    for column in ("unit_id", "period", "store", "commodity", "treatment_group"):
        panel[column] = panel[column].fillna("").astype(str)
    panel["treated"] = panel["treated"].astype("int8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    panel.to_stata(destination, write_index=False, version=118)
    return destination


def find_stata() -> Path:
    configured = os.environ.get("STATA_EXE")
    candidates = (Path(configured),) + STATA_CANDIDATES if configured else STATA_CANDIDATES
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Stata was not found. Set STATA_EXE to StataMP-64.exe.")


def run_stata(root: Path, do_file: Path) -> None:
    executable = find_stata()
    resolved_do = do_file if do_file.is_absolute() else root / do_file
    if not resolved_do.exists():
        raise FileNotFoundError(resolved_do)
    result = subprocess.run(
        [str(executable), "/e", "do", str(resolved_do)],
        cwd=root,
        check=False,
        timeout=1800,
    )
    if result.returncode:
        raise RuntimeError(f"Stata failed with exit code {result.returncode}: {resolved_do}")


def prepare_eu_robustness_panels(root: Path) -> None:
    """Build publication panels for country-price and beef-import robustness checks."""
    powershell = shutil.which("powershell.exe") or shutil.which("pwsh")
    if powershell is None:
        raise FileNotFoundError("PowerShell was not found; EU robustness panels cannot be prepared.")

    jobs = (
        (
            root / "data/raw/eu_beef_carcass_prices_2023m04_2025m09.json",
            root / "scripts/prepare_country_beef_panel.ps1",
        ),
        (
            root / "data/raw/eu_beef_trade_data_en.csv",
            root / "scripts/prepare_beef_trade_pair_panel.ps1",
        ),
    )
    for raw_path, script_path in jobs:
        if not raw_path.exists():
            raise FileNotFoundError(
                f"EU robustness input missing: {raw_path}. See docs for source and retrieval steps."
            )
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            cwd=root,
            check=False,
            timeout=1800,
        )
        if result.returncode:
            raise RuntimeError(
                f"EU robustness panel preparation failed with exit code {result.returncode}: {script_path}"
            )
