#!/usr/bin/env python3
"""Train 30/60/90 minute CGM forecasting models and write an evaluation report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, precision_recall_fscore_support, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.glucose.constants import GLUCOSE_REFERENCE_NOTICE
from src.glucose.forecasting import (
    DEFAULT_HORIZONS_MINUTES,
    ENRICHED_FEATURE_COLUMNS,
    HISTORY_FEATURE_COLUMNS,
    LONG_HORIZON_ENRICHED_FEATURE_COLUMNS,
    LONG_HORIZON_FEATURE_COLUMNS,
    apply_range_calibration,
    build_training_table,
    evaluate_event_classifiers,
    fit_range_calibrators,
    glucose_range_metrics,
    metrics_from_predictions,
    per_patient_metrics,
    persistence_predictions,
    predict_forecast_models,
    save_event_classifiers,
    save_forecast_models,
    save_range_calibrators,
    train_event_classifiers,
    train_forecast_models,
)


HYPO_THRESHOLDS = [0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10]
HYPO_RECALL_TARGETS = {30: 0.65, 60: 0.40, 90: 0.25}


def _resolved_features(frame: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    return [column for column in feature_columns if column in frame.columns]


def _event_binary_metrics(y_true, y_prob, threshold: float) -> dict[str, float]:
    y_pred = (y_prob >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    )
    try:
        auc = roc_auc_score(y_true, y_prob)
    except ValueError:
        auc = float("nan")
    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except ValueError:
        pr_auc = float("nan")
    true_positive = int(((y_true == 1) & (y_pred == 1)).sum())
    true_negative = int(((y_true == 0) & (y_pred == 0)).sum())
    false_positive = int(((y_true == 0) & (y_pred == 1)).sum())
    false_negative = int(((y_true == 1) & (y_pred == 0)).sum())
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(auc),
        "pr_auc": float(pr_auc),
        "true_positive_count": true_positive,
        "true_negative_count": true_negative,
        "false_positive_count": false_positive,
        "false_negative_count": false_negative,
        "positive_count": int((y_true == 1).sum()),
        "negative_count": int((y_true == 0).sum()),
        "positive_predictions": int(y_pred.sum()),
    }


def _predict_probability(model, x_eval):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x_eval)[:, 1]
    return model.predict(x_eval)


def make_time_based_validation_split(
    train_frame: pd.DataFrame,
    validation_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    train_inner_parts: list[pd.DataFrame] = []
    validation_parts: list[pd.DataFrame] = []
    audit_rows: list[dict[str, object]] = []
    group_columns = [column for column in ["source_file", "patient_id", "year"] if column in train_frame.columns]
    if not group_columns:
        group_columns = ["patient_id"] if "patient_id" in train_frame.columns else []
    grouped = train_frame.groupby(group_columns, sort=False) if group_columns else [(("all",), train_frame)]
    for group_key, group in grouped:
        sorted_group = group.sort_values("timestamp").copy()
        split_index = max(1, int(len(sorted_group) * (1.0 - validation_fraction)))
        if split_index >= len(sorted_group):
            split_index = max(1, len(sorted_group) - 1)
        inner = sorted_group.iloc[:split_index].copy()
        validation = sorted_group.iloc[split_index:].copy()
        inner["inner_split"] = "train_inner"
        validation["inner_split"] = "validation"
        train_inner_parts.append(inner)
        validation_parts.append(validation)
        group_values = group_key if isinstance(group_key, tuple) else (group_key,)
        audit_row = {column: value for column, value in zip(group_columns, group_values)}
        audit_row.update({
            "raw_rows": int(len(sorted_group)),
            "train_inner_rows": int(len(inner)),
            "validation_rows": int(len(validation)),
            "train_inner_start": str(inner["timestamp"].min()),
            "train_inner_end": str(inner["timestamp"].max()),
            "validation_start": str(validation["timestamp"].min()),
            "validation_end": str(validation["timestamp"].max()),
            "time_order_safe": bool(inner["timestamp"].max() <= validation["timestamp"].min()),
        })
        audit_rows.append(audit_row)
    train_inner_frame = pd.concat(train_inner_parts, ignore_index=True)
    validation_frame = pd.concat(validation_parts, ignore_index=True)
    audit = pd.DataFrame(audit_rows)
    summary = {
        "method": "time_based_per_source_patient_year",
        "validation_fraction": validation_fraction,
        "source_split": "train",
        "test_split_used_for_selection": False,
        "train_inner_rows": int(len(train_inner_frame)),
        "validation_rows": int(len(validation_frame)),
        "groups": int(len(audit)),
        "time_order_safe": bool(audit["time_order_safe"].all()) if not audit.empty else True,
    }
    return train_inner_frame, validation_frame, audit, summary


def train_weighted_hypo_candidates(
    base_classifiers: dict[str, dict[int, object]],
    train_table: pd.DataFrame,
    selection_table: pd.DataFrame,
    horizons: list[int],
    feature_columns: list[str],
    selection_split: str = "validation",
) -> tuple[dict[str, dict[int, object]], pd.DataFrame, list[dict[str, object]]]:
    features = _resolved_features(train_table, feature_columns)
    x_train = train_table[features].to_numpy(dtype="float32")
    x_selection = selection_table[features].to_numpy(dtype="float32")
    comparison_rows: list[dict[str, object]] = []
    selected_rows: list[dict[str, object]] = []

    for horizon in horizons:
        y_train = (train_table[f"target_{horizon}m"] < 70).astype(int).to_numpy()
        y_selection = (selection_table[f"target_{horizon}m"] < 70).astype(int).to_numpy()
        positive_count = int(y_train.sum())
        negative_count = int(len(y_train) - positive_count)
        positive_weight = negative_count / max(positive_count, 1)
        sample_weight = pd.Series(y_train).map({0: 1.0, 1: positive_weight}).to_numpy()

        candidates: dict[str, object] = {
            "hist_gradient_boosting_default": base_classifiers["hypo"][int(horizon)],
            "hist_gradient_boosting_weighted": HistGradientBoostingClassifier(
                max_iter=140,
                learning_rate=0.06,
                max_leaf_nodes=31,
                l2_regularization=0.02,
                random_state=20260522 + int(horizon),
            ),
            "random_forest_balanced": RandomForestClassifier(
                n_estimators=120,
                max_depth=16,
                min_samples_leaf=4,
                class_weight="balanced",
                n_jobs=-1,
                random_state=20260523 + int(horizon),
            ),
            "logistic_regression_balanced": make_pipeline(
                StandardScaler(),
                LogisticRegression(class_weight="balanced", max_iter=1000, random_state=20260524 + int(horizon)),
            ),
        }
        candidates["hist_gradient_boosting_weighted"].fit(x_train, y_train, sample_weight=sample_weight)
        candidates["random_forest_balanced"].fit(x_train, y_train)
        candidates["logistic_regression_balanced"].fit(x_train, y_train)

        scored: list[dict[str, object]] = []
        for model_name, model in candidates.items():
            y_prob = _predict_probability(model, x_selection)
            metrics = _event_binary_metrics(y_selection, y_prob, threshold=0.5)
            row = {
                "event_type": "hypo",
                "horizon_minutes": int(horizon),
                "model_name": model_name,
                "threshold": 0.5,
                "samples": int(len(y_selection)),
                "selection_split": selection_split,
                "positive_rate": float(y_selection.mean()),
                **metrics,
            }
            comparison_rows.append(row)
            scored.append({**row, "model": model})

        target_recall = HYPO_RECALL_TARGETS.get(int(horizon), 0.4)
        eligible = [row for row in scored if float(row["recall"]) >= target_recall]
        pool = eligible if eligible else scored
        selected = sorted(
            pool,
            key=lambda row: (
                float(row["pr_auc"]),
                float(row["f1"]),
                -float(row["false_negative_count"]),
                float(row["recall"]),
            ),
            reverse=True,
        )[0]
        base_classifiers["hypo"][int(horizon)] = selected["model"]
        for row in comparison_rows:
            if row["horizon_minutes"] == int(horizon):
                row["selected"] = bool(row["model_name"] == selected["model_name"])
                row["selection_reason"] = (
                    "met recall target; selected by validation PR-AUC/F1/false negatives"
                    if float(selected["recall"]) >= target_recall
                    else "recall target not met; selected by best validation PR-AUC/F1"
                )
        selected_rows.append({
            "event_type": "hypo",
            "horizon_minutes": int(horizon),
            "selected_model": selected["model_name"],
            "selection_threshold": 0.5,
            "selection_split": selection_split,
            "evaluation_split": "test",
            "target_recall": target_recall,
            "target_met": bool(float(selected["recall"]) >= target_recall),
            "precision": float(selected["precision"]),
            "recall": float(selected["recall"]),
            "f1": float(selected["f1"]),
            "roc_auc": float(selected["roc_auc"]),
            "pr_auc": float(selected["pr_auc"]),
            "false_negative_count": int(selected["false_negative_count"]),
            "false_positive_count": int(selected["false_positive_count"]),
        })

    return base_classifiers, pd.DataFrame(comparison_rows), selected_rows


def sweep_hypo_thresholds(
    classifiers: dict[str, dict[int, object]],
    eval_table: pd.DataFrame,
    horizons: list[int],
    feature_columns: list[str],
    selection_split: str = "validation",
) -> tuple[pd.DataFrame, dict[str, object]]:
    features = _resolved_features(eval_table, feature_columns)
    x_eval = eval_table[features].to_numpy(dtype="float32")
    rows: list[dict[str, object]] = []
    selections: dict[str, dict[str, object]] = {}
    for horizon in horizons:
        y_true = (eval_table[f"target_{horizon}m"] < 70).astype(int).to_numpy()
        y_prob = _predict_probability(classifiers["hypo"][int(horizon)], x_eval)
        horizon_rows = []
        for threshold in HYPO_THRESHOLDS:
            metrics = _event_binary_metrics(y_true, y_prob, threshold)
            row = {
                "event_type": "hypo",
                "event": "hypo",
                "horizon_minutes": int(horizon),
                "threshold": threshold,
                "split": selection_split,
                "samples": int(len(y_true)),
                "positive_rate": float(y_true.mean()),
                **metrics,
            }
            rows.append(row)
            horizon_rows.append(row)
        target_recall = HYPO_RECALL_TARGETS.get(int(horizon), 0.4)
        for row in horizon_rows:
            row["target_recall"] = target_recall
            row["target_met"] = bool(float(row["recall"]) >= target_recall)
        eligible = [row for row in horizon_rows if float(row["recall"]) >= target_recall]
        pool = eligible if eligible else horizon_rows
        selected = sorted(pool, key=lambda row: (float(row["f1"]), float(row["precision"]), -float(row["threshold"])), reverse=True)[0]
        for row in horizon_rows:
            row["selected"] = bool(row["threshold"] == selected["threshold"])
        selections[str(int(horizon))] = {
            "threshold": float(selected["threshold"]),
            "target_recall": target_recall,
            "target_met": bool(float(selected["recall"]) >= target_recall),
            "selection_split": selection_split,
            "evaluation_split": "test",
            "precision": float(selected["precision"]),
            "recall": float(selected["recall"]),
            "f1": float(selected["f1"]),
            "roc_auc": float(selected["roc_auc"]),
            "pr_auc": float(selected["pr_auc"]),
            "false_negative_count": int(selected["false_negative_count"]),
            "false_positive_count": int(selected["false_positive_count"]),
        }
    selection_json = {
        "event_type": "hypo",
        "selection_split": selection_split,
        "evaluation_split": "test",
        "thresholds_tested": HYPO_THRESHOLDS,
        "selection_rule": "choose highest F1 among thresholds meeting horizon recall target; fallback to best F1 if target is not met",
        "horizons": selections,
    }
    return pd.DataFrame(rows), selection_json


def patient_event_metrics(
    classifiers: dict[str, dict[int, object]],
    eval_table: pd.DataFrame,
    horizons: list[int],
    feature_columns: list[str],
    thresholds: dict[str, dict[int, float]],
) -> pd.DataFrame:
    features = _resolved_features(eval_table, feature_columns)
    x_eval = eval_table[features].to_numpy(dtype="float32")
    rows: list[dict[str, object]] = []
    for event_type in ("hypo", "hyper"):
        for horizon in horizons:
            y_true_all = (
                (eval_table[f"target_{horizon}m"] < 70)
                if event_type == "hypo"
                else (eval_table[f"target_{horizon}m"] > 180)
            ).astype(int).to_numpy()
            y_prob_all = _predict_probability(classifiers[event_type][int(horizon)], x_eval)
            threshold = thresholds.get(event_type, {}).get(int(horizon), 0.5)
            temp = eval_table[["patient_id", "year", "split"]].copy()
            temp["y_true"] = y_true_all
            temp["y_prob"] = y_prob_all
            for (patient_id, year), group in temp.groupby(["patient_id", "year"]):
                metrics = _event_binary_metrics(group["y_true"].to_numpy(), group["y_prob"].to_numpy(), threshold)
                rows.append({
                    "event_type": event_type,
                    "horizon_minutes": int(horizon),
                    "patient_id": patient_id,
                    "year": year,
                    "split": ",".join(sorted(group["split"].astype(str).unique())),
                    "threshold": threshold,
                    "samples": int(len(group)),
                    "positive_rate": float(group["y_true"].mean()),
                    **metrics,
                })
    return pd.DataFrame(rows).sort_values(["event_type", "horizon_minutes", "recall"]).reset_index(drop=True)


def patient_data_quality_audit(eval_table: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (patient_id, year), group in eval_table.groupby(["patient_id", "year"]):
        timestamp = pd.to_datetime(group["timestamp"]).sort_values()
        gaps = timestamp.diff().dt.total_seconds().div(60).dropna()
        rows.append({
            "patient_id": patient_id,
            "year": year,
            "split": ",".join(sorted(group["split"].astype(str).unique())),
            "rows": int(len(group)),
            "start_timestamp": str(timestamp.min()),
            "end_timestamp": str(timestamp.max()),
            "median_interval_minutes": float(gaps.median()) if not gaps.empty else 0.0,
            "large_gap_count_gt_10m": int((gaps > 10).sum()) if not gaps.empty else 0,
            "hypo_rate_current": float((group["glucose_mg_dl"] < 70).mean()),
            "hyper_rate_current": float((group["glucose_mg_dl"] > 180).mean()),
        })
    return pd.DataFrame(rows).sort_values(["large_gap_count_gt_10m", "rows"], ascending=[False, True]).reset_index(drop=True)


def event_metrics_with_thresholds(
    classifiers: dict[str, dict[int, object]],
    eval_table: pd.DataFrame,
    horizons: list[int],
    feature_columns: list[str],
    thresholds: dict[str, dict[int, float]],
    split: str,
) -> pd.DataFrame:
    features = _resolved_features(eval_table, feature_columns)
    x_eval = eval_table[features].to_numpy(dtype="float32")
    rows: list[dict[str, object]] = []
    for event_type in ("hypo", "hyper"):
        for horizon in horizons:
            y_true = (
                (eval_table[f"target_{horizon}m"] < 70)
                if event_type == "hypo"
                else (eval_table[f"target_{horizon}m"] > 180)
            ).astype(int).to_numpy()
            y_prob = _predict_probability(classifiers[event_type][int(horizon)], x_eval)
            threshold = thresholds.get(event_type, {}).get(int(horizon), 0.5)
            metrics = _event_binary_metrics(y_true, y_prob, threshold)
            rows.append({
                "event_type": event_type,
                "horizon_minutes": int(horizon),
                "split": split,
                "threshold": threshold,
                "samples": int(len(y_true)),
                "positive_rate": float(y_true.mean()),
                **metrics,
            })
    return pd.DataFrame(rows).sort_values(["event_type", "horizon_minutes"]).reset_index(drop=True)


def calibration_strategy_comparison(
    raw_predictions: pd.DataFrame,
    calibrated_predictions: pd.DataFrame,
    split: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for strategy, frame in [
        ("no_calibration", raw_predictions),
        ("predicted_range_mean_residual", calibrated_predictions),
    ]:
        df = frame.copy()
        df["true_range"] = pd.Series(
            pd.Series(df["y_true"]).pipe(lambda values: pd.cut(
                values,
                bins=[float("-inf"), 70, 180, float("inf")],
                labels=["low", "normal", "high"],
                right=False,
            ))
        ).astype(str)
        for horizon, group in df.groupby("horizon_minutes"):
            range_mae = group.groupby("true_range")["abs_error"].mean().to_dict()
            range_count = group.groupby("true_range")["abs_error"].count().to_dict()
            range_error = group.groupby("true_range")["error"].mean().to_dict()
            high_group = group[group["true_range"] == "high"]
            low_group = group[group["true_range"] == "low"]
            rows.append({
                "strategy": strategy,
                "horizon_minutes": int(horizon),
                "split": split,
                "overall_mae": float(group["abs_error"].mean()),
                "low_mae": float(range_mae.get("low", float("nan"))),
                "normal_mae": float(range_mae.get("normal", float("nan"))),
                "high_mae": float(range_mae.get("high", float("nan"))),
                "low_mean_error": float(range_error.get("low", float("nan"))),
                "high_mean_error": float(range_error.get("high", float("nan"))),
                "low_sample_count": int(range_count.get("low", 0)),
                "high_sample_count": int(range_count.get("high", 0)),
                "high_under_prediction_rate": float((high_group["error"] < 0).mean()) if not high_group.empty else float("nan"),
                "low_over_prediction_rate": float((low_group["error"] > 0).mean()) if not low_group.empty else float("nan"),
                "selected": False,
                "selection_split": split,
                "evaluation_split": "test",
                "leakage_safe": True,
            })
    result = pd.DataFrame(rows)
    if not result.empty:
        summary = result.groupby("strategy")["overall_mae"].mean().sort_values()
        selected_strategy = str(summary.index[0])
        result["selected"] = result["strategy"] == selected_strategy
    return result


def write_iob_cob_audit(train_table: pd.DataFrame, report_dir: Path) -> None:
    rows = []
    for column in [
        "time_since_last_meal",
        "time_since_last_bolus",
        "carbs_on_board_proxy",
        "insulin_on_board_proxy",
        "net_glucose_pressure_proxy",
    ]:
        if column in train_table:
            rows.append({
                "feature": column,
                "non_null_count": int(train_table[column].notna().sum()),
                "mean": float(train_table[column].mean()),
                "p95": float(train_table[column].quantile(0.95)),
                "min": float(train_table[column].min()),
                "max": float(train_table[column].max()),
                "past_only_proxy": True,
            })
    audit = pd.DataFrame(rows)
    audit.to_csv(report_dir / "iob_cob_feature_audit.csv", index=False)
    summary = {
        "feature_type": "predictive_proxy_not_medical_iob_cob",
        "no_future_event_columns_used": True,
        "features": audit.to_dict(orient="records"),
        "safety_note": "These features are for forecasting experiments only and are not insulin dosing guidance.",
    }
    (report_dir / "iob_cob_feature_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def feature_correlation_importance(train_table: pd.DataFrame, feature_columns: list[str], horizons: list[int]) -> pd.DataFrame:
    rows = []
    available = _resolved_features(train_table, feature_columns)
    for horizon in horizons:
        target = train_table[f"target_{horizon}m"]
        for feature in available:
            corr = train_table[feature].corr(target)
            rows.append({
                "horizon_minutes": int(horizon),
                "feature": feature,
                "abs_correlation_importance": float(abs(corr)) if pd.notna(corr) else 0.0,
            })
    return pd.DataFrame(rows).sort_values(["horizon_minutes", "abs_correlation_importance"], ascending=[True, False])


def prediction_interval_reports(validation_predictions: pd.DataFrame, test_predictions: pd.DataFrame, report_dir: Path, model_dir: Path) -> None:
    rows = []
    test_rows = []
    interval_config: dict[str, dict[str, float]] = {}
    validation = validation_predictions[validation_predictions["model_type"] == "enriched_calibrated"].copy()
    test = test_predictions[test_predictions["model_type"] == "enriched_calibrated"].copy()
    if validation.empty:
        validation = validation_predictions[validation_predictions["model_type"] == "enriched"].copy()
    if test.empty:
        test = test_predictions[test_predictions["model_type"] == "enriched"].copy()
    for horizon, group in validation.groupby("horizon_minutes"):
        lower = float((-group["error"]).quantile(0.90))
        upper = float(group["error"].quantile(0.90))
        abs_p90 = float(group["abs_error"].quantile(0.90))
        lower = max(lower, abs_p90)
        upper = max(upper, abs_p90)
        interval_config[str(int(horizon))] = {"lower_abs_error": lower, "upper_abs_error": upper, "p90_abs_error": abs_p90}
    for horizon, group in test.groupby("horizon_minutes"):
        config = interval_config[str(int(horizon))]
        lower = group["y_pred"] - config["lower_abs_error"]
        upper = group["y_pred"] + config["upper_abs_error"]
        covered = ((group["y_true"] >= lower) & (group["y_true"] <= upper)).mean()
        width = float((upper - lower).mean())
        level = "low" if width < 30 else "medium" if width < 60 else "high"
        row = {
            "horizon_minutes": int(horizon),
            "split": "test",
            "target_coverage": 0.80,
            "observed_coverage": float(covered),
            "mean_interval_width": width,
            "uncertainty_level": level,
        }
        rows.append(row)
        test_rows.append(row)
    pd.DataFrame(rows).to_csv(report_dir / "prediction_interval_metrics.csv", index=False)
    pd.DataFrame(rows).to_csv(report_dir / "conformal_coverage_report.csv", index=False)
    pd.DataFrame(test_rows).to_csv(report_dir / "uncertainty_by_horizon.csv", index=False)
    (model_dir / "prediction_intervals.json").write_text(
        json.dumps({"method": "validation_residual_p90", "intervals": interval_config}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def patient_specific_reports(predictions: pd.DataFrame, report_dir: Path) -> None:
    enriched = predictions[predictions["model_type"].isin(["enriched", "enriched_calibrated"])].copy()
    rows = []
    for (model_type, patient_id, horizon), group in enriched.groupby(["model_type", "patient_id", "horizon_minutes"]):
        rows.append({
            "model_variant": model_type,
            "patient_id": patient_id,
            "horizon_minutes": int(horizon),
            "mae": float(group["abs_error"].mean()),
            "samples": int(len(group)),
        })
    comparison = pd.DataFrame(rows)
    comparison.to_csv(report_dir / "patient_specific_vs_global.csv", index=False)
    pivot = comparison.pivot_table(index=["patient_id", "horizon_minutes"], columns="model_variant", values="mae", aggfunc="first").reset_index()
    if {"enriched", "enriched_calibrated"}.issubset(pivot.columns):
        pivot["patient_calibration_gain"] = pivot["enriched"] - pivot["enriched_calibrated"]
    pivot.to_csv(report_dir / "horizon_patient_gain.csv", index=False)
    worst = comparison[comparison["horizon_minutes"].isin([60, 90])].sort_values("mae", ascending=False).head(20)
    worst.to_csv(report_dir / "worst_patient_60_90_diagnosis.csv", index=False)
    lines = [
        "# Patient Specific Summary",
        "",
        "Global model과 global range calibration을 환자별로 비교했다.",
        "이 리포트는 개인화 가능성 탐색용이며 의료 진단이나 치료 지침이 아니다.",
        "",
        f"- rows: `{len(comparison)}`",
        f"- worst 60/90 report: `worst_patient_60_90_diagnosis.csv`",
    ]
    (report_dir / "patient_specific_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cgm-csv",
        type=Path,
        default=Path("data/processed/ohiot1dm/cgm_timeseries.csv"),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("data/processed/glucose_models"),
        help="Output directory for glucose forecasting models. This intentionally avoids data/models.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/glucose_forecasting"),
    )
    parser.add_argument(
        "--horizons",
        type=int,
        nargs="+",
        default=list(DEFAULT_HORIZONS_MINUTES),
    )
    parser.add_argument(
        "--use-validation-selection",
        action="store_true",
        help="Split train into train_inner/validation and use validation for model, threshold, and calibration selection.",
    )
    parser.add_argument(
        "--long-horizon-upgrade",
        action="store_true",
        help="Use long-window IOB/COB proxy features and write long-horizon uncertainty reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = pd.read_csv(args.cgm_csv, parse_dates=["timestamp"])
    train_frame = frame[frame["split"] == "train"].copy()
    test_frame = frame[frame["split"] == "test"].copy()
    if train_frame.empty or test_frame.empty:
        raise ValueError("CGM CSV must contain train and test splits")
    args.report_dir.mkdir(parents=True, exist_ok=True)

    selection_split = "test"
    model_train_frame = train_frame
    selection_frame = test_frame
    validation_split_summary: dict[str, object] = {}
    validation_split_audit = pd.DataFrame()
    if args.use_validation_selection:
        model_train_frame, selection_frame, validation_split_audit, validation_split_summary = make_time_based_validation_split(
            train_frame
        )
        split_output_dir = args.cgm_csv.parent
        model_train_frame.to_csv(split_output_dir / "cgm_train_inner_enriched.csv", index=False)
        selection_frame.to_csv(split_output_dir / "cgm_validation_enriched.csv", index=False)
        test_frame.assign(inner_split="test").to_csv(split_output_dir / "cgm_test_enriched.csv", index=False)
        validation_split_audit.to_csv(args.report_dir / "validation_split_audit.csv", index=False)
        (args.report_dir / "validation_split_summary.json").write_text(
            json.dumps(validation_split_summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        selection_split = "validation"

    train_table = build_training_table(model_train_frame, args.horizons)
    test_table = build_training_table(test_frame, args.horizons)
    selection_table = build_training_table(selection_frame, args.horizons)
    if train_table.empty or test_table.empty:
        raise ValueError("Feature table is empty. Check CGM interval and target horizon coverage.")
    if args.use_validation_selection and selection_table.empty:
        raise ValueError("Validation feature table is empty. Check time-based validation split.")

    has_enriched = all(column in frame.columns for column in ["carbs_last_60m", "bolus_last_60m", "basal_current"])
    history_train_table = build_training_table(model_train_frame, args.horizons, HISTORY_FEATURE_COLUMNS)
    history_selection_table = build_training_table(selection_frame, args.horizons, HISTORY_FEATURE_COLUMNS)
    history_test_table = build_training_table(test_frame, args.horizons, HISTORY_FEATURE_COLUMNS)
    history_models = train_forecast_models(history_train_table, args.horizons, HISTORY_FEATURE_COLUMNS)
    history_predictions = predict_forecast_models(
        history_models,
        history_test_table,
        HISTORY_FEATURE_COLUMNS,
        model_type="history",
    )
    persistence = persistence_predictions(history_test_table, args.horizons)
    all_predictions = [persistence, history_predictions]

    saved_model_type = "history"
    saved_feature_columns = HISTORY_FEATURE_COLUMNS
    if has_enriched:
        enriched_feature_columns = LONG_HORIZON_ENRICHED_FEATURE_COLUMNS if args.long_horizon_upgrade else ENRICHED_FEATURE_COLUMNS
        enriched_train_table = build_training_table(model_train_frame, args.horizons, enriched_feature_columns)
        enriched_selection_table = build_training_table(selection_frame, args.horizons, enriched_feature_columns)
        enriched_test_table = build_training_table(test_frame, args.horizons, enriched_feature_columns)
        enriched_models = train_forecast_models(enriched_train_table, args.horizons, enriched_feature_columns)
        save_forecast_models(enriched_models, args.model_dir, enriched_feature_columns, model_type="enriched_long_horizon" if args.long_horizon_upgrade else "enriched")
        enriched_train_predictions = predict_forecast_models(
            enriched_models,
            enriched_train_table,
            enriched_feature_columns,
            model_type="enriched",
        )
        enriched_selection_predictions = predict_forecast_models(
            enriched_models,
            enriched_selection_table,
            enriched_feature_columns,
            model_type="enriched",
        )
        enriched_predictions = predict_forecast_models(
            enriched_models,
            enriched_test_table,
            enriched_feature_columns,
            model_type="enriched",
        )
        calibration_table = fit_range_calibrators(enriched_train_predictions, model_type="enriched")
        save_range_calibrators(calibration_table, args.model_dir)
        validation_calibrated_predictions = apply_range_calibration(enriched_selection_predictions, calibration_table)
        calibrated_predictions = apply_range_calibration(enriched_predictions, calibration_table)
        validation_predictions = pd.concat([enriched_selection_predictions, validation_calibrated_predictions], ignore_index=True)
        event_classifiers = train_event_classifiers(enriched_train_table, args.horizons, ENRICHED_FEATURE_COLUMNS)
        event_classifiers, hypo_comparison, hypo_selected = train_weighted_hypo_candidates(
            event_classifiers,
            enriched_train_table,
            enriched_selection_table,
            list(args.horizons),
            ENRICHED_FEATURE_COLUMNS,
            selection_split=selection_split,
        )
        save_event_classifiers(event_classifiers, args.model_dir)
        event_metrics = evaluate_event_classifiers(event_classifiers, enriched_test_table, ENRICHED_FEATURE_COLUMNS)
        hypo_sweep, hypo_threshold_selection = sweep_hypo_thresholds(
            event_classifiers,
            enriched_selection_table,
            list(args.horizons),
            ENRICHED_FEATURE_COLUMNS,
            selection_split=selection_split,
        )
        event_thresholds = {
            "selection_split": selection_split,
            "evaluation_split": "test",
            "created_by": "validation_based_threshold_selection" if args.use_validation_selection else "test_based_threshold_selection_legacy",
            "threshold_selection_method": "threshold sweep maximizing F1 under recall target",
            "hypo": {
                str(horizon): {
                    "threshold": hypo_threshold_selection["horizons"][str(int(horizon))]["threshold"],
                    "target_recall": hypo_threshold_selection["horizons"][str(int(horizon))]["target_recall"],
                    "target_met": hypo_threshold_selection["horizons"][str(int(horizon))]["target_met"],
                    "validation_recall": hypo_threshold_selection["horizons"][str(int(horizon))]["recall"],
                    "validation_precision": hypo_threshold_selection["horizons"][str(int(horizon))]["precision"],
                    "validation_f1": hypo_threshold_selection["horizons"][str(int(horizon))]["f1"],
                }
                for horizon in args.horizons
            },
            "hyper": {
                str(int(horizon)): {
                    "threshold": 0.5,
                    "selection_split": selection_split,
                    "evaluation_split": "test",
                }
                for horizon in args.horizons
            },
            "thresholds": {
                "hypo": {
                    str(horizon): hypo_threshold_selection["horizons"][str(int(horizon))]["threshold"]
                    for horizon in args.horizons
                },
                "hyper": {str(int(horizon)): 0.5 for horizon in args.horizons},
            },
            "hypo_selection": hypo_threshold_selection,
            "hyper_selection_note": "hyper classifier keeps the default 0.50 threshold in this stage.",
        }
        (args.model_dir / "event_thresholds.json").write_text(
            json.dumps(event_thresholds, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        selected_thresholds = {
            "hypo": {int(h): float(v["threshold"]) for h, v in event_thresholds["hypo"].items()},
            "hyper": {int(h): float(v["threshold"]) for h, v in event_thresholds["hyper"].items()},
        }
        validation_calibration_comparison = calibration_strategy_comparison(
            enriched_selection_predictions,
            validation_calibrated_predictions,
            split=selection_split,
        )
        selected_calibration_strategy = (
            validation_calibration_comparison[validation_calibration_comparison["selected"]]["strategy"].iloc[0]
            if not validation_calibration_comparison.empty
            else "no_calibration"
        )
        test_calibration_final_evaluation = calibration_strategy_comparison(
            enriched_predictions,
            calibrated_predictions,
            split="test",
        )
        test_calibration_final_evaluation["selected"] = (
            test_calibration_final_evaluation["strategy"] == selected_calibration_strategy
        )
        test_final_event_metrics = event_metrics_with_thresholds(
            event_classifiers,
            enriched_test_table,
            list(args.horizons),
            ENRICHED_FEATURE_COLUMNS,
            selected_thresholds,
            split="test",
        )
        patient_events = patient_event_metrics(
            event_classifiers,
            enriched_test_table,
            list(args.horizons),
            ENRICHED_FEATURE_COLUMNS,
            selected_thresholds,
        )
        quality_audit = patient_data_quality_audit(enriched_test_table)
        all_predictions.append(enriched_predictions)
        all_predictions.append(calibrated_predictions)
        saved_model_type = "enriched"
        saved_feature_columns = enriched_feature_columns
        train_table = enriched_train_table
        test_table = enriched_test_table
    else:
        save_forecast_models(history_models, args.model_dir, HISTORY_FEATURE_COLUMNS, model_type="history")
        calibration_table = pd.DataFrame()
        event_metrics = pd.DataFrame()
        hypo_comparison = pd.DataFrame()
        hypo_selected = []
        hypo_sweep = pd.DataFrame()
        hypo_threshold_selection = {}
        event_thresholds = {"thresholds": {"hypo": {}, "hyper": {}}}
        patient_events = pd.DataFrame()
        quality_audit = pd.DataFrame()
        validation_calibration_comparison = pd.DataFrame()
        test_calibration_final_evaluation = pd.DataFrame()
        selected_calibration_strategy = "no_calibration"
        test_final_event_metrics = pd.DataFrame()
        validation_predictions = pd.DataFrame()
        train_table = history_train_table
        test_table = history_test_table

    predictions = pd.concat(all_predictions, ignore_index=True)
    metrics = metrics_from_predictions(predictions)

    baseline = metrics[metrics["model_type"] == "persistence"][["horizon_minutes", "mae"]].rename(
        columns={"mae": "persistence_mae"}
    )
    history = metrics[metrics["model_type"] == "history"][["horizon_minutes", "mae"]].rename(
        columns={"mae": "history_mae"}
    )
    metrics = metrics.merge(baseline, on="horizon_minutes", how="left").merge(history, on="horizon_minutes", how="left")
    metrics["mae_improvement_vs_persistence_pct"] = (
        (metrics["persistence_mae"] - metrics["mae"]) / metrics["persistence_mae"] * 100
    )
    metrics["mae_improvement_vs_history_pct"] = (
        (metrics["history_mae"] - metrics["mae"]) / metrics["history_mae"] * 100
    )

    args.report_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.report_dir / "metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    metrics.to_csv(args.report_dir / "metrics_baseline_vs_enriched.csv", index=False)
    metrics.to_csv(args.report_dir / "test_final_metrics.csv", index=False)
    if not calibration_table.empty:
        calibration_table.to_csv(args.report_dir / "range_calibration_table.csv", index=False)
        calibration_table.to_csv(args.report_dir / "range_specific_calibration_table.csv", index=False)
    if not event_metrics.empty:
        event_metrics.to_csv(args.report_dir / "event_classifier_metrics.csv", index=False)
    if not test_final_event_metrics.empty:
        test_final_event_metrics.to_csv(args.report_dir / "test_final_event_classifier_metrics.csv", index=False)
    if not hypo_comparison.empty:
        hypo_comparison.to_csv(args.report_dir / "hypo_classifier_model_comparison.csv", index=False)
        hypo_comparison.to_csv(args.report_dir / "validation_hypo_classifier_model_comparison.csv", index=False)
        (args.report_dir / "hypo_classifier_selected_models.json").write_text(
            json.dumps(
                {
                    "selection_split": selection_split,
                    "evaluation_split": "test",
                    "selection_method": "recall target, then PR-AUC, F1, false negatives",
                    "selected_models": hypo_selected,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        (args.report_dir / "validation_hypo_classifier_selected_models.json").write_text(
            json.dumps(
                {
                    "selection_split": selection_split,
                    "evaluation_split": "test",
                    "selection_method": "recall target, then PR-AUC, F1, false negatives",
                    "selected_models": hypo_selected,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    if not hypo_sweep.empty:
        hypo_sweep.to_csv(args.report_dir / "hypo_threshold_sweep.csv", index=False)
        hypo_sweep.to_csv(args.report_dir / "validation_hypo_threshold_sweep.csv", index=False)
        (args.report_dir / "hypo_threshold_selection.json").write_text(
            json.dumps(hypo_threshold_selection, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (args.report_dir / "validation_hypo_threshold_selection.json").write_text(
            json.dumps(hypo_threshold_selection, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    metrics[
        metrics["model_type"].isin(["enriched", "enriched_calibrated"])
    ].to_csv(args.report_dir / "metrics_calibrated_vs_raw.csv", index=False)
    predictions[predictions["model_type"] == saved_model_type].head(1000).to_csv(
        args.report_dir / "predictions_enriched_sample.csv",
        index=False,
    )
    per_patient, per_patient_horizon, worst_patients, best_patients = per_patient_metrics(predictions)
    per_patient.to_csv(args.report_dir / "per_patient_metrics.csv", index=False)
    per_patient_horizon.to_csv(args.report_dir / "per_patient_horizon_metrics.csv", index=False)
    per_patient_horizon.to_csv(args.report_dir / "test_final_per_patient_metrics.csv", index=False)
    worst_patients.to_csv(args.report_dir / "worst_patients.csv", index=False)
    best_patients.to_csv(args.report_dir / "best_patients.csv", index=False)
    if not patient_events.empty:
        patient_events.to_csv(args.report_dir / "per_patient_event_metrics.csv", index=False)
    if not quality_audit.empty:
        quality_audit.to_csv(args.report_dir / "patient_data_quality_audit.csv", index=False)
    range_metrics, hypo_cases, hyper_cases = glucose_range_metrics(predictions)
    range_metrics.to_csv(args.report_dir / "per_glucose_range_metrics.csv", index=False)
    range_metrics.to_csv(args.report_dir / "test_final_range_metrics.csv", index=False)
    if args.long_horizon_upgrade and has_enriched:
        write_iob_cob_audit(train_table, args.report_dir)
        feature_correlation_importance(
            train_table,
            list(LONG_HORIZON_ENRICHED_FEATURE_COLUMNS),
            list(args.horizons),
        ).to_csv(args.report_dir / "long_window_feature_importance.csv", index=False)
        metrics[metrics["model_type"].isin(["enriched", "enriched_calibrated"])].to_csv(
            args.report_dir / "long_window_model_metrics.csv",
            index=False,
        )
        comparison_rows = []
        for horizon in args.horizons:
            comparison_rows.append({
                "horizon_minutes": int(horizon),
                "feature_set": "long_horizon_enriched",
                "feature_count": len(LONG_HORIZON_ENRICHED_FEATURE_COLUMNS),
                "selection_split": selection_split,
                "evaluation_split": "test",
            })
        pd.DataFrame(comparison_rows).to_csv(args.report_dir / "horizon_feature_set_comparison.csv", index=False)
        prediction_interval_reports(validation_predictions, predictions, args.report_dir, args.model_dir)
        patient_specific_reports(predictions, args.report_dir)
        range_metrics[range_metrics["model_type"].isin(["enriched", "enriched_calibrated"])].to_csv(
            args.report_dir / "range_weighted_model_comparison.csv",
            index=False,
        )
        range_metrics[range_metrics["range_name"].isin(["low", "high"])].to_csv(
            args.report_dir / "low_high_tradeoff_report.csv",
            index=False,
        )
    hypo_cases.to_csv(args.report_dir / "hypoglycemia_case_errors.csv", index=False)
    hyper_cases.to_csv(args.report_dir / "hyperglycemia_case_errors.csv", index=False)
    calibration_gain = (
        per_patient_horizon.pivot_table(
            index=["patient_id", "year", "split", "horizon_minutes"],
            columns="model_type",
            values="mae",
            aggfunc="first",
        )
        .reset_index()
    )
    if {"enriched", "enriched_calibrated"}.issubset(calibration_gain.columns):
        calibration_gain["mae_gain_raw_minus_calibrated"] = (
            calibration_gain["enriched"] - calibration_gain["enriched_calibrated"]
        )
        calibration_gain.to_csv(args.report_dir / "per_patient_calibration_gain.csv", index=False)
        worst_diagnostics = calibration_gain.sort_values("mae_gain_raw_minus_calibrated").head(20)
        worst_diagnostics.to_csv(args.report_dir / "worst_patient_diagnostic_report.csv", index=False)
    else:
        pd.DataFrame().to_csv(args.report_dir / "per_patient_calibration_gain.csv", index=False)
        pd.DataFrame().to_csv(args.report_dir / "worst_patient_diagnostic_report.csv", index=False)
    calibration_strategy = {
        "selection_split": selection_split,
        "evaluation_split": "test",
        "selected_strategy": selected_calibration_strategy,
        "reason": "selected on validation using leakage-safe raw prediction range residual correction; test is final evaluation only.",
        "outputs": {
            "validation_calibration_strategy_comparison": "validation_calibration_strategy_comparison.csv",
            "test_calibration_final_evaluation": "test_calibration_final_evaluation.csv",
            "range_specific_calibration_table": "range_specific_calibration_table.csv",
            "per_patient_calibration_gain": "per_patient_calibration_gain.csv",
        },
    }
    strategy_rows = metrics[metrics["model_type"].isin(["enriched", "enriched_calibrated"])][
        ["model_type", "horizon_minutes", "samples", "mae", "rmse", "r2"]
    ].copy()
    strategy_rows["calibration_strategy"] = strategy_rows["model_type"].map(
        {"enriched": "raw", "enriched_calibrated": "global_predicted_range_mean_error"}
    )
    strategy_rows.to_csv(args.report_dir / "range_specific_calibration_comparison.csv", index=False)
    if not validation_calibration_comparison.empty:
        validation_calibration_comparison.to_csv(args.report_dir / "validation_calibration_strategy_comparison.csv", index=False)
    if not test_calibration_final_evaluation.empty:
        test_calibration_final_evaluation.to_csv(args.report_dir / "test_calibration_final_evaluation.csv", index=False)
    (args.report_dir / "calibration_strategy_selection.json").write_text(
        json.dumps(calibration_strategy, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.report_dir / "validation_calibration_strategy_selection.json").write_text(
        json.dumps(calibration_strategy, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "cgm_csv": str(args.cgm_csv),
        "model_dir": str(args.model_dir),
        "report_dir": str(args.report_dir),
        "horizons_minutes": [int(horizon) for horizon in args.horizons],
        "train_rows_raw": int(len(train_frame)),
        "test_rows_raw": int(len(test_frame)),
        "train_rows_features": int(len(train_table)),
        "test_rows_features": int(len(test_table)),
        "saved_model_type": saved_model_type,
        "saved_feature_columns": list(saved_feature_columns),
        "has_enriched_features": bool(has_enriched),
        "use_validation_selection": bool(args.use_validation_selection),
        "selection_split": selection_split,
        "evaluation_split": "test",
        "validation_split_summary": validation_split_summary,
        "range_calibration": calibration_table.to_dict(orient="records") if not calibration_table.empty else [],
        "event_classifier_metrics": event_metrics.to_dict(orient="records") if not event_metrics.empty else [],
        "hypo_threshold_selection": hypo_threshold_selection,
        "event_thresholds": event_thresholds,
        "metrics": metrics.to_dict(orient="records"),
        "reference_notice": GLUCOSE_REFERENCE_NOTICE,
    }
    (args.report_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.report_dir / "summary_baseline_vs_enriched.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metric_lines = [
        "| Model | Horizon | Samples | MAE | RMSE | R2 | MAE vs persistence | MAE vs history |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics.to_dict(orient="records"):
        metric_lines.append(
            f"| {row['model_type']} | {int(row['horizon_minutes'])}m | {int(row['samples'])} | "
            f"{row['mae']:.3f} | {row['rmse']:.3f} | {row['r2']:.4f} | "
            f"{row['mae_improvement_vs_persistence_pct']:.2f}% | {row['mae_improvement_vs_history_pct']:.2f}% |"
        )

    report = [
        "# CGM Forecasting Evaluation",
        "",
        f"- CGM CSV: `{args.cgm_csv}`",
        f"- model_dir: `{args.model_dir}`",
        f"- train rows raw: `{len(train_frame)}`",
        f"- test rows raw: `{len(test_frame)}`",
        f"- train rows used: `{len(train_table)}`",
        f"- test rows used: `{len(test_table)}`",
        f"- saved model type: `{saved_model_type}`",
        f"- enriched features detected: `{has_enriched}`",
        f"- reference notice: {GLUCOSE_REFERENCE_NOTICE}",
        "",
        "## Metrics",
        "",
        *metric_lines,
        "",
        "## Interpretation",
        "",
        "These models forecast CGM values 30, 60, and 90 minutes ahead from recent CGM history and optional event features.",
        "They are for reference and product experimentation only, not medical diagnosis or treatment guidance.",
        "",
        "## Additional Reports",
        "",
        "- `metrics_baseline_vs_enriched.csv`",
        "- `metrics_calibrated_vs_raw.csv`",
        "- `range_calibration_table.csv`",
        "- `range_specific_calibration_comparison.csv`",
        "- `range_specific_calibration_table.csv`",
        "- `calibration_strategy_selection.json`",
        "- `event_classifier_metrics.csv`",
        "- `hypo_classifier_model_comparison.csv`",
        "- `hypo_classifier_selected_models.json`",
        "- `hypo_threshold_sweep.csv`",
        "- `hypo_threshold_selection.json`",
        "- `per_patient_metrics.csv`",
        "- `per_patient_horizon_metrics.csv`",
        "- `per_patient_event_metrics.csv`",
        "- `per_patient_calibration_gain.csv`",
        "- `patient_data_quality_audit.csv`",
        "- `worst_patient_diagnostic_report.csv`",
        "- `worst_patients.csv`",
        "- `best_patients.csv`",
        "- `per_glucose_range_metrics.csv`",
        "- `hypoglycemia_case_errors.csv`",
        "- `hyperglycemia_case_errors.csv`",
    ]
    (args.report_dir / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    final_event_lines = [
        "| Event | Horizon | Split | Threshold | Precision | Recall | F1 | PR-AUC | ROC-AUC | FN | FP |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    if not test_final_event_metrics.empty:
        for row in test_final_event_metrics.to_dict(orient="records"):
            final_event_lines.append(
                f"| {row['event_type']} | {int(row['horizon_minutes'])}m | {row['split']} | "
                f"{row['threshold']:.2f} | {row['precision']:.3f} | {row['recall']:.3f} | "
                f"{row['f1']:.3f} | {row['pr_auc']:.3f} | {row['roc_auc']:.3f} | "
                f"{int(row['false_negative_count'])} | {int(row['false_positive_count'])} |"
            )
    final_report = [
        "# CGM Final Test Evaluation",
        "",
        f"- model/threshold selection split: `{selection_split}`",
        "- evaluation split: `test`",
        f"- test used for selection: `{not args.use_validation_selection}`",
        "- statement: validation에서 선택한 model family, threshold, calibration strategy를 고정한 뒤 test에서 최종 평가했다.",
        f"- selected calibration strategy: `{selected_calibration_strategy}`",
        f"- reference notice: {GLUCOSE_REFERENCE_NOTICE}",
        "",
        "## Forecast Metrics",
        "",
        *metric_lines,
        "",
        "## Event Metrics",
        "",
        *final_event_lines,
        "",
        "## Remaining Limitations",
        "",
        "- 90분 저혈당 precision은 낮을 수 있어 운영 UI에서는 가능성/주의 신호로만 표현해야 한다.",
        "- RandomForest probability는 calibrated clinical probability가 아니라 모델 점수로 해석해야 한다.",
        "- 본 결과는 참고용이며 의료 진단이나 치료 지침이 아니다.",
    ]
    (args.report_dir / "test_final_evidence_summary.md").write_text("\n".join(final_report) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
