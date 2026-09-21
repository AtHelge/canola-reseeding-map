import geopandas as gpd


def flag_critical(tiles_gdf: gpd.GeoDataFrame, critical_density: float = 10) -> gpd.GeoDataFrame:
    result = tiles_gdf.copy()
    result["is_critical"] = result["density_per_m2"] < critical_density
    return result
