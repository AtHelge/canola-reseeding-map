import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)


def load_detections(data_dir: Path, subfolder: str) -> pd.DataFrame:
    subfolder_dir = data_dir / "detections" / subfolder
    csv_paths = sorted(subfolder_dir.glob("*.csv"))

    if not csv_paths:
        logger.warning("No detection CSVs found in %s", subfolder_dir)
        return pd.DataFrame()

    logger.info("Loading %d detection CSVs from %s", len(csv_paths), subfolder_dir)
    frames = [pd.read_csv(csv_path).assign(file_name=csv_path.stem) for csv_path in csv_paths]
    return pd.concat(frames, ignore_index=True)


def load_footprints(data_dir: Path) -> gpd.GeoDataFrame:
    footprints_dir = data_dir / "image_footprints"
    shp_paths = sorted(footprints_dir.glob("*.shp"))

    if not shp_paths:
        logger.warning("No footprint shapefiles found in %s", footprints_dir)
        return gpd.GeoDataFrame()

    logger.info("Loading %d footprint shapefiles from %s", len(shp_paths), footprints_dir)
    frames = [gpd.read_file(shp_path).assign(file_name=shp_path.stem) for shp_path in shp_paths]
    return pd.concat(frames, ignore_index=True)


def load_field_boundary(data_dir: Path) -> gpd.GeoDataFrame:
    boundary_path = data_dir / "field_boundary.shp"

    if not boundary_path.exists():
        logger.warning("No field boundary shapefile found at %s", boundary_path)
        return gpd.GeoDataFrame()

    logger.info("Loading field boundary from %s", boundary_path)
    return gpd.read_file(boundary_path)
