from pathlib import Path

import geopandas as gpd


def export_geopackage(tiles_gdf: gpd.GeoDataFrame, zones_gdf: gpd.GeoDataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_path.unlink(missing_ok=True)
    except PermissionError as error:
        raise PermissionError(
            f"Cannot overwrite {out_path} because it is open in another program "
            "(e.g. QGIS). Close it there and rerun the pipeline."
        ) from error
    tiles_gdf.to_file(out_path, driver="GPKG", layer="whole_field")
    zones_gdf.to_file(out_path, driver="GPKG", layer="reseeding_zones")
