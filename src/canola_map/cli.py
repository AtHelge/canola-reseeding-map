import argparse
import tomllib
from pathlib import Path
from canola_map import classify, join, metrics, render, write
from canola_map import io as data_io


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "default.toml"

#loads default config values from default.toml
def load_config_defaults(config_path: Path) -> dict:
    with open(config_path, "rb") as config_file:
        return tomllib.load(config_file)


# argument data and out required, the rest can be changed optionally. Defaults are loaded from default.toml
def build_parser(defaults: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canola reseeding map pipeline")
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--target-density", type=float, default=defaults["target_density"])
    parser.add_argument("--critical-density", type=float, default=defaults["critical_density"])
    parser.add_argument("--min-gap-area", type=float, default=defaults["min_gap_area"])
    parser.add_argument("--conf-threshold", type=float, default=defaults["conf_threshold"])
    parser.add_argument("--crs", default=defaults["crs"])
    parser.add_argument("--detection-subfolder", default=defaults["detection_subfolder"])
    return parser

# parses command line arguments
def parse_args(argv=None) -> argparse.Namespace:
    defaults = load_config_defaults(DEFAULT_CONFIG_PATH)
    parser = build_parser(defaults)
    return parser.parse_args(argv)



def run_pipeline(args: argparse.Namespace) -> None:

    #saves the parsed arguments as path objects
    data_dir = Path(args.data)
    out_dir = Path(args.out)

    #creates output folder based on provided path
    out_dir.mkdir(parents=True, exist_ok=True)
    gpkg_path = out_dir / "reseeding_map.gpkg"
    png_path = out_dir / "reseeding_map.png"


    # loads detections, footprints, and field boundary with help of data.io
    subfolder = args.detection_subfolder #selects subfolder from default or as provided by user
    detections_df = data_io.load_detections(data_dir, subfolder)

    footprints_gdf = data_io.load_footprints(data_dir)
    if footprints_gdf.empty:
        raise RuntimeError("No footprints found in data directory")

    field_boundary_gdf = data_io.load_field_boundary(data_dir)
    if field_boundary_gdf.empty:
        raise RuntimeError("No field boundary found in data directory")


    # reprojects footprints and field boundary to the specified coordinate reference system (default 25832)
    footprints_gdf = join.reproject(footprints_gdf, args.crs)
    field_boundary_gdf = join.reproject(field_boundary_gdf, args.crs)

    #passes the conf treshold to aggregate_per_frame to filter out detections below the threshold
    counts_df = join.aggregate_per_frame(detections_df, args.conf_threshold)


    tiles_gdf = join.attach_footprints(counts_df, footprints_gdf, field_boundary_gdf)
    tiles_gdf = metrics.compute_density(tiles_gdf) 
    tiles_gdf = classify.flag_critical(tiles_gdf, args.critical_density)
    tiles_gdf, zones_gdf = classify.dissolve_gaps(tiles_gdf, args.min_gap_area)

    write.export_geopackage(tiles_gdf, zones_gdf, gpkg_path)
    
    render.make_png(
        tiles_gdf,
        field_boundary_gdf,
        png_path,
        args.target_density,
        args.critical_density,
    )


def main(argv=None) -> None:
    args = parse_args(argv)
    run_pipeline(args)


if __name__ == "__main__":
    main()
