import geopandas as gpd
from shapely.geometry import box

from canola_map.classify import flag_critical


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
