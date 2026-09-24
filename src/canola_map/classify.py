import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseMultipartGeometry

GAP_CLOSING_TOLERANCE_M = 0.1


def flag_critical(tiles_gdf: gpd.GeoDataFrame, critical_density: float = 10) -> gpd.GeoDataFrame:
    result = tiles_gdf.copy()
    result["is_critical"] = result["density_per_m2"] < critical_density
    #returns gdf with is_critical column (true for critical tiles)
    return result



def dissolve_gaps(tiles_gdf: gpd.GeoDataFrame, min_area: float = 5
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    tiles_gdf = tiles_gdf.copy()
    #select all tiles that are marked as critical (is_critical = True)
    critical_tiles = tiles_gdf[tiles_gdf["is_critical"]]

    if critical_tiles.empty:
        tiles_gdf["gap_status"] = "ok"
        zones_gdf = gpd.GeoDataFrame(
            {"geometry": [], "area_m2": [], "mean_density": [], "n_tiles": []},
            crs=tiles_gdf.crs,
        )
        return tiles_gdf, zones_gdf

    # expands critical tiles by GAP_CLOSING_TOLERANCE_M so nearly-touching tiles merge into one cluster
    merged = critical_tiles.geometry.buffer(GAP_CLOSING_TOLERANCE_M).union_all()
    #merged is a shapley object
    merged = merged.buffer(-GAP_CLOSING_TOLERANCE_M)
    # splits the merged geometry into individual pieces
    pieces = list(merged.geoms) if isinstance(merged, BaseMultipartGeometry) else [merged]

    #builds a GeoDataFrame for the clusters (both: under 5m2 and above) with their geometries and areas
    clusters = gpd.GeoDataFrame({"geometry": pieces}, crs=tiles_gdf.crs)
    clusters["area_m2"] = clusters.geometry.area

    # determines which cluster each critical tile belongs to by finding the cluster with the largest overlap area
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
        # calculates mean density of the tiles in the cluster and number of tiles in cluster ->for .gpkg file
        member_tiles = tiles_gdf.loc[member_idx]
        mean_densities.append(member_tiles["density_per_m2"].mean())
        n_tiles.append(len(member_tiles))
        # tags tiles in cluster as reseed if bigger 5m2 otherwise as too_small
        gap_status.loc[member_idx] = "reseed" if cluster_area >= min_area else "too_small"


    tiles_gdf["gap_status"] = gap_status

    clusters["mean_density"] = mean_densities
    clusters["n_tiles"] = n_tiles

    # drops clusters below min_area of 5m2
    zones_gdf = clusters[clusters["area_m2"] >= min_area].reset_index(drop=True)

    #returns tiles with gap_status column and zones with area, mean_density and n_tiles columns
    return tiles_gdf, zones_gdf
