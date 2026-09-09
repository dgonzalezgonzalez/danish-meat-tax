"""Render the publication surface figure after running the Stata master."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from danish_meat_tax.calibration_figures import render_calibration_surfaces

if __name__ == "__main__":
    print(render_calibration_surfaces(Path(__file__).resolve().parents[1]))
