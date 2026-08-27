"""Convert preprocessing outputs into compact, Stata-native input files.

This module performs no estimation.  It exists because product descriptions in
the source panel can contain embedded newlines that are valid CSV but exceed
Stata's quoted-row parser.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from danish_meat_tax.stata_runner import prepare_micro_panel  # noqa: E402


if __name__ == "__main__":
    print(
        prepare_micro_panel(
            ROOT / "data" / "processed" / "commodity_panel.csv",
            ROOT / "data" / "processed" / "commodity_panel_stata.dta",
        )
    )
