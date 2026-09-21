from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

from canola_map.write import export_geopackage


def test_export_geopackage_writes_both_layers_with_expected_columns(tmp_path: Path):
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [0.25, 0.1],
            "area_m2": [100.0, 100.0],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        },
        crs="EPSG:25832",
    )

    zones_gdf = gpd.GeoDataFrame(
        {
            "area_m2": [8.0],
            "mean_density": [3.0],
            "n_tiles": [2],
            "geometry": [box(0, 0, 4, 2)],
        },
        crs="EPSG:25832",
    )

    out_path = tmp_path / "output.gpkg"

    export_geopackage(tiles_gdf, zones_gdf, out_path)

    assert out_path.exists()

    density_layer = gpd.read_file(out_path, layer="density")
    gaps_layer = gpd.read_file(out_path, layer="gaps")

    assert list(density_layer.columns) == ["density_per_m2", "area_m2", "geometry"]
    assert list(gaps_layer.columns) == ["area_m2", "mean_density", "n_tiles", "geometry"]

    assert len(density_layer) == 2
    assert len(gaps_layer) == 1
