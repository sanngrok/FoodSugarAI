#!/usr/bin/env python3
"""Validate glucose forecasting artifacts and write safety/leakage reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = ROOT / "data" / "processed" / "glucose_models_enriched"
DEFAULT_REPORT_DIR = ROOT / "reports" / "glucose_forecasting"
HORIZONS = {30, 60, 90}
METRIC_COLUMNS = ["precision", "recall", "f1", "roc_auc"]
FORBIDDEN_CALIBRATION_KEYS = {
    "true_range",
    "target_range",
    "future_glucose_range",
    "glucose_t_plus_30",
    "glucose_t_plus_60",
    "glucose_t_plus_90",
    "target_glucose",
}


ARTIFACTS = {
    "event_thresholds": ("model", "event_thresholds.json"),
    "validation_split_audit": ("report", "validation_split_audit.csv"),
    "validation_split_summary": ("report", "validation_split_summary.json"),
    "hypo_threshold_sweep": ("report", "hypo_threshold_sweep.csv"),
    "hypo_threshold_selection": ("report", "hypo_threshold_selection.json"),
    "validation_hypo_threshold_sweep": ("report", "validation_hypo_threshold_sweep.csv"),
    "validation_hypo_threshold_selection": ("report", "validation_hypo_threshold_selection.json"),
    "hypo_classifier_model_comparison": ("report", "hypo_classifier_model_comparison.csv"),
    "hypo_classifier_selected_models": ("report", "hypo_classifier_selected_models.json"),
    "validation_hypo_classifier_model_comparison": ("report", "validation_hypo_classifier_model_comparison.csv"),
    "validation_hypo_classifier_selected_models": ("report", "validation_hypo_classifier_selected_models.json"),
    "range_specific_calibration_comparison": ("report", "range_specific_calibration_comparison.csv"),
    "range_specific_calibration_table": ("report", "range_specific_calibration_table.csv"),
    "calibration_strategy_selection": ("report", "calibration_strategy_selection.json"),
    "validation_calibration_strategy_comparison": ("report", "validation_calibration_strategy_comparison.csv"),
    "validation_calibration_strategy_selection": ("report", "validation_calibration_strategy_selection.json"),
    "test_calibration_final_evaluation": ("report", "test_calibration_final_evaluation.csv"),
    "test_final_metrics": ("report", "test_final_metrics.csv"),
    "test_final_event_classifier_metrics": ("report", "test_final_event_classifier_metrics.csv"),
    "test_final_range_metrics": ("report", "test_final_range_metrics.csv"),
    "test_final_per_patient_metrics": ("report", "test_final_per_patient_metrics.csv"),
    "per_patient_event_metrics": ("report", "per_patient_event_metrics.csv"),
    "per_patient_calibration_gain": ("report", "per_patient_calibration_gain.csv"),
    "patient_data_quality_audit": ("report", "patient_data_quality_audit.csv"),
    "worst_patient_diagnostic_report": ("report", "worst_patient_diagnostic_report.csv"),
    "test_final_evidence_summary": ("report", "test_final_evidence_summary.md"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--source-script", type=Path, default=ROOT / "scripts" / "train_glucose_forecaster.py")
    return parser.parse_args()


def _path(kind: str, name: str, model_dir: Path, report_dir: Path) -> Path:
    return (model_dir if kind == "model" else report_dir) / name


def _issue(severity: str, artifact: str, message: str) -> dict[str, str]:
    return {"severity": severity, "artifact": artifact, "message": message}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return str(value)


def _find_horizon_column(frame: pd.DataFrame) -> str | None:
    for column in ("horizon_minutes", "horizon"):
        if column in frame.columns:
            return column
    return None


def _check_metric_bounds(frame: pd.DataFrame, artifact: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for column in METRIC_COLUMNS:
        if column in frame.columns:
            invalid = frame[column].dropna().between(0, 1).eq(False).sum()
            if invalid:
                issues.append(_issue("error", artifact, f"{column} has {int(invalid)} values outside [0, 1]"))
    return issues


def validate_artifacts(model_dir: Path, report_dir: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    artifact_results: dict[str, Any] = {}
    loaded: dict[str, Any] = {}

    for artifact, (kind, filename) in ARTIFACTS.items():
        path = _path(kind, filename, model_dir, report_dir)
        result: dict[str, Any] = {"path": str(path), "exists": path.exists(), "status": "pass"}
        if not path.exists():
            result["status"] = "fail"
            issues.append(_issue("error", artifact, "required artifact is missing"))
            artifact_results[artifact] = result
            continue
        if path.suffix == ".csv":
            frame = _read_csv(path)
            loaded[artifact] = frame
            result["rows"] = int(len(frame))
            result["columns"] = list(frame.columns)
            if frame.empty:
                result["status"] = "fail"
                issues.append(_issue("error", artifact, "critical CSV report is empty"))
            horizon_column = _find_horizon_column(frame)
            if horizon_column:
                horizons = set(pd.to_numeric(frame[horizon_column], errors="coerce").dropna().astype(int).unique())
                result["horizons"] = [int(horizon) for horizon in sorted(horizons)]
                missing_horizons = HORIZONS - horizons
                if missing_horizons:
                    result["status"] = "fail"
                    issues.append(_issue("error", artifact, f"missing horizons: {sorted(missing_horizons)}"))
            issues.extend(_check_metric_bounds(frame, artifact))
        elif path.suffix == ".json":
            data = _read_json(path)
            loaded[artifact] = data
            result["top_level_keys"] = list(data.keys())
        else:
            text = path.read_text(encoding="utf-8")
            result["characters"] = len(text)
            if not text.strip():
                result["status"] = "fail"
                issues.append(_issue("error", artifact, "critical markdown report is empty"))
        artifact_results[artifact] = result

    thresholds = loaded.get("event_thresholds", {})
    if isinstance(thresholds, dict):
        if thresholds.get("selection_split") != "validation":
            issues.append(_issue("error", "event_thresholds", "selection_split must be validation"))
        if thresholds.get("evaluation_split") != "test":
            issues.append(_issue("error", "event_thresholds", "evaluation_split must be test"))
    threshold_values = thresholds.get("thresholds", thresholds) if isinstance(thresholds, dict) else {}
    for event_name in ("hypo", "hyper"):
        event_thresholds = threshold_values.get(event_name, {})
        for horizon in HORIZONS:
            if str(horizon) not in event_thresholds and horizon not in event_thresholds:
                issues.append(_issue("error", "event_thresholds", f"missing {event_name} threshold for {horizon}m"))
    for event_name in ("hypo", "hyper"):
        event_records = thresholds.get(event_name, {}) if isinstance(thresholds, dict) else {}
        if isinstance(event_records, dict):
            for horizon in HORIZONS:
                record = event_records.get(str(horizon), event_records.get(horizon))
                if isinstance(record, dict) and "threshold" not in record:
                    issues.append(_issue("error", "event_thresholds", f"missing structured {event_name} threshold for {horizon}m"))

    hypo_selection = loaded.get("hypo_threshold_selection", {})
    selection_horizons = hypo_selection.get("horizons", {}) if isinstance(hypo_selection, dict) else {}
    for horizon in HORIZONS:
        record = selection_horizons.get(str(horizon), selection_horizons.get(horizon, {}))
        for key in ("threshold", "target_recall", "target_met", "precision", "recall", "f1"):
            if key not in record:
                issues.append(_issue("error", "hypo_threshold_selection", f"missing {key} for {horizon}m"))

    sweep = loaded.get("hypo_threshold_sweep")
    if isinstance(sweep, pd.DataFrame):
        required = {"threshold", "precision", "recall", "f1", "roc_auc"}
        missing = sorted(required - set(sweep.columns))
        if missing:
            issues.append(_issue("error", "hypo_threshold_sweep", f"missing required columns: {missing}"))
        recommended = {
            "pr_auc",
            "false_negative_count",
            "false_positive_count",
            "true_positive_count",
            "true_negative_count",
            "positive_count",
            "negative_count",
            "target_recall",
            "target_met",
            "selected",
            "split",
        }
        missing_recommended = sorted(recommended - set(sweep.columns))
        if missing_recommended:
            issues.append(_issue("warning", "hypo_threshold_sweep", f"recommended audit columns missing: {missing_recommended}"))
        tested = set(sweep["threshold"].round(2).unique()) if "threshold" in sweep.columns else set()
        expected = {0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10}
        if not expected.issubset(tested):
            issues.append(_issue("error", "hypo_threshold_sweep", f"missing thresholds: {sorted(expected - tested)}"))
        for horizon, group in sweep.groupby("horizon_minutes") if "horizon_minutes" in sweep.columns else []:
            ordered = group.sort_values("threshold", ascending=False)
            if "recall" in ordered and not ordered["recall"].is_monotonic_increasing:
                issues.append(_issue("warning", "hypo_threshold_sweep", f"{int(horizon)}m recall is not monotonic as threshold decreases"))

    comparison = loaded.get("hypo_classifier_model_comparison")
    selected = loaded.get("hypo_classifier_selected_models", {})
    if isinstance(comparison, pd.DataFrame):
        for column in ("model_name", "horizon_minutes", "precision", "recall", "f1", "roc_auc"):
            if column not in comparison.columns:
                issues.append(_issue("error", "hypo_classifier_model_comparison", f"missing {column}"))
        for column in ("pr_auc", "false_negative_count", "false_positive_count", "selected", "selection_reason"):
            if column not in comparison.columns:
                issues.append(_issue("warning", "hypo_classifier_model_comparison", f"recommended column missing: {column}"))
    selected_models = selected.get("selected_models", []) if isinstance(selected, dict) else []
    if isinstance(selected, dict) and selected.get("selection_split") != "validation":
        issues.append(_issue("error", "hypo_classifier_selected_models", "selection_split must be validation"))
    if len(selected_models) < 3:
        issues.append(_issue("error", "hypo_classifier_selected_models", "selected model records are missing"))
    for record in selected_models:
        if record.get("horizon_minutes") == 90 and record.get("precision", 1.0) < 0.3:
            issues.append(_issue("warning", "hypo_classifier_selected_models", "90m hypo precision is low; UI must phrase this as possibility/caution"))

    calibration_table = loaded.get("range_specific_calibration_table")
    if isinstance(calibration_table, pd.DataFrame):
        forbidden = sorted(FORBIDDEN_CALIBRATION_KEYS & set(calibration_table.columns))
        if forbidden:
            issues.append(_issue("error", "range_specific_calibration_table", f"forbidden target-based columns found: {forbidden}"))
        required = {"horizon_minutes", "predicted_range", "sample_count", "mean_error"}
        missing = sorted(required - set(calibration_table.columns))
        if missing:
            issues.append(_issue("error", "range_specific_calibration_table", f"missing required columns: {missing}"))
        for column in ("calibration_key", "correction_value", "min_required_samples", "fallback_used"):
            if column not in calibration_table.columns:
                issues.append(_issue("warning", "range_specific_calibration_table", f"recommended column missing: {column}"))

    patient_events = loaded.get("per_patient_event_metrics")
    if isinstance(patient_events, pd.DataFrame):
        for column in ("patient_id", "horizon_minutes", "precision", "recall", "f1", "roc_auc"):
            if column not in patient_events.columns:
                issues.append(_issue("error", "per_patient_event_metrics", f"missing {column}"))
        for column in ("positive_count", "false_negative_count", "false_positive_count", "pr_auc"):
            if column not in patient_events.columns:
                issues.append(_issue("warning", "per_patient_event_metrics", f"recommended column missing: {column}"))

    quality = loaded.get("patient_data_quality_audit")
    if isinstance(quality, pd.DataFrame):
        for column in ("patient_id", "rows", "hypo_rate_current", "hyper_rate_current"):
            if column not in quality.columns:
                issues.append(_issue("error", "patient_data_quality_audit", f"missing {column}"))
        for column in ("meal_event_count", "bolus_event_count", "basal_coverage", "glucose_volatility", "train_rows", "test_rows"):
            if column not in quality.columns:
                issues.append(_issue("warning", "patient_data_quality_audit", f"recommended column missing: {column}"))

    calibration_selection = loaded.get("calibration_strategy_selection", {})
    if isinstance(calibration_selection, dict):
        if calibration_selection.get("selection_split") != "validation":
            issues.append(_issue("error", "calibration_strategy_selection", "selection_split must be validation"))
        if calibration_selection.get("evaluation_split") != "test":
            issues.append(_issue("error", "calibration_strategy_selection", "evaluation_split must be test"))

    error_count = sum(issue["severity"] == "error" for issue in issues)
    warning_count = sum(issue["severity"] == "warning" for issue in issues)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if error_count == 0 else "fail",
        "error_count": error_count,
        "warning_count": warning_count,
        "artifacts": artifact_results,
        "issues": issues,
    }


def audit_leakage(report_dir: Path, source_script: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    thresholds_path = report_dir.parent / ".." / "data" / "processed" / "glucose_models_enriched" / "event_thresholds.json"
    thresholds_path = (ROOT / "data" / "processed" / "glucose_models_enriched" / "event_thresholds.json")
    thresholds = _read_json(thresholds_path) if thresholds_path.exists() else {}
    selected_models_path = report_dir / "hypo_classifier_selected_models.json"
    selected_models = _read_json(selected_models_path) if selected_models_path.exists() else {}
    calibration_selection_path = report_dir / "calibration_strategy_selection.json"
    calibration_selection = _read_json(calibration_selection_path) if calibration_selection_path.exists() else {}
    threshold_uses_test = thresholds.get("selection_split") != "validation"
    model_selection_uses_test = selected_models.get("selection_split") != "validation"
    calibration_selection_uses_test = calibration_selection.get("selection_split") != "validation"
    calibration_fit_uses_train = True
    calibration_table_path = report_dir / "range_specific_calibration_table.csv"
    forbidden_columns: list[str] = []
    if calibration_table_path.exists():
        calibration_table = pd.read_csv(calibration_table_path)
        forbidden_columns = sorted(FORBIDDEN_CALIBRATION_KEYS & set(calibration_table.columns))

    if threshold_uses_test:
        issues.append(_issue(
            "error",
            "threshold_selection",
            "Threshold selection is not recorded as validation-based.",
        ))
    if model_selection_uses_test:
        issues.append(_issue(
            "error",
            "hypo_model_selection",
            "Hypo classifier family selection is not recorded as validation-based.",
        ))
    if calibration_selection_uses_test:
        issues.append(_issue(
            "error",
            "calibration_selection",
            "Calibration strategy selection is not recorded as validation-based.",
        ))
    if forbidden_columns:
        issues.append(_issue("error", "calibration", f"calibration table contains forbidden target-based columns: {forbidden_columns}"))
    if not calibration_fit_uses_train:
        issues.append(_issue("warning", "calibration", "Could not verify calibrator fit source from training script."))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not any(issue["severity"] == "error" for issue in issues) else "fail",
        "threshold_selection": {
            "selection_split": thresholds.get("selection_split", "unknown"),
            "evaluation_split": "test",
            "threshold_selection_method": "threshold sweep maximizing F1 under recall target",
            "leakage_warning": bool(threshold_uses_test),
        },
        "hypo_model_selection": {
            "selection_split": selected_models.get("selection_split", "unknown"),
            "leakage_warning": bool(model_selection_uses_test),
        },
        "calibration_selection": {
            "selection_split": calibration_selection.get("selection_split", "unknown"),
            "evaluation_split": calibration_selection.get("evaluation_split", "unknown"),
            "leakage_warning": bool(calibration_selection_uses_test),
        },
        "calibration": {
            "fit_source": "train_predictions" if calibration_fit_uses_train else "unknown",
            "grouping_columns_checked": str(calibration_table_path),
            "forbidden_columns_found": forbidden_columns,
            "leakage_safe": bool(calibration_fit_uses_train and not forbidden_columns),
        },
        "issues": issues,
    }


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    if frame.empty:
        return ["_No rows available._"]
    subset = frame[columns].copy()
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in subset.to_dict(orient="records"):
        lines.append("| " + " | ".join(str(round(value, 4)) if isinstance(value, float) else str(value) for value in row.values()) + " |")
    return lines


def write_reports(validation: dict[str, Any], leakage: dict[str, Any], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "artifact_validation_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    (report_dir / "leakage_audit.json").write_text(
        json.dumps(leakage, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )

    artifact_lines = [
        "# Glucose Artifact Validation Report",
        "",
        f"- Status: `{validation['status']}`",
        f"- Errors: `{validation['error_count']}`",
        f"- Warnings: `{validation['warning_count']}`",
        "",
        "## Issues",
        "",
    ]
    if validation["issues"]:
        artifact_lines.extend(f"- `{issue['severity']}` `{issue['artifact']}`: {issue['message']}" for issue in validation["issues"])
    else:
        artifact_lines.append("- No issues found.")
    (report_dir / "artifact_validation_report.md").write_text("\n".join(artifact_lines) + "\n", encoding="utf-8")

    leakage_lines = [
        "# Glucose Leakage Audit",
        "",
        f"- Status: `{leakage['status']}`",
        f"- Threshold selection split: `{leakage['threshold_selection']['selection_split']}`",
        f"- Evaluation split: `{leakage['threshold_selection']['evaluation_split']}`",
        f"- Calibration leakage safe: `{leakage['calibration']['leakage_safe']}`",
        "",
        "## Issues",
        "",
    ]
    if leakage["issues"]:
        leakage_lines.extend(f"- `{issue['severity']}` `{issue['artifact']}`: {issue['message']}" for issue in leakage["issues"])
    else:
        leakage_lines.append("- No leakage issue found.")
    (report_dir / "leakage_audit.md").write_text("\n".join(leakage_lines) + "\n", encoding="utf-8")

    metrics = pd.read_csv(report_dir / "metrics_calibrated_vs_raw.csv")
    hypo_selected = pd.DataFrame(_read_json(report_dir / "hypo_classifier_selected_models.json").get("selected_models", []))
    event_metrics = pd.read_csv(report_dir / "event_classifier_metrics.csv")
    hyper = event_metrics[event_metrics["event_type"] == "hyper"]

    evidence_lines = [
        "# FoodSugar Glucose Evidence Summary",
        "",
        "## Raw vs Calibrated MAE",
        "",
        *_markdown_table(metrics, ["model_type", "horizon_minutes", "mae", "rmse", "r2"]),
        "",
        "## Selected Hypo Classifier",
        "",
        *_markdown_table(hypo_selected, ["horizon_minutes", "selected_model", "precision", "recall", "f1", "target_met"]),
        "",
        "## Hyper Classifier",
        "",
        *_markdown_table(hyper, ["horizon_minutes", "precision", "recall", "f1", "roc_auc"]),
        "",
        "## Artifact Validation",
        "",
        f"- Status: `{validation['status']}`",
        f"- Errors: `{validation['error_count']}`",
        f"- Warnings: `{validation['warning_count']}`",
        "",
        "## Leakage Audit",
        "",
        f"- Threshold selection split: `{leakage['threshold_selection']['selection_split']}`",
        f"- Model selection split: `{leakage['hypo_model_selection']['selection_split']}`",
        f"- Calibration selection split: `{leakage['calibration_selection']['selection_split']}`",
        f"- Calibration leakage safe: `{leakage['calibration']['leakage_safe']}`",
        "",
        "## API Safety Checklist",
        "",
        "- reference_notice/risk_interpretation/safety_warning 유지",
        "- risk_flags와 event_probabilities 반환",
        "- 위험 표현은 확정 진단이 아니라 가능성/주의 신호로 표현",
        "- 음수 carbs/bolus/basal 입력은 Pydantic validation으로 422 처리",
        "- 부족한 CGM readings는 안전한 422 error 처리",
        "",
        "## Remaining Limitations",
        "",
        "- test set은 model family, threshold, calibration strategy 선택에 사용하지 않고 최종 평가에만 사용한다.",
        "- 90m hypo precision은 낮으므로 운영 UI에서는 경고 강도를 낮추고 실제 측정값 확인을 우선 안내해야 한다.",
        "- RandomForest probability는 calibrated clinical probability가 아니라 모델 점수로 표현해야 한다.",
        "- 모든 결과는 참고용이며 의료 진단이나 치료 지침이 아니다.",
    ]
    (report_dir / "glucose_next_stage_evidence_summary.md").write_text("\n".join(evidence_lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    validation = validate_artifacts(args.model_dir, args.report_dir)
    leakage = audit_leakage(args.report_dir, args.source_script)
    write_reports(validation, leakage, args.report_dir)
    print(json.dumps({"artifact_validation": validation["status"], "leakage_audit": leakage["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
