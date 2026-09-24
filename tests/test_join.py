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


def test_attach_footprints_keeps_footprint_with_zero_surviving_detections():
    counts = pd.DataFrame(
        {
            "file_name": ["img1"],
            "detection_count": [5],
        }
    )

    footprints_gdf = gpd.GeoDataFrame(
        {
            "file_name": ["img1", "img2"],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        },
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 20, 10)]},
        crs="EPSG:25832",
    )

    result = attach_footprints(counts, footprints_gdf, field_boundary_gdf)

    assert len(result) == 2
    counts_by_name = dict(zip(result["file_name"], result["detection_count"]))
    assert counts_by_name == {"img1": 5, "img2": 0}
    assert result["geometry"].notna().all()


def test_attach_footprints_drops_degenerate_geometry_footprints():
    counts = pd.DataFrame(
        {
            "file_name": ["img1", "img2", "img3", "img_sliver"],
            "detection_count": [5, 3, 7, 2],
        }
    )

    footprints_gdf = gpd.GeoDataFrame(
        {
            "file_name": ["img1", "img2", "img3", "img_sliver"],
            "geometry": [
                box(0, 0, 10, 10),
                box(10, 0, 20, 10),
                box(20, 0, 30, 10),
                box(40, 0, 40.1, 0.1),
            ],
        },
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 41, 10)]},
        crs="EPSG:25832",
    )

    result = attach_footprints(counts, footprints_gdf, field_boundary_gdf)

    assert set(result["file_name"]) == {"img1", "img2", "img3"}
    assert "img_sliver" not in set(result["file_name"])


def test_attach_footprints_drops_counts_without_footprint_match():
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

    result = attach_footprints(counts, footprints_gdf, field_boundary_gdf)

    assert len(result) == 1
    assert list(result["file_name"]) == ["img1"]
    assert result["detection_count"].iloc[0] == 5


def test_attach_footprints_drops_tile_outside_field_boundary():
    counts = pd.DataFrame(
        {
            "file_name": ["img1", "img2"],
            "detection_count": [5, 3],
        }
    )

    footprints_gdf = gpd.GeoDataFrame(
        {
            "file_name": ["img1", "img2"],
            "geometry": [box(0, 0, 10, 10), box(1000, 1000, 1010, 1010)],
        },
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 20, 20)]},
        crs="EPSG:25832",
    )

    result = attach_footprints(counts, footprints_gdf, field_boundary_gdf)

    assert len(result) == 1
    assert list(result["file_name"]) == ["img1"]


def test_attach_footprints_output_never_exceeds_raw_footprint_count():
    counts = pd.DataFrame(
        {
            "file_name": ["img1", "img2", "img3", "img4"],
            "detection_count": [5, 3, 7, 2],
        }
    )

    footprints_gdf = gpd.GeoDataFrame(
        {
            "file_name": ["img1", "img2"],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        },
        crs="EPSG:25832",
    )

    field_boundary_gdf = gpd.GeoDataFrame(
        {"geometry": [box(0, 0, 20, 10)]},
        crs="EPSG:25832",
    )

    result = attach_footprints(counts, footprints_gdf, field_boundary_gdf)

    assert len(result) <= len(footprints_gdf)
    assert len(result) == 2
    assert set(result["file_name"]) == {"img1", "img2"}


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
