import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseMultipartGeometry

GAP_CLOSING_TOLERANCE_M = 0.1


def flag_critical(tiles_gdf: gpd.GeoDataFrame, critical_density: float = 10) -> gpd.GeoDataFrame:
    result = tiles_gdf.copy()
    result["is_critical"] = result["density_per_m2"] < critical_density
    return result


def dissolve_gaps(
    tiles_gdf: gpd.GeoDataFrame, min_area: float = 5
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    tiles_gdf = tiles_gdf.copy()
    critical_tiles = tiles_gdf[tiles_gdf["is_critical"]]

    if critical_tiles.empty:
        tiles_gdf["gap_status"] = "ok"
        zones_gdf = gpd.GeoDataFrame(
            {"geometry": [], "area_m2": [], "mean_density": [], "n_tiles": []},
            crs=tiles_gdf.crs,
        )
        return tiles_gdf, zones_gdf

    merged = critical_tiles.geometry.buffer(GAP_CLOSING_TOLERANCE_M).union_all()
    merged = merged.buffer(-GAP_CLOSING_TOLERANCE_M)
    pieces = list(merged.geoms) if isinstance(merged, BaseMultipartGeometry) else [merged]

    clusters = gpd.GeoDataFrame({"geometry": pieces}, crs=tiles_gdf.crs)
    clusters["area_m2"] = clusters.geometry.area

    dominant_cluster_position = {}
    for tile_idx, tile_geometry in critical_tiles.geometry.items():
        overlap_areas = [tile_geometry.intersection(piece).area for piece in pieces]
        dominant_cluster_position[tile_idx] = overlap_areas.index(max(overlap_areas))

    mean_densities = []
    n_tiles = []
    gap_status = pd.Series("ok", index=tiles_gdf.index)

    for cluster_position, cluster_area in enumerate(clusters["area_m2"]):
        member_idx = [
            tile_idx
            for tile_idx, position in dominant_cluster_position.items()
            if position == cluster_position
        ]
        member_tiles = tiles_gdf.loc[member_idx]
        mean_densities.append(member_tiles["density_per_m2"].mean())
        n_tiles.append(len(member_tiles))
        gap_status.loc[member_idx] = "reseed" if cluster_area >= min_area else "too_small"

    tiles_gdf["gap_status"] = gap_status

    clusters["mean_density"] = mean_densities
    clusters["n_tiles"] = n_tiles

    zones_gdf = clusters[clusters["area_m2"] >= min_area].reset_index(drop=True)

    return tiles_gdf, zones_gdf
