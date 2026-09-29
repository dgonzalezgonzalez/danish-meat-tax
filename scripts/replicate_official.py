"""Rebuild the core official-price and bovine-production evidence only.

This target needs the frozen official inputs and Stata, but no grocery history,
Commission trade extract, or conditional carbon-accounting inputs.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from danish_meat_tax.data_sources.hicp import prepare_hicp_panel
from danish_meat_tax.data_sources.production import prepare_production_panel
from danish_meat_tax.stata_runner import run_stata


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
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
