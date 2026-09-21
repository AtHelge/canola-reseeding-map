import pandas as pd

from canola_map.join import aggregate_per_frame


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
