from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.glucose.forecasting import (
    clear_forecast_model_cache,
    forecast_model_cache_load_count,
    load_event_classifiers_cached,
    load_event_thresholds_cached,
    load_forecast_models_cached,
    load_range_calibrators_cached,
)


class ConstantForecastModel:
    def __init__(self, value: float):
        self.value = value

    def predict(self, x):
        return np.full(len(x), self.value)


def test_forecasting_reports_are_created():
    required = [
        "reports/glucose_forecasting/metrics_baseline_vs_enriched.csv",
        "reports/glucose_forecasting/metrics_calibrated_vs_raw.csv",
        "reports/glucose_forecasting/range_calibration_table.csv",
        "reports/glucose_forecasting/range_specific_calibration_comparison.csv",
        "reports/glucose_forecasting/range_specific_calibration_table.csv",
        "reports/glucose_forecasting/calibration_strategy_selection.json",
        "reports/glucose_forecasting/event_classifier_metrics.csv",
        "reports/glucose_forecasting/hypo_threshold_sweep.csv",
        "reports/glucose_forecasting/hypo_threshold_selection.json",
        "reports/glucose_forecasting/hypo_classifier_model_comparison.csv",
        "reports/glucose_forecasting/hypo_classifier_selected_models.json",
        "reports/glucose_forecasting/summary_baseline_vs_enriched.json",
        "reports/glucose_forecasting/per_patient_metrics.csv",
        "reports/glucose_forecasting/per_patient_horizon_metrics.csv",
        "reports/glucose_forecasting/per_patient_event_metrics.csv",
        "reports/glucose_forecasting/per_patient_calibration_gain.csv",
        "reports/glucose_forecasting/patient_data_quality_audit.csv",
        "reports/glucose_forecasting/worst_patient_diagnostic_report.csv",
        "reports/glucose_forecasting/worst_patients.csv",
        "reports/glucose_forecasting/best_patients.csv",
        "reports/glucose_forecasting/per_glucose_range_metrics.csv",
        "reports/glucose_forecasting/hypoglycemia_case_errors.csv",
        "reports/glucose_forecasting/hyperglycemia_case_errors.csv",
        "data/processed/glucose_models_enriched/event_thresholds.json",
    ]

    for path in required:
        assert Path(path).exists(), path


def test_enriched_metrics_include_baselines_and_improvement():
    metrics = pd.read_csv("reports/glucose_forecasting/metrics_baseline_vs_enriched.csv")

    assert {"persistence", "history", "enriched"}.issubset(set(metrics["model_type"]))
    assert {30, 60, 90}.issubset(set(metrics["horizon_minutes"]))
    enriched = metrics[metrics["model_type"] == "enriched"]
    assert (enriched["mae_improvement_vs_history_pct"] > 0).all()


def test_calibrated_metrics_are_present():
    metrics = pd.read_csv("reports/glucose_forecasting/metrics_calibrated_vs_raw.csv")

    assert {"enriched", "enriched_calibrated"}.issubset(set(metrics["model_type"]))
    assert {30, 60, 90}.issubset(set(metrics["horizon_minutes"]))


def test_event_classifier_metrics_are_present():
    metrics = pd.read_csv("reports/glucose_forecasting/event_classifier_metrics.csv")

    assert {"hypo", "hyper"}.issubset(set(metrics["event_type"]))
    assert {30, 60, 90}.issubset(set(metrics["horizon_minutes"]))
    assert {"precision", "recall", "f1", "roc_auc"}.issubset(metrics.columns)


def test_hypo_threshold_selection_is_present():
    sweep = pd.read_csv("reports/glucose_forecasting/hypo_threshold_sweep.csv")

    assert {0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1}.issubset(set(sweep["threshold"].round(2)))
    assert {30, 60, 90}.issubset(set(sweep["horizon_minutes"]))
    assert {"precision", "recall", "f1"}.issubset(sweep.columns)


def test_glucose_range_metrics_include_low_normal_high():
    metrics = pd.read_csv("reports/glucose_forecasting/per_glucose_range_metrics.csv")

    assert {"low", "normal", "high"}.issubset(set(metrics["range_name"]))
    assert {"under_prediction_rate", "over_prediction_rate"}.issubset(metrics.columns)


def test_forecast_model_cache_reuses_loaded_models(tmp_path):
    clear_forecast_model_cache()
    for horizon, value in [(30, 120), (60, 140), (90, 160)]:
        joblib.dump(ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")

    first = load_forecast_models_cached(tmp_path)
    second = load_forecast_models_cached(tmp_path)

    assert first is second
    assert sorted(first) == [30, 60, 90]
    assert forecast_model_cache_load_count(tmp_path) == 1


def test_calibrator_and_event_classifier_cache(tmp_path):
    clear_forecast_model_cache()
    (tmp_path / "range_calibrators.json").write_text(
        '[{"horizon_minutes":30,"predicted_range":"normal","mean_error":2.0}]',
        encoding="utf-8",
    )
    joblib.dump(ConstantForecastModel(0), tmp_path / "glucose_event_hypo_30m.joblib")
    (tmp_path / "event_thresholds.json").write_text(
        '{"thresholds":{"hypo":{"30":0.2},"hyper":{"30":0.5}}}',
        encoding="utf-8",
    )

    first_cal = load_range_calibrators_cached(tmp_path)
    second_cal = load_range_calibrators_cached(tmp_path)
    first_events = load_event_classifiers_cached(tmp_path)
    second_events = load_event_classifiers_cached(tmp_path)
    first_thresholds = load_event_thresholds_cached(tmp_path)
    second_thresholds = load_event_thresholds_cached(tmp_path)

    assert first_cal is second_cal
    assert first_events is second_events
    assert first_thresholds is second_thresholds
    assert first_thresholds["hypo"][30] == 0.2
    assert "hypo" in first_events
