import argparse
import tomllib
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "default.toml"

HARDCODED_DEFAULTS = {
    "target_density": 40,
    "critical_density": 10,
    "min_gap_area": 5,
    "conf_threshold": 0.5,
    "crs": "EPSG:25832",
    "seed": 42,
    "log_level": "INFO",
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
    return parser


def parse_args(argv=None) -> argparse.Namespace:
    config_defaults = load_config_defaults(DEFAULT_CONFIG_PATH)
    defaults = {**HARDCODED_DEFAULTS, **config_defaults}
    parser = build_parser(defaults)
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    print(args)


if __name__ == "__main__":
    main()
