import pandas as pd


def aggregate_per_frame(detections_df: pd.DataFrame, conf_threshold: float) -> pd.DataFrame:
    filtered = detections_df[detections_df["confidence"] >= conf_threshold]
    return filtered.groupby("file_name").size().reset_index(name="detection_count")
