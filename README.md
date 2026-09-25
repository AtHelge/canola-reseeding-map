# canola-reseeding

Drone-based reseeding map generator for winter oilseed rape fields — uses plant-level detections per drone frame and their footprints to generate a map of low-density gaps, filtering out noise via confidence, geometry, and minimum-area checks. Outputs a georeferenced GeoPackage + PNG.

## Setup

```
git clone <repo-url>
cd canola-reseeding-map
```

```
parent-folder/
├── canola-reseeding-map/
└── data/field01/
```

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

```
python -m canola_map.cli --data ../data/field01 --out outputs/field01
```

## Parameters

| Flag | Default | Justification |
|---|---|---|
| `--data` | required | Path to the field data folder. |
| `--out` | required | Output folder for the GeoPackage and PNG. |
| `--target-density` | 40 | Average target for winter oilseed rape |
| `--critical-density` | 10 | Lower bound of stand density |
| `--min-gap-area` | 5 | Minimum contiguous area for a gap to count as a real reseeding decision |
| `--conf-threshold` | 0.2 | higher values discarded too many valid low-confidence detections and produced implausibly high critical rates; sensitivity flattens out below ~0.2; no ground truth exists to validate further. |
| `--crs` | EPSG:25832 | Metric CRS (UTM 32N) all geometry is reprojected into before any area calculation. |
| `--detection-subfolder` | crop_canola | Selects the detection class subfolder; the data also ships a `grass_weeds` class. |

Any of these can also be set in `config/default.toml`; a CLI flag always overrides the config value.

## Architecture

- `io.py` — loads detection CSVs, footprint shapefiles, and the field boundary from a data folder.
- `join.py` — aggregates detections per image, attaches footprint geometry, drops degenerate/unmatched/out-of-boundary tiles, reprojects to a metric CRS.
- `metrics.py` — computes tile area and detections-per-m² density.
- `classify.py` — flags tiles below critical density and dissolves adjacent critical tiles into gap clusters, tagging each `reseed`, `too_small`, or `ok`.
- `write.py` — exports the tile and gap-zone layers to a GeoPackage.
- `render.py` — renders the PNG overview map with tile coloring, field boundary, north arrow, scale bar, and legend.
- `cli.py` — argument parsing and pipeline orchestration.

The pipeline is fully deterministic — no randomness is used anywhere, so no random seed is required.

## Outputs

`--out` contains:
- `reseeding_map.gpkg` — `whole_field` layer (one row per image tile, with density and gap status) and `reseeding_zones` layer (merged gap clusters at or above `--min-gap-area`).
- `reseeding_map.png` — overview map. Green: at or above critical density. Red: below critical density, cluster large enough to reseed. Orange: below critical density, but the cluster is too small to act on.

## Viewing the output in QGIS

1. Layer > Add Layer > Add Vector Layer, select `reseeding_map.gpkg`.
2. Choose both the `whole_field` and `reseeding_zones` layers.
3. To match the PNG's coloring: right-click `whole_field` > Properties > Symbology > switch to "Categorized" > Value: `gap_status` > Classify.
