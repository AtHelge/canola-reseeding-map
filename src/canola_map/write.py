from pathlib import Path

import geopandas as gpd


def export_geopackage(tiles_gdf: gpd.GeoDataFrame, zones_gdf: gpd.GeoDataFrame, out_path: Path) -> None:
    tiles_gdf.to_file(out_path, driver="GPKG", layer="density")
    zones_gdf.to_file(out_path, driver="GPKG", layer="gaps")
