import geopandas as gpd
from shapely.geometry.base import BaseMultipartGeometry


def flag_critical(tiles_gdf: gpd.GeoDataFrame, critical_density: float = 10) -> gpd.GeoDataFrame:
    result = tiles_gdf.copy()
    result["is_critical"] = result["density_per_m2"] < critical_density
    return result


def dissolve_gaps(tiles_gdf: gpd.GeoDataFrame, min_area: float = 5) -> gpd.GeoDataFrame:
    critical_tiles = tiles_gdf[tiles_gdf["is_critical"]]

    if critical_tiles.empty:
        return gpd.GeoDataFrame(
            {"geometry": [], "area_m2": [], "mean_density": [], "n_tiles": []},
            crs=tiles_gdf.crs,
        )

    merged = critical_tiles.geometry.union_all()
    pieces = list(merged.geoms) if isinstance(merged, BaseMultipartGeometry) else [merged]

    clusters = gpd.GeoDataFrame({"geometry": pieces}, crs=tiles_gdf.crs)
    clusters["area_m2"] = clusters.geometry.area

    mean_densities = []
    n_tiles = []
    for cluster_geometry in clusters.geometry:
        member_tiles = critical_tiles[critical_tiles.geometry.intersects(cluster_geometry)]
        mean_densities.append(member_tiles["density_per_m2"].mean())
        n_tiles.append(len(member_tiles))

    clusters["mean_density"] = mean_densities
    clusters["n_tiles"] = n_tiles

    return clusters[clusters["area_m2"] >= min_area].reset_index(drop=True)
