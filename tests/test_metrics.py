import geopandas as gpd
import pytest
from shapely.geometry import box

from canola_map.metrics import compute_density


def test_compute_density_matches_expected_values_for_known_area_and_count():
    tiles_gdf = gpd.GeoDataFrame(
        {
            "detection_count": [25, 10],
            "geometry": [box(0, 0, 10, 10), box(0, 0, 5, 20)],
        },
        crs="EPSG:25832",
    )

    result = compute_density(tiles_gdf)

    assert result["area_m2"].tolist() == pytest.approx([100.0, 100.0])
    assert result["density_per_m2"].tolist() == pytest.approx([0.25, 0.1])
