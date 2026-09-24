from pathlib import Path
import geopandas as gpd
import pandas as pd


def load_detections(data_dir: Path, subfolder: str) -> pd.DataFrame:
    subfolder_dir = data_dir / "detections" / subfolder
    csv_paths = sorted(subfolder_dir.glob("*.csv"))

    if not csv_paths:
        return pd.DataFrame()

    frames = []
    for csv_path in csv_paths:
        #only reads and renames column conf
        df = pd.read_csv(csv_path, usecols=["conf"])
        df = df.rename(columns={"conf": "confidence"})
        # adds new column file_name
        df = df.assign(file_name=csv_path.stem)
        frames.append(df)
    
    #concatenates all the dataframes into one (all detections with their confidence values and file names)
    return pd.concat(frames, ignore_index=True)




def load_footprints(data_dir: Path) -> gpd.GeoDataFrame:
    footprints_dir = data_dir / "image_footprints"
    shp_paths = sorted(footprints_dir.glob("*.shp"))

    if not shp_paths:
        return gpd.GeoDataFrame()

    frames = []

    for shp_path in shp_paths:
        shp_gdf = gpd.read_file(shp_path)
        if "file_name" not in shp_gdf.columns:
            shp_gdf = shp_gdf.assign(file_name=shp_path.stem)
        frames.append(shp_gdf)
    #concatenates all geodataframes into one(with file_name and geometry)
    return pd.concat(frames, ignore_index=True)



def load_field_boundary(data_dir: Path) -> gpd.GeoDataFrame:
    boundary_path = data_dir / "field_boundary" / "field_boundary.shp"

    if not boundary_path.exists():
        return gpd.GeoDataFrame()

    return gpd.read_file(boundary_path)
