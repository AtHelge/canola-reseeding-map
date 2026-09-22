from pathlib import Path

import geopandas as gpd

from canola_map.cli import main


def test_full_pipeline_on_mini_field_produces_plausible_outputs(tmp_path):
    fixture_dir = Path(__file__).parent / "fixtures" / "mini_field"
    out_dir = tmp_path / "outputs"

    main(
        [
            "--data",
            str(fixture_dir),
            "--out",
            str(out_dir),
            "--detection-subfolder",
            "crop_canola",
        ]
    )

    gpkg_path = out_dir / "reseeding_map.gpkg"
    png_path = out_dir / "reseeding_map.png"

    assert gpkg_path.exists()
    assert png_path.exists()
    assert png_path.stat().st_size > 0

    density = gpd.read_file(gpkg_path, layer="density")
    gaps = gpd.read_file(gpkg_path, layer="gaps")

    assert not density.empty
    assert set(density["gap_status"].unique()).issubset({"reseed", "too_small", "ok"})
    assert (density["density_per_m2"] >= 0).all()
    assert (gaps["area_m2"] >= 5).all()

    zero_survivor_row = density[density["file_name"] == "425_c_20250929093922869_t_00012C06F254_cam"]
    assert len(zero_survivor_row) == 1
    assert zero_survivor_row["detection_count"].iloc[0] == 0

    degenerate_names = set(density["file_name"]) & {"618_c_20250929094211812_t_00012C06F254_cam"}
    assert degenerate_names == set()
