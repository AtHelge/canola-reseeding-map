# canola-reseeding

A pipeline that turns per-image canola-plant detections and their camera footprints into a reseeding map: it estimates plant density per image tile, flags tiles below a critical density, groups adjacent critical tiles into gap zones, and exports both a GeoPackage (for GIS use) and a PNG overview map.

## Setup

```
python -m venv venv
venv\Scripts\activate        (PowerShell/cmd)
source venv/Scripts/activate (Git Bash)
pip install -e .
pip install -r requirements.txt
```

`pip install -e .` registers the `canola_map` package (src layout) so it importable without setting `PYTHONPATH`; `requirements.txt` installs its runtime dependencies (pandas, geopandas, shapely, rasterio, matplotlib, pyproj, pytest).

## Running the pipeline

```
python -m canola_map.cli --data <path to field data folder> --out <output folder>
```

`--data` must point at a folder containing a `detections/<subfolder>/*.csv` tree, an `image_footprints/*.shp` shapefile, and a `field_boundary/field_boundary.shp` shapefile. The pipeline writes `reseeding_map.gpkg` (with `density` and `gaps` layers) and `reseeding_map.png` into `--out`, creating that folder if needed.

## CLI parameters

| Parameter | Default | Purpose |
|---|---|---|
| `--data` | required | Path to the field data folder (detections, footprints, field boundary). |
| `--out` | required | Output folder for `reseeding_map.gpkg` and `reseeding_map.png`. |
| `--target-density` | 40 | Detections per m² considered a healthy canola stand; used only to label the map, not to classify tiles. |
| `--critical-density` | 10 | Detections per m² below which a tile is flagged `is_critical`; set well below `target-density` so only genuinely thin stands trigger a gap, not ordinary field variation. |
| `--min-gap-area` | 5 | Minimum merged-cluster area (m²) for a critical zone to be reported as reseed-worthy; smaller clusters are marked `too_small` because a reseeding pass isn't worth running on a patch that size. |
| `--conf-threshold` | 0.2 | Minimum detection confidence counted toward density; kept low because canola plant detections at this growth stage tend to score lower than the model's confident range, so a high threshold would undercount real plants. |
| `--crs` | EPSG:25832 | Metric CRS (UTM zone 32N) all geometry is reprojected into before any area or distance calculation, since the raw data ships in WGS84 (degrees, not meters). |
| `--detection-subfolder` | crop_canola | Which class subfolder under `detections/` to read; the data also contains a `grass_weeds` subfolder for a different detection class. |
| `--seed` | 42 | Random seed, for reproducibility of any future stochastic step in the pipeline. |
| `--log-level` | INFO | Logging verbosity for the per-step progress/timing log. |

Any of these can also be set via `config/default.toml`; a CLI flag always overrides the config value for that run.

## Architecture

- `src/canola_map/cli.py` — argument parsing (with `config/default.toml` as the default source), step-by-step pipeline orchestration with per-step timing logs, and the `python -m canola_map.cli` entry point.
- `src/canola_map/io.py` — loads detection CSVs, footprint shapefiles, and the field boundary shapefile from a data folder.
- `src/canola_map/join.py` — aggregates detections per image (`aggregate_per_frame`), attaches footprint geometry to those counts while dropping degenerate footprints, unmatched files, and out-of-boundary tiles (`attach_footprints`), and reprojects geometry to a metric CRS (`reproject`).
- `src/canola_map/metrics.py` — computes tile area and detections-per-m² density (`compute_density`).
- `src/canola_map/classify.py` — flags tiles below the critical density (`flag_critical`) and dissolves adjacent critical tiles into gap clusters, tagging each tile `reseed`, `too_small`, or `ok` (`dissolve_gaps`).
- `src/canola_map/write.py` — exports the tile and gap-zone layers to a GeoPackage (`export_geopackage`).
- `src/canola_map/render.py` — renders the PNG overview map with a flat red/orange/green tile coloring, field boundary, north arrow, scale bar, and legend (`make_png`).
- `config/default.toml` — default values for the CLI parameters above.
- `tests/` — unit tests per module plus `tests/test_integration.py`, which runs the full CLI pipeline against the small real-data fixture in `tests/fixtures/mini_field/`.

## Limitations

- **Tile resolution**: each "tile" is one camera image footprint, not a uniform grid cell, so spatial resolution varies with flight overlap and is not constant across the field.
- **Confidence-threshold sensitivity**: density is computed only from detections at or above `--conf-threshold`; changing it shifts every density value and therefore which tiles are flagged critical, so results should be compared only within a fixed threshold.
- **Degenerate footprint geometries are filtered out**: footprints with an area below 10% of the run's median footprint area are dropped before density is computed. This is a relative threshold, not an absolute one, so it adapts to each flight's footprint size but can only remove footprints that are anomalously small compared to their own run; it exists because the underlying footprint data appears to include sliver polygons left over from an undocumented upstream overlap-removal step.
- **Section-control / machinery context**: the reseed-vs-too-small split (`--min-gap-area`) assumes reseeding is carried out by section-controlled machinery that can only act on zones above some minimum size; the right threshold depends on the actual equipment used and should be tuned accordingly, not treated as a universal constant.
- **Detection quality is out of scope**: this pipeline consumes detections as given and does not evaluate or correct for the upstream model's false positive/negative rate; any systematic bias in the detector will appear unchanged in the density map.
