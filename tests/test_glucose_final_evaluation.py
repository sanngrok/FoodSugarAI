import json
from pathlib import Path

import pandas as pd


def test_validation_based_reports_exist():
    required = [
        "reports/glucose_forecasting/validation_hypo_classifier_model_comparison.csv",
        "reports/glucose_forecasting/validation_hypo_classifier_selected_models.json",
        "reports/glucose_forecasting/validation_hypo_threshold_sweep.csv",
        "reports/glucose_forecasting/validation_hypo_threshold_selection.json",
        "reports/glucose_forecasting/validation_calibration_strategy_comparison.csv",
        "reports/glucose_forecasting/validation_calibration_strategy_selection.json",
        "reports/glucose_forecasting/test_calibration_final_evaluation.csv",
        "reports/glucose_forecasting/test_final_metrics.csv",
        "reports/glucose_forecasting/test_final_event_classifier_metrics.csv",
        "reports/glucose_forecasting/test_final_range_metrics.csv",
        "reports/glucose_forecasting/test_final_per_patient_metrics.csv",
        "reports/glucose_forecasting/test_final_evidence_summary.md",
    ]

    for path in required:
        assert Path(path).exists(), path


def test_event_thresholds_record_validation_selection_and_test_evaluation():
    thresholds = json.loads(Path("data/processed/glucose_models_enriched/event_thresholds.json").read_text(encoding="utf-8"))

    assert thresholds["selection_split"] == "validation"
    assert thresholds["evaluation_split"] == "test"
    assert thresholds["created_by"] == "validation_based_threshold_selection"
    for horizon in ["30", "60", "90"]:
        assert "threshold" in thresholds["hypo"][horizon]
        assert "validation_recall" in thresholds["hypo"][horizon]
        assert thresholds["hypo"][horizon]["target_met"] is True


def test_final_event_metrics_are_test_only_and_include_pr_auc_counts():
    metrics = pd.read_csv("reports/glucose_forecasting/test_final_event_classifier_metrics.csv")

    assert set(metrics["split"].unique()) == {"test"}
    assert {"hypo", "hyper"}.issubset(set(metrics["event_type"]))
    assert {30, 60, 90}.issubset(set(metrics["horizon_minutes"]))
    assert {"pr_auc", "false_negative_count", "false_positive_count", "positive_count"}.issubset(metrics.columns)


def test_final_evidence_summary_documents_no_test_selection():
    evidence = Path("reports/glucose_forecasting/test_final_evidence_summary.md").read_text(encoding="utf-8")

    assert "model/threshold selection split: `validation`" in evidence
    assert "evaluation split: `test`" in evidence
    assert "test used for selection: `False`" in evidence
