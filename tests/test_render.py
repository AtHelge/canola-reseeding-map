from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from canola_map.render import make_png


def test_make_png_creates_file_with_mixed_data_and_gap_zone(tmp_path: Path):
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [0.25, np.nan, 0.05],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10), box(20, 0, 30, 10)],
        },
        crs="EPSG:25832",
    )

    zones_gdf = gpd.GeoDataFrame(
        {"geometry": [box(20, 0, 30, 10)]},
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 30, 10)]},
        crs="EPSG:25832",
    )

    out_path = tmp_path / "map.png"

    make_png(
        tiles_gdf,
        zones_gdf,
        field_boundary_gdf,
        out_path,
        target_density=40,
        critical_density=10,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_make_png_handles_no_gap_zones(tmp_path: Path):
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [0.25, 0.3],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        },
        crs="EPSG:25832",
    )

    zones_gdf = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:25832")

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 20, 10)]},
        crs="EPSG:25832",
    )

    out_path = tmp_path / "map_no_zones.png"

    make_png(
        tiles_gdf,
        zones_gdf,
        field_boundary_gdf,
        out_path,
        target_density=40,
        critical_density=10,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0
