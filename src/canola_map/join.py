
import geopandas as gpd
import pandas as pd


#reprojection function to convert the coordinate reference system of a GeoDataFrame to a target CRS
def reproject(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:25832") -> gpd.GeoDataFrame:
    return gdf.to_crs(target_crs)


# filters out detections below conf_threshold; raising it undercounts real plants, lowering it counts more false positives
def aggregate_per_frame(detections_df: pd.DataFrame, conf_threshold: float) -> pd.DataFrame:
    filtered = detections_df[detections_df["confidence"] >= conf_threshold]
    #counts the number of detections per file_name and returns a DataFrame with file_name and detection_count columns
    return filtered.groupby("file_name").size().reset_index(name="detection_count")


def attach_footprints(counts: pd.DataFrame,footprints_gdf: gpd.GeoDataFrame,field_boundary_gdf: gpd.GeoDataFrame,) -> gpd.GeoDataFrame:
    # removes all degenerate footprints smaller than 10% of the median tile area
    median_area = footprints_gdf.geometry.area.median()
    valid_mask = footprints_gdf.geometry.area >= 0.1 * median_area
    footprints_gdf = footprints_gdf.loc[valid_mask]

    #creates a union of all geometries in the field boundary GeoDataFrame to create a polygon representing the entire field
    field_union = field_boundary_gdf.geometry.union_all()

    # merge footprints and counts(detections) where the file_name matches
    merged = footprints_gdf.merge(counts, on="file_name", how="left")
    # fills missing detection counts with 0
    merged["detection_count"] = merged["detection_count"].fillna(0).astype(int)
    # and converts the result to a GeoDataFrame
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=footprints_gdf.crs)

    # keeps only tiles that touch or overlap the field boundary, masks everything fully outside as false
    within_boundary_mask = merged.geometry.intersects(field_union)

    #removes false tiles and resets the row index of the resulting GeoDataFrame
    return merged.loc[within_boundary_mask].reset_index(drop=True)

