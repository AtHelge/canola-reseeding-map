from pathlib import Path

import geopandas as gpd


def export_geopackage(tiles_gdf: gpd.GeoDataFrame, zones_gdf: gpd.GeoDataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tiles_gdf.to_file(out_path, driver="GPKG", layer="density")
    zones_gdf.to_file(out_path, driver="GPKG", layer="gaps")
