"""Download if absent and reshape the country-level HICP robustness input."""
from pathlib import Path

from danish_meat_tax.data_sources.hicp import download_hicp, prepare_hicp_panel


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    download_hicp(root / "data/raw")
    print(prepare_hicp_panel(root))
