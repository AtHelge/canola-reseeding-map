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
    median_area = footprints_gdf.geometry.area.median()
    valid_mask = footprints_gdf.geometry.area >= 0.1 * median_area
    n_dropped_degenerate = int((~valid_mask).sum())
    if n_dropped_degenerate > 0:
        logger.warning(
            "%d footprints dropped as degenerate geometries (area below 10%% of median tile area)",
            n_dropped_degenerate,
        )
    footprints_gdf = footprints_gdf.loc[valid_mask]

    field_union = field_boundary_gdf.geometry.union_all()

    counts_without_footprint = set(counts["file_name"]) - set(footprints_gdf["file_name"])
    unmatched_count = len(counts_without_footprint)

    if unmatched_count > 0:
        matched_union = footprints_gdf.geometry.union_all()
        field_area = field_union.area
        covered_area = matched_union.intersection(field_union).area
        area_share = covered_area / field_area if field_area else 0.0
        logger.warning(
            "%d file_names have no footprint match; matched footprints cover %.1f%% of the field area",
            unmatched_count,
            area_share * 100,
        )

    merged = footprints_gdf.merge(counts, on="file_name", how="left")
    merged["detection_count"] = merged["detection_count"].fillna(0).astype(int)
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=footprints_gdf.crs)

    within_boundary_mask = merged.geometry.intersects(field_union)

    return merged.loc[within_boundary_mask].reset_index(drop=True)


def reproject(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:25832") -> gpd.GeoDataFrame:
    return gdf.to_crs(target_crs)
