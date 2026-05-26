import json
from pathlib import Path

import pandas as pd


def test_prediction_interval_reports_exist():
    required = [
        "reports/glucose_forecasting/prediction_interval_metrics.csv",
        "reports/glucose_forecasting/conformal_coverage_report.csv",
        "reports/glucose_forecasting/uncertainty_by_horizon.csv",
        "data/processed/glucose_models_enriched/prediction_intervals.json",
    ]

    for path in required:
        assert Path(path).exists(), path


def test_prediction_intervals_cover_all_horizons():
    config = json.loads(Path("data/processed/glucose_models_enriched/prediction_intervals.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv("reports/glucose_forecasting/prediction_interval_metrics.csv")

    assert {"30", "60", "90"}.issubset(set(config["intervals"]))
    assert {30, 60, 90}.issubset(set(metrics["horizon_minutes"]))
    assert {"observed_coverage", "mean_interval_width", "uncertainty_level"}.issubset(metrics.columns)
