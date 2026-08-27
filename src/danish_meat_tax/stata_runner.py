from __future__ import annotations

import os
from pathlib import Path
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
