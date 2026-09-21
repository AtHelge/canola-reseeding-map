import logging

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)


def aggregate_per_frame(detections_df: pd.DataFrame, conf_threshold: float) -> pd.DataFrame:
    filtered = detections_df[detections_df["confidence"] >= conf_threshold]
    return filtered.groupby("file_name").size().reset_index(name="detection_count")


def attach_footprints(
    counts: pd.DataFrame,
    footprints_gdf: gpd.GeoDataFrame,
    field_boundary_gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    merged = counts.merge(footprints_gdf, on="file_name", how="left")
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=footprints_gdf.crs)

    unmatched_mask = merged["geometry"].isna()
    unmatched_count = int(unmatched_mask.sum())

    if unmatched_count > 0:
        matched_union = merged.loc[~unmatched_mask, "geometry"].union_all()
        field_union = field_boundary_gdf.geometry.union_all()
        field_area = field_union.area
        covered_area = matched_union.intersection(field_union).area
        area_share = covered_area / field_area if field_area else 0.0
        logger.warning(
            "%d file_names have no footprint match; matched footprints cover %.1f%% of the field area",
            unmatched_count,
            area_share * 100,
        )

    return merged


def reproject(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:25832") -> gpd.GeoDataFrame:
    return gdf.to_crs(target_crs)
