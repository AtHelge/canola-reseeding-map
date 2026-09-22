from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from canola_map.render import make_png


def test_make_png_creates_file_with_all_gap_statuses_and_no_data(tmp_path: Path):
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [15.0, np.nan, 5.0, 3.0],
            "is_critical": [False, False, True, True],
            "gap_status": ["ok", "ok", "too_small", "reseed"],
            "geometry": [
                box(0, 0, 10, 10),
                box(10, 0, 20, 10),
                box(20, 0, 30, 10),
                box(30, 0, 40, 10),
            ],
        },
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 40, 10)]},
        crs="EPSG:25832",
    )

    out_path = tmp_path / "map.png"

    make_png(
        tiles_gdf,
        field_boundary_gdf,
        out_path,
        target_density=40,
        critical_density=10,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_make_png_handles_only_ok_tiles(tmp_path: Path):
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [15.0, 20.0],
            "is_critical": [False, False],
            "gap_status": ["ok", "ok"],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        },
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 20, 10)]},
        crs="EPSG:25832",
    )

    out_path = tmp_path / "map_only_ok.png"

    make_png(
        tiles_gdf,
        field_boundary_gdf,
        out_path,
        target_density=40,
        critical_density=10,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0
