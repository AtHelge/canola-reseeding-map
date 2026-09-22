import geopandas as gpd
import pytest
from shapely.geometry import MultiPolygon, box

from canola_map.classify import dissolve_gaps, flag_critical


def test_flag_critical_marks_tiles_below_threshold():
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [5.0, 15.0, 10.0],
            "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)],
        },
        crs="EPSG:25832",
    )

    result = flag_critical(tiles_gdf, critical_density=10)

    assert result["is_critical"].tolist() == [True, False, False]


def test_dissolve_gaps_merges_adjacent_critical_tiles_into_one_cluster():
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [2.0, 4.0],
            "is_critical": [True, True],
            "geometry": [box(10, 0, 12, 2), box(12, 0, 14, 2)],
        },
        crs="EPSG:25832",
    )

    tiles_result, zones_result = dissolve_gaps(tiles_gdf, min_area=5)

    assert len(zones_result) == 1
    assert zones_result["area_m2"].iloc[0] == pytest.approx(8.0)
    assert zones_result["mean_density"].iloc[0] == pytest.approx(3.0)
    assert zones_result["n_tiles"].iloc[0] == 2
    assert tiles_result["gap_status"].tolist() == ["reseed", "reseed"]


def test_dissolve_gaps_drops_isolated_cluster_below_min_area():
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [8.0],
            "is_critical": [True],
            "geometry": [box(0, 0, 2, 2)],
        },
        crs="EPSG:25832",
    )

    tiles_result, zones_result = dissolve_gaps(tiles_gdf, min_area=5)

    assert zones_result.empty
    assert tiles_result["gap_status"].tolist() == ["too_small"]


def test_dissolve_gaps_assigns_reseed_too_small_and_ok_status():
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [8.0, 2.0, 4.0, 100.0],
            "is_critical": [True, True, True, False],
            "geometry": [
                box(0, 0, 2, 2),
                box(10, 0, 12, 2),
                box(12, 0, 14, 2),
                box(20, 0, 22, 2),
            ],
        },
        crs="EPSG:25832",
    )

    tiles_result, zones_result = dissolve_gaps(tiles_gdf, min_area=5)

    assert len(zones_result) == 1
    assert zones_result["area_m2"].iloc[0] == pytest.approx(8.0)
    assert zones_result["n_tiles"].iloc[0] == 2
    assert tiles_result["gap_status"].tolist() == ["too_small", "reseed", "reseed", "ok"]


def test_dissolve_gaps_bridges_small_reprojection_gap_between_tiles():
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [2.0, 4.0],
            "is_critical": [True, True],
            "geometry": [box(0, 0, 2, 2), box(2.01, 0, 4.01, 2)],
        },
        crs="EPSG:25832",
    )

    tiles_result, zones_result = dissolve_gaps(tiles_gdf, min_area=5)

    assert len(zones_result) == 1
    assert zones_result["n_tiles"].iloc[0] == 2
    assert tiles_result["gap_status"].tolist() == ["reseed", "reseed"]


def test_dissolve_gaps_assigns_multipart_tile_to_dominant_cluster_not_orphan_sliver():
    multipart_tile_geometry = MultiPolygon([box(3, 0, 12.4, 4), box(100, 100, 100.3, 101)])
    tiles_gdf = gpd.GeoDataFrame(
        {
            "density_per_m2": [2.0, 3.0],
            "is_critical": [True, True],
            "geometry": [box(0, 0, 3, 4), multipart_tile_geometry],
        },
        crs="EPSG:25832",
    )

    assert tiles_gdf.geometry.iloc[1].area == pytest.approx(37.9)

    tiles_result, zones_result = dissolve_gaps(tiles_gdf, min_area=5)

    assert tiles_result["gap_status"].tolist() == ["reseed", "reseed"]
    assert len(zones_result) == 1
