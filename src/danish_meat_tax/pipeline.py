from __future__ import annotations

import argparse
from pathlib import Path

from .config import EVENT_DATE, PipelinePaths
from .data_sources.heissepreise import download_json, write_fixture
from .estimators import run_estimations
from .normalize_products import build_processed_products
from .output import make_outputs
from .panel_builder import write_panel


def _latest_raw_path(paths: PipelinePaths) -> Path:
    fixture_path = paths.raw_dir / "heissepreise_fixture.json"
    candidates = sorted(paths.raw_dir.glob("heissepreise_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else fixture_path


def run_stage(stage: str, paths: PipelinePaths, fixture: bool, frequency: str) -> None:
    paths.ensure()
    raw_path = _latest_raw_path(paths)
    products_path = paths.processed_dir / "products.csv"
    panel_path = paths.processed_dir / "commodity_panel.csv"
    diagnostics_path = paths.diagnostics_dir / "panel_balance.csv"

    if stage in {"download", "all"}:
        result = write_fixture(paths.raw_dir) if fixture else download_json(paths.raw_dir)
        raw_path = result.path
        print(f"download: {result.record_count} records -> {result.path}")
    if stage in {"process", "all"}:
        raw_path = raw_path if raw_path.exists() else _latest_raw_path(paths)
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw data missing: {raw_path}. Run download first or use --fixture.")
        products = build_processed_products(raw_path, products_path)
        print(f"process: {len(products)} rows -> {products_path}")
    if stage in {"panel", "all"}:
        result = write_panel(
            products_path,
            panel_path,
            diagnostics_path,
            event_date=EVENT_DATE,
            frequency=frequency,
        )
        print(f"panel: {result.diagnostics['rows']} rows -> {panel_path}")
    if stage in {"estimate", "all"}:
        results = run_estimations(panel_path, paths.models_dir)
        print("estimate: " + ", ".join(results.keys()) + f" -> {paths.models_dir}")
    if stage in {"outputs", "all"}:
        outputs = make_outputs(paths.models_dir, paths.figures_dir, paths.tables_dir)
        print("outputs: " + ", ".join(str(path) for path in outputs.values()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Danish meat tax announcement price-effects pipeline")
    parser.add_argument(
        "stage",
        choices=["download", "process", "panel", "estimate", "outputs", "all"],
        help="Pipeline stage to run.",
    )
    parser.add_argument("--root", type=Path, default=Path("."), help="Project root path.")
    parser.add_argument("--fixture", action="store_true", help="Use deterministic offline fixture price data.")
    parser.add_argument("--frequency", choices=["daily", "weekly"], default="daily", help="Panel aggregation frequency.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_stage(args.stage, PipelinePaths(args.root), fixture=args.fixture, frequency=args.frequency)
