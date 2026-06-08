from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


EVENT_DATE = "2024-06-24"
DEFAULT_SOURCE_URLS = (
    "https://dagligepriser.dk/data/latest-canonical.json",
)


@dataclass(frozen=True)
class PipelinePaths:
    root: Path = Path(".")

    @property
    def raw_dir(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def figures_dir(self) -> Path:
        return self.root / "outputs" / "figures"

    @property
    def tables_dir(self) -> Path:
        return self.root / "outputs" / "tables"

    @property
    def models_dir(self) -> Path:
        return self.root / "outputs" / "models"

    @property
    def diagnostics_dir(self) -> Path:
        return self.root / "outputs" / "diagnostics"

    def ensure(self) -> None:
        for directory in (
            self.raw_dir,
            self.processed_dir,
            self.figures_dir,
            self.tables_dir,
            self.models_dir,
            self.diagnostics_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
