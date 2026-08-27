from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen


PRIS01_DATA_URL = "https://api.statbank.dk/v1/data/PRIS01/CSV?VAREGR=*&ENHED=100&Tid=*"
PRIS01_METADATA_URL = "https://api.statbank.dk/v1/tableinfo/PRIS01?lang=en"


@dataclass(frozen=True)
class StatbankFiles:
    data: Path
    metadata: Path
    cached: bool


def _download(url: str, destination: Path) -> None:
    with urlopen(url, timeout=120) as response:  # noqa: S310 - fixed official endpoint
        payload = response.read()
    destination.write_bytes(payload)


def download_pris01(raw_dir: Path, refresh: bool = False) -> StatbankFiles:
    """Download the official PRIS01 CPI table and its metadata."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    data_path = raw_dir / "statbank_pris01.csv"
    metadata_path = raw_dir / "statbank_pris01_metadata.json"
    cached = data_path.exists() and metadata_path.exists() and not refresh
    if not cached:
        _download(PRIS01_DATA_URL, data_path)
        _download(PRIS01_METADATA_URL, metadata_path)
    return StatbankFiles(data=data_path, metadata=metadata_path, cached=cached)
