from pathlib import Path

import pandas as pd


def test_patient_specific_reports_exist():
    required = [
        "reports/glucose_forecasting/patient_specific_vs_global.csv",
        "reports/glucose_forecasting/horizon_patient_gain.csv",
        "reports/glucose_forecasting/worst_patient_60_90_diagnosis.csv",
        "reports/glucose_forecasting/patient_specific_summary.md",
    ]

    for path in required:
        assert Path(path).exists(), path


def test_patient_specific_comparison_has_long_horizons():
    comparison = pd.read_csv("reports/glucose_forecasting/patient_specific_vs_global.csv")

    assert {60, 90}.issubset(set(comparison["horizon_minutes"]))
    assert "patient_id" in comparison.columns
    assert "mae" in comparison.columns
