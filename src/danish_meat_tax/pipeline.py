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


def run_stage(
    stage: str,
    paths: PipelinePaths,
    fixture: bool,
    frequency: str,
    require_complete_units: bool = False,
    refresh: bool = False,
    source_url: str | None = None,
    max_age_days: int | None = None,
    food_only: bool = True,
    exclude_unknown: bool = True,
    include_dairy_as_treated: bool = True,
    min_pre_periods: int = 1,
    min_post_periods: int = 1,
    max_pre_periods: int | None = None,
    max_post_periods: int | None = None,
    symmetric_window: bool = False,
    raw_path_override: Path | None = None,
    unit_level: str = "commodity_store",
) -> None:
    paths.ensure()
    raw_path = raw_path_override or _latest_raw_path(paths)
    products_path = paths.processed_dir / "products.csv"
    panel_path = paths.processed_dir / "commodity_panel.csv"
    diagnostics_path = paths.diagnostics_dir / "panel_balance.csv"

    if stage in {"download", "all"}:
        download_kwargs = {"refresh": refresh, "max_age_days": max_age_days}
        if source_url:
            download_kwargs["source_urls"] = (source_url,)
        result = write_fixture(paths.raw_dir) if fixture else download_json(paths.raw_dir, **download_kwargs)
        raw_path = result.path
        cache_note = " cached" if result.cached else ""
        print(f"download{cache_note}: {result.record_count} records -> {result.path}")
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
            require_complete_units=require_complete_units,
            food_only=food_only,
            exclude_unknown=exclude_unknown,
            include_dairy_as_treated=include_dairy_as_treated,
            min_pre_periods=min_pre_periods,
            min_post_periods=min_post_periods,
            max_pre_periods=max_pre_periods,
            max_post_periods=max_post_periods,
            symmetric_window=symmetric_window,
            unit_level=unit_level,
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
    parser.add_argument(
        "--require-complete-units",
        action="store_true",
        help="Require each retained unit to appear in every selected pre/post period.",
    )
    parser.add_argument("--refresh", action="store_true", help="Force raw data download even when cache exists.")
    parser.add_argument("--source-url", help="Override source URL for real data download.")
    parser.add_argument("--max-age-days", type=int, help="Refresh cache when manifest is older than this many days.")
    parser.add_argument("--include-non-food", dest="food_only", action="store_false", help="Keep non-food products in panel.")
    parser.add_argument("--include-unknown", dest="exclude_unknown", action="store_false", help="Keep unknown commodity products in panel.")
    parser.add_argument(
        "--dairy-as-control",
        dest="include_dairy_as_treated",
        action="store_false",
        help="Treat dairy as food control instead of livestock-exposed treatment.",
    )
    parser.add_argument("--min-pre-periods", type=int, default=1, help="Minimum pre-event periods required per unit.")
    parser.add_argument("--min-post-periods", type=int, default=1, help="Minimum post-event periods required per unit.")
    parser.add_argument("--max-pre-periods", type=int, help="Cap retained pre-event periods.")
    parser.add_argument("--max-post-periods", type=int, help="Cap retained post-event periods.")
    parser.add_argument("--symmetric-window", action="store_true", help="Use largest equal pre/post period window.")
    parser.add_argument(
        "--unit-level",
        choices=["product_store", "commodity_store", "commodity"],
        default="commodity_store",
        help="Panel unit level for econometric estimation.",
    )
    parser.add_argument("--raw-path", type=Path, help="Process a specific raw JSON file instead of latest cached file.")
    parser.set_defaults(food_only=True, exclude_unknown=True, include_dairy_as_treated=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_stage(
        args.stage,
        PipelinePaths(args.root),
        fixture=args.fixture,
        frequency=args.frequency,
        require_complete_units=args.require_complete_units,
        refresh=args.refresh,
        source_url=args.source_url,
        max_age_days=args.max_age_days,
        food_only=args.food_only,
        exclude_unknown=args.exclude_unknown,
        include_dairy_as_treated=args.include_dairy_as_treated,
        min_pre_periods=args.min_pre_periods,
        min_post_periods=args.min_post_periods,
        max_pre_periods=args.max_pre_periods,
        max_post_periods=args.max_post_periods,
        symmetric_window=args.symmetric_window,
        raw_path_override=args.raw_path,
        unit_level=args.unit_level,
    )
