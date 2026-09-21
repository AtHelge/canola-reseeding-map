from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box


@pytest.fixture
def detections_data_dir(tmp_path: Path) -> Path:
    subfolder_dir = tmp_path / "detections" / "fieldA"
    subfolder_dir.mkdir(parents=True)

    pd.DataFrame(
        {
            "x": [10.0, 20.0],
            "y": [50.0, 60.0],
            "confidence": [0.8, 0.9],
        }
    ).to_csv(subfolder_dir / "plot1.csv", index=False)

    pd.DataFrame(
        {
            "x": [30.0],
            "y": [70.0],
            "confidence": [0.6],
        }
    ).to_csv(subfolder_dir / "plot2.csv", index=False)

    return tmp_path


@pytest.fixture
def footprints_data_dir(tmp_path: Path) -> Path:
    footprints_dir = tmp_path / "image_footprints"
    footprints_dir.mkdir(parents=True)

    gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 10, 10)]},
        crs="EPSG:25832",
    ).to_file(footprints_dir / "img001.shp")

    gpd.GeoDataFrame(
        {"geometry": [box(10, 0, 20, 10)]},
        crs="EPSG:25832",
    ).to_file(footprints_dir / "img002.shp")

    return tmp_path


@pytest.fixture
def field_boundary_data_dir(tmp_path: Path) -> Path:
    gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 100, 100)]},
        crs="EPSG:25832",
    ).to_file(tmp_path / "field_boundary.shp")

    return tmp_path
