import geopandas as gpd

# calculates the density of detections per square meter for each tile in the GeoDataFrame and saves as a copy
def compute_density(tiles_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    result = tiles_gdf.copy()
    result["area_m2"] = result.geometry.area
    result["density_per_m2"] = result["detection_count"] / result["area_m2"]
    #returns gdf with area and density columns
    return result

