import geopandas as gpd


def compute_density(tiles_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    result = tiles_gdf.copy()
    result["area_m2"] = result.geometry.area
    result["density_per_m2"] = result["detection_count"] / result["area_m2"]
    return result
