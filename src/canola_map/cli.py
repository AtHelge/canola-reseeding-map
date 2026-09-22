import argparse
import logging
import random
import sys
import time
import tomllib
from pathlib import Path

from canola_map import classify, join, metrics, render, write
from canola_map import io as data_io

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "default.toml"

HARDCODED_DEFAULTS = {
    "target_density": 40,
    "critical_density": 10,
    "min_gap_area": 5,
    "conf_threshold": 0.5,
    "crs": "EPSG:25832",
    "seed": 42,
    "log_level": "INFO",
    "detection_subfolder": "crop_canola",
}


def load_config_defaults(config_path: Path) -> dict:
    if not config_path.exists():
        return {}

    with open(config_path, "rb") as config_file:
        return tomllib.load(config_file)


def build_parser(defaults: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canola reseeding map pipeline")
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--target-density", type=float, default=defaults["target_density"])
    parser.add_argument("--critical-density", type=float, default=defaults["critical_density"])
    parser.add_argument("--min-gap-area", type=float, default=defaults["min_gap_area"])
    parser.add_argument("--conf-threshold", type=float, default=defaults["conf_threshold"])
    parser.add_argument("--crs", default=defaults["crs"])
    parser.add_argument("--seed", type=int, default=defaults["seed"])
    parser.add_argument("--log-level", default=defaults["log_level"])
    parser.add_argument("--detection-subfolder", default=defaults["detection_subfolder"])
    return parser


def parse_args(argv=None) -> argparse.Namespace:
    config_defaults = load_config_defaults(DEFAULT_CONFIG_PATH)
    defaults = {**HARDCODED_DEFAULTS, **config_defaults}
    parser = build_parser(defaults)
    return parser.parse_args(argv)


def _run_step(step_name, step_fn, *args, **kwargs):
    logger.info("Starting step: %s", step_name)
    start_time = time.perf_counter()
    result = step_fn(*args, **kwargs)
    elapsed = time.perf_counter() - start_time
    logger.info("Finished step: %s in %.2fs", step_name, elapsed)
    return result


def _discover_detection_subfolder(data_dir: Path) -> str:
    detections_dir = data_dir / "detections"
    subfolders = sorted(path.name for path in detections_dir.iterdir() if path.is_dir())

    if len(subfolders) != 1:
        raise RuntimeError(
            f"Expected exactly one subfolder in {detections_dir}, found {len(subfolders)}: "
            f"{subfolders}. Pass --detection-subfolder to pick one."
        )

    return subfolders[0]


def run_pipeline(args: argparse.Namespace) -> None:
    data_dir = Path(args.data)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    gpkg_path = out_dir / "reseeding_map.gpkg"
    png_path = out_dir / "reseeding_map.png"

    subfolder = args.detection_subfolder or _discover_detection_subfolder(data_dir)
    detections_df = _run_step("load_detections", data_io.load_detections, data_dir, subfolder)

    footprints_gdf = _run_step("load_footprints", data_io.load_footprints, data_dir)
    if footprints_gdf.empty:
        raise RuntimeError("No footprints found in data directory")

    field_boundary_gdf = _run_step("load_field_boundary", data_io.load_field_boundary, data_dir)
    if field_boundary_gdf.empty:
        raise RuntimeError("No field boundary found in data directory")

    footprints_gdf = _run_step("reproject_footprints", join.reproject, footprints_gdf, args.crs)
    field_boundary_gdf = _run_step(
        "reproject_field_boundary", join.reproject, field_boundary_gdf, args.crs
    )

    counts_df = _run_step(
        "aggregate_per_frame", join.aggregate_per_frame, detections_df, args.conf_threshold
    )
    tiles_gdf = _run_step(
        "attach_footprints", join.attach_footprints, counts_df, footprints_gdf, field_boundary_gdf
    )
    tiles_gdf = _run_step("compute_density", metrics.compute_density, tiles_gdf)
    tiles_gdf = _run_step(
        "flag_critical", classify.flag_critical, tiles_gdf, args.critical_density
    )
    tiles_gdf, zones_gdf = _run_step(
        "dissolve_gaps", classify.dissolve_gaps, tiles_gdf, args.min_gap_area
    )

    _run_step("export_geopackage", write.export_geopackage, tiles_gdf, zones_gdf, gpkg_path)
    _run_step(
        "make_png",
        render.make_png,
        tiles_gdf,
        field_boundary_gdf,
        png_path,
        args.target_density,
        args.critical_density,
    )


def main(argv=None) -> None:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    random.seed(args.seed)

    pipeline_start_time = time.perf_counter()
    try:
        run_pipeline(args)
    except Exception:
        logger.error("Pipeline failed", exc_info=True)
        sys.exit(1)

    elapsed = time.perf_counter() - pipeline_start_time
    logger.info("Pipeline completed in %.2fs", elapsed)


if __name__ == "__main__":
    main()
