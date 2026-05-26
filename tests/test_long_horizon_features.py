from pathlib import Path

import joblib
import pandas as pd


def test_long_horizon_feature_reports_exist():
    required = [
        "reports/glucose_forecasting/horizon_feature_set_comparison.csv",
        "reports/glucose_forecasting/long_window_feature_importance.csv",
        "reports/glucose_forecasting/long_window_model_metrics.csv",
    ]

    for path in required:
        assert Path(path).exists(), path


def test_long_horizon_metadata_contains_proxy_features():
    metadata = joblib.load("data/processed/glucose_models_enriched/metadata.joblib")
    features = set(metadata["feature_columns"])

    assert metadata["model_type"] == "enriched_long_horizon"
    assert "carbs_on_board_proxy" in features
    assert "glucose_slope_120m" in features
    assert "recent_low_event_count_180m" in features


def test_long_window_model_metrics_include_60_90():
    metrics = pd.read_csv("reports/glucose_forecasting/long_window_model_metrics.csv")

    assert {60, 90}.issubset(set(metrics["horizon_minutes"]))
    assert {"enriched", "enriched_calibrated"}.issubset(set(metrics["model_type"]))
