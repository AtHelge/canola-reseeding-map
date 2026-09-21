from pathlib import Path

import geopandas as gpd
import pandas as pd

from canola_map.io import load_detections, load_field_boundary, load_footprints


def test_load_detections_concatenates_all_csvs(detections_data_dir: Path):
    result = load_detections(detections_data_dir, "fieldA")

    assert len(result) == 3
    assert list(result.columns) == ["x", "y", "confidence", "file_name"]


def test_load_detections_adds_file_name_without_extension(detections_data_dir: Path):
    result = load_detections(detections_data_dir, "fieldA")

    assert set(result["file_name"]) == {"plot1", "plot2"}


def test_load_detections_returns_empty_frame_for_missing_subfolder(detections_data_dir: Path):
    result = load_detections(detections_data_dir, "fieldB")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_load_footprints_concatenates_all_shapefiles(footprints_data_dir: Path):
    result = load_footprints(footprints_data_dir)

    assert len(result) == 2
    assert set(result["file_name"]) == {"img001", "img002"}


def test_load_footprints_returns_empty_geodataframe_when_missing(tmp_path: Path):
    result = load_footprints(tmp_path)

    assert isinstance(result, gpd.GeoDataFrame)
    assert result.empty


def test_load_field_boundary_reads_single_shapefile(field_boundary_data_dir: Path):
    result = load_field_boundary(field_boundary_data_dir)

    assert len(result) == 1
    assert result.crs.to_string() == "EPSG:25832"


def test_load_field_boundary_returns_empty_geodataframe_when_missing(tmp_path: Path):
    result = load_field_boundary(tmp_path)

    assert isinstance(result, gpd.GeoDataFrame)
    assert result.empty
