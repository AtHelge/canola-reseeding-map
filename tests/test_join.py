import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from canola_map.join import aggregate_per_frame, attach_footprints, reproject


def test_aggregate_per_frame_counts_detections_above_threshold():
    detections_df = pd.DataFrame(
        {
            "file_name": ["img1", "img1", "img1", "img2", "img2", "img3"],
            "confidence": [0.9, 0.6, 0.4, 0.55, 0.2, 0.3],
        }
    )

    result = aggregate_per_frame(detections_df, conf_threshold=0.5)

    expected = {"img1": 2, "img2": 1}
    assert dict(zip(result["file_name"], result["detection_count"])) == expected


def test_aggregate_per_frame_excludes_frames_with_no_detections_above_threshold():
    detections_df = pd.DataFrame(
        {
            "file_name": ["img1", "img1", "img2"],
            "confidence": [0.9, 0.8, 0.1],
        }
    )

    result = aggregate_per_frame(detections_df, conf_threshold=0.5)

    assert list(result["file_name"]) == ["img1"]
    assert list(result["detection_count"]) == [2]


def test_aggregate_per_frame_includes_boundary_confidence_value():
    detections_df = pd.DataFrame(
        {
            "file_name": ["img1", "img1"],
            "confidence": [0.5, 0.49],
        }
    )

    result = aggregate_per_frame(detections_df, conf_threshold=0.5)

    assert dict(zip(result["file_name"], result["detection_count"])) == {"img1": 1}


def test_attach_footprints_logs_unmatched_file_name_and_area_share(caplog):
    counts = pd.DataFrame(
        {
            "file_name": ["img1", "img2"],
            "detection_count": [5, 3],
        }
    )

    footprints_gdf = gpd.GeoDataFrame(
        {"file_name": ["img1"], "geometry": [box(0, 0, 50, 100)]},
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 100, 100)]},
        crs="EPSG:25832",
    )

    with caplog.at_level(logging.WARNING):
        result = attach_footprints(counts, footprints_gdf, field_boundary_gdf)

    assert len(result) == 2
    assert result.loc[result["file_name"] == "img2", "geometry"].isna().all()
    assert result.loc[result["file_name"] == "img1", "geometry"].notna().all()

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert "1 file_names have no footprint match" in message
    assert "50.0%" in message


def test_reproject_converts_crs_and_yields_plausible_area_in_meters():
    gdf = gpd.GeoDataFrame(
        {"geometry": [box(9.0, 52.0, 9.01, 52.01)]},
        crs="EPSG:4326",
    )

    result = reproject(gdf, target_crs="EPSG:25832")

    assert result.crs.to_string() == "EPSG:25832"
    assert result.geometry.iloc[0].geom_type == "Polygon"

    area_m2 = result.geometry.area.iloc[0]
    assert 100_000 < area_m2 < 1_000_000
