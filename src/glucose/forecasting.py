"""CGM feature engineering and forecasting model helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_fscore_support,
    r2_score,
    roc_auc_score,
)

from src.glucose.constants import GLUCOSE_REFERENCE_NOTICE, OHIOT1DM_TRAINING_PATIENT_IDS


DEFAULT_HORIZONS_MINUTES = (30, 60, 90)
HISTORY_FEATURE_COLUMNS = [
    "glucose_mg_dl",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "lag_12",
    "diff_1",
    "diff_3",
    "diff_6",
    "rolling_mean_3",
    "rolling_mean_6",
    "rolling_mean_12",
    "rolling_std_6",
    "rolling_std_12",
    "hour_sin",
    "hour_cos",
]
ENRICHED_ONLY_FEATURE_COLUMNS = [
    "carbs_current",
    "carbs_last_30m",
    "carbs_last_60m",
    "carbs_last_120m",
    "carbs_last_180m",
    "bolus_current",
    "bolus_last_30m",
    "bolus_last_60m",
    "bolus_last_120m",
    "bolus_last_180m",
    "basal_current",
    "basal_mean_60m",
    "basal_mean_120m",
    "exercise_active",
    "exercise_last_60m",
    "exercise_last_120m",
    "sleep_indicator",
    "hypo_event_current",
    "gsr_current",
    "skin_temperature_current",
    "acceleration_current",
    "day_of_week",
    "patient_id_numeric",
]
LONG_HORIZON_FEATURE_COLUMNS = [
    "time_since_last_meal",
    "time_since_last_bolus",
    "meal_bolus_gap_minutes",
    "carbs_decay_30m",
    "carbs_decay_60m",
    "carbs_decay_120m",
    "carbs_decay_180m",
    "carbs_on_board_proxy",
    "insulin_decay_60m",
    "insulin_decay_120m",
    "insulin_decay_180m",
    "insulin_decay_240m",
    "insulin_on_board_proxy",
    "carb_insulin_ratio_proxy",
    "net_glucose_pressure_proxy",
    "glucose_slope_60m",
    "glucose_slope_120m",
    "glucose_volatility_120m",
    "glucose_volatility_180m",
    "glucose_mean_120m",
    "glucose_mean_180m",
    "recent_low_event_count_180m",
    "recent_high_event_count_180m",
    "time_since_last_low",
    "time_since_last_high",
    "basal_mean_180m",
    "exercise_last_180m",
]
ENRICHED_FEATURE_COLUMNS = HISTORY_FEATURE_COLUMNS + ENRICHED_ONLY_FEATURE_COLUMNS
LONG_HORIZON_ENRICHED_FEATURE_COLUMNS = ENRICHED_FEATURE_COLUMNS + LONG_HORIZON_FEATURE_COLUMNS
FEATURE_COLUMNS = HISTORY_FEATURE_COLUMNS
_MODEL_CACHE: dict[str, dict[int, RegressorMixin]] = {}
_MODEL_CACHE_LOAD_COUNT: dict[str, int] = {}
_METADATA_CACHE: dict[str, dict[str, object]] = {}
_CALIBRATION_CACHE: dict[str, pd.DataFrame] = {}
_EVENT_CLASSIFIER_CACHE: dict[str, dict[str, dict[int, HistGradientBoostingClassifier]]] = {}
_EVENT_THRESHOLD_CACHE: dict[str, dict[str, dict[int, float]]] = {}
_INTERVAL_CACHE: dict[str, dict[int, dict[str, float]]] = {}


@dataclass(frozen=True)
class ForecastResult:
    predictions: dict[int, float]
    calibrated_predictions: dict[int, float] | None = None
    event_probabilities: dict[int, dict[str, float]] | None = None
    risk_flags: dict[int, dict[str, bool]] | None = None
    prediction_intervals: dict[int, list[float]] | None = None
    uncertainty_level: dict[int, str] | None = None
    uncertainty_message: dict[int, str] | None = None
    reference_notice: str = GLUCOSE_REFERENCE_NOTICE


@dataclass(frozen=True)
class EnrichedForecastInputs:
    carbs_current: float = 0.0
    carbs_last_30m: float = 0.0
    carbs_last_60m: float = 0.0
    carbs_last_120m: float = 0.0
    carbs_last_180m: float = 0.0
    bolus_current: float = 0.0
    bolus_last_30m: float = 0.0
    bolus_last_60m: float = 0.0
    bolus_last_120m: float = 0.0
    bolus_last_180m: float = 0.0
    basal_current: float = 0.0
    basal_mean_60m: float = 0.0
    basal_mean_120m: float = 0.0
    exercise_active: float = 0.0
    exercise_last_60m: float = 0.0
    exercise_last_120m: float = 0.0
    sleep_indicator: float = 0.0
    hypo_event_current: float = 0.0
    gsr_current: float = 0.0
    skin_temperature_current: float = 0.0
    acceleration_current: float = 0.0
    patient_id_numeric: float = 0.0


def add_cgm_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add lag, trend, rolling, and time-of-day features per series."""
    required = {"timestamp", "glucose_mg_dl", "patient_id", "source_file"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"CGM frame missing columns: {sorted(missing)}")

    df = frame.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["source_file", "timestamp"]).reset_index(drop=True)
    group = df.groupby("source_file", sort=False)["glucose_mg_dl"]

    for lag in (1, 2, 3, 6, 12):
        df[f"lag_{lag}"] = group.shift(lag)
    df["diff_1"] = df["glucose_mg_dl"] - df["lag_1"]
    df["diff_3"] = df["glucose_mg_dl"] - df["lag_3"]
    df["diff_6"] = df["glucose_mg_dl"] - df["lag_6"]
    for window in (3, 6, 12):
        df[f"rolling_mean_{window}"] = group.transform(
            lambda series: series.rolling(window=window, min_periods=window).mean()
        )
    for window in (6, 12):
        df[f"rolling_std_{window}"] = group.transform(
            lambda series: series.rolling(window=window, min_periods=window).std()
        )

    hour = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60.0
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    df["day_of_week"] = df["timestamp"].dt.dayofweek.astype(float)
    df["patient_id_numeric"] = pd.to_numeric(df["patient_id"], errors="coerce").fillna(0.0)
    return df


def _minutes_since_recent_signal(values: pd.Series, window_steps: int) -> pd.Series:
    elapsed: list[float] = []
    last_seen: int | None = None
    for index, value in enumerate(values.fillna(0.0).to_numpy()):
        if value > 0:
            last_seen = index
            elapsed.append(0.0)
        elif last_seen is None:
            elapsed.append(float(window_steps * 5 + 5))
        else:
            elapsed.append(float(min((index - last_seen) * 5, window_steps * 5 + 5)))
    return pd.Series(elapsed, index=values.index)


def add_long_horizon_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add past-only long-horizon proxy features for research forecasting.

    IOB/COB fields are predictive proxy features derived from observed past
    event aggregates. They are not medical IOB/COB calculations and must not be
    used for insulin dosing or treatment decisions.
    """
    df = frame.copy()
    group = df.groupby("source_file", sort=False)
    glucose_group = group["glucose_mg_dl"]
    for lag in (12, 24):
        lagged = glucose_group.shift(lag)
        minutes = lag * 5
        df[f"glucose_slope_{minutes}m"] = (df["glucose_mg_dl"] - lagged) / float(minutes)
    for window, minutes in ((24, 120), (36, 180)):
        df[f"glucose_mean_{minutes}m"] = glucose_group.transform(
            lambda series: series.rolling(window=window, min_periods=1).mean()
        )
        df[f"glucose_volatility_{minutes}m"] = glucose_group.transform(
            lambda series: series.rolling(window=window, min_periods=2).std()
        ).fillna(0.0)
    low_flag = (df["glucose_mg_dl"] < 70).astype(float)
    high_flag = (df["glucose_mg_dl"] > 180).astype(float)
    df["recent_low_event_count_180m"] = low_flag.groupby(df["source_file"], sort=False).transform(
        lambda series: series.rolling(window=36, min_periods=1).sum()
    )
    df["recent_high_event_count_180m"] = high_flag.groupby(df["source_file"], sort=False).transform(
        lambda series: series.rolling(window=36, min_periods=1).sum()
    )
    df["time_since_last_low"] = low_flag.groupby(df["source_file"], sort=False).transform(
        lambda series: _minutes_since_recent_signal(series, 36)
    )
    df["time_since_last_high"] = high_flag.groupby(df["source_file"], sort=False).transform(
        lambda series: _minutes_since_recent_signal(series, 36)
    )

    for column in [
        "carbs_current",
        "carbs_last_30m",
        "carbs_last_60m",
        "carbs_last_120m",
        "carbs_last_180m",
        "bolus_current",
        "bolus_last_30m",
        "bolus_last_60m",
        "bolus_last_120m",
        "bolus_last_180m",
        "basal_mean_120m",
        "exercise_last_120m",
    ]:
        if column not in df:
            df[column] = 0.0
    df["time_since_last_meal"] = np.select(
        [
            df["carbs_current"] > 0,
            df["carbs_last_30m"] > 0,
            df["carbs_last_60m"] > 0,
            df["carbs_last_120m"] > 0,
            df["carbs_last_180m"] > 0,
        ],
        [0.0, 30.0, 60.0, 120.0, 180.0],
        default=240.0,
    )
    df["time_since_last_bolus"] = np.select(
        [
            df["bolus_current"] > 0,
            df["bolus_last_30m"] > 0,
            df["bolus_last_60m"] > 0,
            df["bolus_last_120m"] > 0,
            df["bolus_last_180m"] > 0,
        ],
        [0.0, 30.0, 60.0, 120.0, 180.0],
        default=240.0,
    )
    df["meal_bolus_gap_minutes"] = df["time_since_last_meal"] - df["time_since_last_bolus"]
    df["carbs_decay_30m"] = df["carbs_last_30m"] * 0.85
    df["carbs_decay_60m"] = df["carbs_last_60m"] * 0.65
    df["carbs_decay_120m"] = df["carbs_last_120m"] * 0.35
    df["carbs_decay_180m"] = df["carbs_last_180m"] * 0.18
    df["carbs_on_board_proxy"] = (
        df["carbs_decay_30m"] + df["carbs_decay_60m"] + df["carbs_decay_120m"] + df["carbs_decay_180m"]
    )
    df["insulin_decay_60m"] = df["bolus_last_60m"] * 0.80
    df["insulin_decay_120m"] = df["bolus_last_120m"] * 0.55
    df["insulin_decay_180m"] = df["bolus_last_180m"] * 0.30
    df["insulin_decay_240m"] = df["bolus_last_180m"] * 0.15
    df["insulin_on_board_proxy"] = (
        df["insulin_decay_60m"] + df["insulin_decay_120m"] + df["insulin_decay_180m"] + df["insulin_decay_240m"]
    )
    df["carb_insulin_ratio_proxy"] = df["carbs_on_board_proxy"] / (df["insulin_on_board_proxy"] + 1.0)
    df["net_glucose_pressure_proxy"] = df["carbs_on_board_proxy"] - df["insulin_on_board_proxy"] * 12.0
    df["basal_mean_180m"] = df["basal_mean_120m"]
    df["exercise_last_180m"] = df["exercise_last_120m"]
    return df


def add_targets(feature_frame: pd.DataFrame, horizons_minutes: Iterable[int] = DEFAULT_HORIZONS_MINUTES) -> pd.DataFrame:
    """Add future glucose targets, keeping only near-exact 5-minute CGM horizons."""
    df = feature_frame.copy()
    grouped = df.groupby("source_file", sort=False)
    for horizon in horizons_minutes:
        steps = int(horizon / 5)
        future_glucose = grouped["glucose_mg_dl"].shift(-steps)
        future_time = grouped["timestamp"].shift(-steps)
        delta_minutes = (future_time - df["timestamp"]).dt.total_seconds() / 60.0
        target = future_glucose.where((delta_minutes - horizon).abs() <= 2.5)
        df[f"target_{horizon}m"] = target
    return df


def _available_feature_columns(frame: pd.DataFrame, requested: Iterable[str]) -> list[str]:
    return [column for column in requested if column in frame.columns]


def build_training_table(
    frame: pd.DataFrame,
    horizons_minutes: Iterable[int] = DEFAULT_HORIZONS_MINUTES,
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
) -> pd.DataFrame:
    featured = add_cgm_features(frame)
    featured = add_long_horizon_features(featured)
    targeted = add_targets(featured, horizons_minutes)
    target_columns = [f"target_{horizon}m" for horizon in horizons_minutes]
    resolved_features = _available_feature_columns(targeted, feature_columns)
    return targeted.dropna(subset=resolved_features + target_columns).reset_index(drop=True)


def train_forecast_models(
    train_table: pd.DataFrame,
    horizons_minutes: Iterable[int] = DEFAULT_HORIZONS_MINUTES,
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
) -> dict[int, HistGradientBoostingRegressor]:
    """Train one fast tabular regressor per horizon."""
    models: dict[int, HistGradientBoostingRegressor] = {}
    resolved_features = _available_feature_columns(train_table, feature_columns)
    x_train = train_table[resolved_features].to_numpy(dtype=np.float32)
    for horizon in horizons_minutes:
        y_train = train_table[f"target_{horizon}m"].to_numpy(dtype=np.float32)
        model = HistGradientBoostingRegressor(
            max_iter=180,
            learning_rate=0.06,
            max_leaf_nodes=31,
            l2_regularization=0.02,
            random_state=20260520 + int(horizon),
        )
        model.fit(x_train, y_train)
        models[int(horizon)] = model
    return models


def evaluate_forecast_models(
    models: dict[int, RegressorMixin],
    eval_table: pd.DataFrame,
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
    model_type: str = "history",
) -> pd.DataFrame:
    resolved_features = _available_feature_columns(eval_table, feature_columns)
    x_eval = eval_table[resolved_features].to_numpy(dtype=np.float32)
    rows: list[dict[str, float]] = []
    for horizon, model in sorted(models.items()):
        y_true = eval_table[f"target_{horizon}m"].to_numpy(dtype=np.float32)
        y_pred = model.predict(x_eval)
        rmse = mean_squared_error(y_true, y_pred) ** 0.5
        rows.append({
            "model_type": model_type,
            "horizon_minutes": int(horizon),
            "samples": int(len(y_true)),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(rmse),
            "r2": float(r2_score(y_true, y_pred)),
        })
    return pd.DataFrame(rows)


def predict_forecast_models(
    models: dict[int, RegressorMixin],
    eval_table: pd.DataFrame,
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
    model_type: str = "history",
) -> pd.DataFrame:
    resolved_features = _available_feature_columns(eval_table, feature_columns)
    x_eval = eval_table[resolved_features].to_numpy(dtype=np.float32)
    rows: list[pd.DataFrame] = []
    id_columns = ["patient_id", "year", "split", "timestamp", "source_file", "glucose_mg_dl"]
    for horizon, model in sorted(models.items()):
        pred = model.predict(x_eval)
        target = eval_table[f"target_{horizon}m"].to_numpy(dtype=np.float32)
        frame = eval_table[id_columns].copy()
        frame["model_type"] = model_type
        frame["horizon_minutes"] = int(horizon)
        frame["y_true"] = target
        frame["y_pred"] = pred
        frame["error"] = frame["y_pred"] - frame["y_true"]
        frame["abs_error"] = frame["error"].abs()
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def persistence_predictions(
    eval_table: pd.DataFrame,
    horizons_minutes: Iterable[int] = DEFAULT_HORIZONS_MINUTES,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    id_columns = ["patient_id", "year", "split", "timestamp", "source_file", "glucose_mg_dl"]
    for horizon in horizons_minutes:
        frame = eval_table[id_columns].copy()
        frame["model_type"] = "persistence"
        frame["horizon_minutes"] = int(horizon)
        frame["y_true"] = eval_table[f"target_{horizon}m"].to_numpy(dtype=np.float32)
        frame["y_pred"] = eval_table["glucose_mg_dl"].to_numpy(dtype=np.float32)
        frame["error"] = frame["y_pred"] - frame["y_true"]
        frame["abs_error"] = frame["error"].abs()
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def metrics_from_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for (model_type, horizon), group in predictions.groupby(["model_type", "horizon_minutes"]):
        y_true = group["y_true"].to_numpy(dtype=np.float32)
        y_pred = group["y_pred"].to_numpy(dtype=np.float32)
        rows.append({
            "model_type": model_type,
            "horizon_minutes": int(horizon),
            "samples": int(len(group)),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "r2": float(r2_score(y_true, y_pred)) if len(group) >= 2 else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["horizon_minutes", "model_type"]).reset_index(drop=True)


def per_patient_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, float | str | int]] = []
    for (model_type, patient_id, year, horizon), group in predictions.groupby(["model_type", "patient_id", "year", "horizon_minutes"]):
        y_true = group["y_true"].to_numpy(dtype=np.float32)
        y_pred = group["y_pred"].to_numpy(dtype=np.float32)
        rows.append({
            "model_type": model_type,
            "patient_id": patient_id,
            "year": year,
            "split": ",".join(sorted(group["split"].astype(str).unique())),
            "horizon_minutes": int(horizon),
            "sample_count": int(len(group)),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "r2": float(r2_score(y_true, y_pred)) if len(group) >= 2 else np.nan,
        })
    per_horizon = pd.DataFrame(rows).sort_values(["model_type", "horizon_minutes", "mae"]).reset_index(drop=True)
    pivot = per_horizon.pivot_table(
        index=["model_type", "patient_id", "year", "split"],
        columns="horizon_minutes",
        values=["sample_count", "mae", "rmse", "r2"],
        aggfunc="first",
    )
    pivot.columns = [f"{metric}_{int(horizon)}m" for metric, horizon in pivot.columns]
    per_patient = pivot.reset_index()
    enriched_90 = per_horizon[(per_horizon["model_type"] == "enriched") & (per_horizon["horizon_minutes"] == 90)]
    worst = enriched_90.sort_values("mae", ascending=False).head(10).reset_index(drop=True)
    best = enriched_90.sort_values("mae", ascending=True).head(10).reset_index(drop=True)
    return per_patient, per_horizon, worst, best


def glucose_range_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = predictions.copy()
    df["range_name"] = np.select(
        [df["y_true"] < 70, df["y_true"] > 180],
        ["low", "high"],
        default="normal",
    )
    rows: list[dict[str, float | str | int]] = []
    for (model_type, horizon, range_name), group in df.groupby(["model_type", "horizon_minutes", "range_name"]):
        rows.append({
            "model_type": model_type,
            "horizon_minutes": int(horizon),
            "range_name": range_name,
            "sample_count": int(len(group)),
            "mae": float(group["abs_error"].mean()),
            "rmse": float((group["error"].pow(2).mean()) ** 0.5),
            "mean_error": float(group["error"].mean()),
            "under_prediction_rate": float((group["error"] < 0).mean()),
            "over_prediction_rate": float((group["error"] > 0).mean()),
        })
    metrics = pd.DataFrame(rows).sort_values(["model_type", "horizon_minutes", "range_name"]).reset_index(drop=True)
    hypo = df[df["range_name"] == "low"].sort_values("abs_error", ascending=False).head(200).reset_index(drop=True)
    hyper = df[df["range_name"] == "high"].sort_values("abs_error", ascending=False).head(200).reset_index(drop=True)
    return metrics, hypo, hyper


def glucose_range(values: pd.Series | np.ndarray) -> np.ndarray:
    return np.select(
        [np.asarray(values) < 70, np.asarray(values) > 180],
        ["low", "high"],
        default="normal",
    )


def fit_range_calibrators(predictions: pd.DataFrame, model_type: str = "enriched") -> pd.DataFrame:
    """Fit a simple range-aware residual correction table.

    Calibration bins use predicted glucose range so the same logic is available
    at inference time without looking at future true glucose.
    """
    df = predictions[predictions["model_type"] == model_type].copy()
    df["predicted_range"] = glucose_range(df["y_pred"])
    rows: list[dict[str, float | str | int]] = []
    for (horizon, predicted_range), group in df.groupby(["horizon_minutes", "predicted_range"]):
        rows.append({
            "horizon_minutes": int(horizon),
            "predicted_range": predicted_range,
            "sample_count": int(len(group)),
            "mean_error": float(group["error"].mean()),
            "median_error": float(group["error"].median()),
            "mae": float(group["abs_error"].mean()),
        })
    return pd.DataFrame(rows).sort_values(["horizon_minutes", "predicted_range"]).reset_index(drop=True)


def apply_range_calibration(predictions: pd.DataFrame, calibration_table: pd.DataFrame) -> pd.DataFrame:
    df = predictions.copy()
    df["predicted_range"] = glucose_range(df["y_pred"])
    merged = df.merge(
        calibration_table[["horizon_minutes", "predicted_range", "mean_error"]],
        on=["horizon_minutes", "predicted_range"],
        how="left",
    )
    merged["calibration_adjustment"] = -merged["mean_error"].fillna(0.0)
    merged["y_pred_raw"] = merged["y_pred"]
    merged["y_pred"] = merged["y_pred_raw"] + merged["calibration_adjustment"]
    merged["error"] = merged["y_pred"] - merged["y_true"]
    merged["abs_error"] = merged["error"].abs()
    merged["model_type"] = merged["model_type"].astype(str) + "_calibrated"
    return merged.drop(columns=["mean_error"])


def train_event_classifiers(
    train_table: pd.DataFrame,
    horizons_minutes: Iterable[int] = DEFAULT_HORIZONS_MINUTES,
    feature_columns: Iterable[str] = ENRICHED_FEATURE_COLUMNS,
) -> dict[str, dict[int, HistGradientBoostingClassifier]]:
    resolved_features = _available_feature_columns(train_table, feature_columns)
    x_train = train_table[resolved_features].to_numpy(dtype=np.float32)
    classifiers: dict[str, dict[int, HistGradientBoostingClassifier]] = {"hypo": {}, "hyper": {}}
    for horizon in horizons_minutes:
        target = train_table[f"target_{horizon}m"]
        labels = {
            "hypo": (target < 70).astype(int).to_numpy(),
            "hyper": (target > 180).astype(int).to_numpy(),
        }
        for event_name, y_train in labels.items():
            model = HistGradientBoostingClassifier(
                max_iter=140,
                learning_rate=0.06,
                max_leaf_nodes=31,
                l2_regularization=0.02,
                random_state=20260521 + int(horizon) + (1 if event_name == "hypo" else 2),
            )
            model.fit(x_train, y_train)
            classifiers[event_name][int(horizon)] = model
    return classifiers


def evaluate_event_classifiers(
    classifiers: dict[str, dict[int, HistGradientBoostingClassifier]],
    eval_table: pd.DataFrame,
    feature_columns: Iterable[str] = ENRICHED_FEATURE_COLUMNS,
) -> pd.DataFrame:
    resolved_features = _available_feature_columns(eval_table, feature_columns)
    x_eval = eval_table[resolved_features].to_numpy(dtype=np.float32)
    rows: list[dict[str, float | str | int]] = []
    for event_name, horizon_models in classifiers.items():
        for horizon, model in sorted(horizon_models.items()):
            y_true = ((eval_table[f"target_{horizon}m"] < 70) if event_name == "hypo" else (eval_table[f"target_{horizon}m"] > 180)).astype(int)
            y_pred = model.predict(x_eval)
            if hasattr(model, "predict_proba"):
                y_prob = model.predict_proba(x_eval)[:, 1]
            else:
                y_prob = y_pred
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_true,
                y_pred,
                average="binary",
                zero_division=0,
            )
            try:
                auc = roc_auc_score(y_true, y_prob)
            except ValueError:
                auc = np.nan
            rows.append({
                "event_type": event_name,
                "horizon_minutes": int(horizon),
                "samples": int(len(y_true)),
                "positive_rate": float(y_true.mean()),
                "accuracy": float(accuracy_score(y_true, y_pred)),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "roc_auc": float(auc),
            })
    return pd.DataFrame(rows).sort_values(["event_type", "horizon_minutes"]).reset_index(drop=True)


def save_range_calibrators(calibration_table: pd.DataFrame, output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    calibration_table.to_json(output_dir / "range_calibrators.json", orient="records", force_ascii=False, indent=2)


def load_range_calibrators(model_dir: str | Path) -> pd.DataFrame:
    path = Path(model_dir) / "range_calibrators.json"
    if not path.exists():
        return pd.DataFrame(columns=["horizon_minutes", "predicted_range", "mean_error"])
    return pd.read_json(path)


def load_range_calibrators_cached(model_dir: str | Path) -> pd.DataFrame:
    key = str(Path(model_dir).resolve())
    if key not in _CALIBRATION_CACHE:
        _CALIBRATION_CACHE[key] = load_range_calibrators(model_dir)
    return _CALIBRATION_CACHE[key]


def save_event_classifiers(
    classifiers: dict[str, dict[int, HistGradientBoostingClassifier]],
    output_dir: str | Path,
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for event_name, horizon_models in classifiers.items():
        for horizon, model in horizon_models.items():
            joblib.dump(model, output_dir / f"glucose_event_{event_name}_{horizon}m.joblib")


def load_event_classifiers(model_dir: str | Path) -> dict[str, dict[int, HistGradientBoostingClassifier]]:
    model_dir = Path(model_dir)
    classifiers: dict[str, dict[int, HistGradientBoostingClassifier]] = {"hypo": {}, "hyper": {}}
    for model_path in sorted(model_dir.glob("glucose_event_*_*m.joblib")):
        suffix = model_path.stem.removeprefix("glucose_event_")
        event_name, horizon_text = suffix.rsplit("_", 1)
        horizon = int(horizon_text.removesuffix("m"))
        classifiers.setdefault(event_name, {})[horizon] = joblib.load(model_path)
    return classifiers


def load_event_classifiers_cached(model_dir: str | Path) -> dict[str, dict[int, HistGradientBoostingClassifier]]:
    key = str(Path(model_dir).resolve())
    if key not in _EVENT_CLASSIFIER_CACHE:
        _EVENT_CLASSIFIER_CACHE[key] = load_event_classifiers(model_dir)
    return _EVENT_CLASSIFIER_CACHE[key]


def load_event_thresholds(model_dir: str | Path) -> dict[str, dict[int, float]]:
    path = Path(model_dir) / "event_thresholds.json"
    if not path.exists():
        return {"hypo": {}, "hyper": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "thresholds" in raw:
        thresholds = raw["thresholds"]
        return {
            event_name: {int(horizon): float(value) for horizon, value in horizon_values.items()}
            for event_name, horizon_values in thresholds.items()
            if isinstance(horizon_values, dict)
        }
    parsed: dict[str, dict[int, float]] = {"hypo": {}, "hyper": {}}
    for event_name in ("hypo", "hyper"):
        event_values = raw.get(event_name, {})
        if not isinstance(event_values, dict):
            continue
        for horizon, value in event_values.items():
            if isinstance(value, dict):
                parsed[event_name][int(horizon)] = float(value.get("threshold", 0.5))
            else:
                parsed[event_name][int(horizon)] = float(value)
    return parsed


def load_event_thresholds_cached(model_dir: str | Path) -> dict[str, dict[int, float]]:
    key = str(Path(model_dir).resolve())
    if key not in _EVENT_THRESHOLD_CACHE:
        _EVENT_THRESHOLD_CACHE[key] = load_event_thresholds(model_dir)
    return _EVENT_THRESHOLD_CACHE[key]


def load_prediction_intervals(model_dir: str | Path) -> dict[int, dict[str, float]]:
    path = Path(model_dir) / "prediction_intervals.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    intervals = raw.get("intervals", raw)
    return {int(horizon): {str(k): float(v) for k, v in values.items()} for horizon, values in intervals.items()}


def load_prediction_intervals_cached(model_dir: str | Path) -> dict[int, dict[str, float]]:
    key = str(Path(model_dir).resolve())
    if key not in _INTERVAL_CACHE:
        _INTERVAL_CACHE[key] = load_prediction_intervals(model_dir)
    return _INTERVAL_CACHE[key]


def save_forecast_models(
    models: dict[int, RegressorMixin],
    output_dir: str | Path,
    feature_columns: Iterable[str] = FEATURE_COLUMNS,
    model_type: str = "history",
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for horizon, model in models.items():
        joblib.dump(model, output_dir / f"glucose_forecast_{horizon}m.joblib")
    joblib.dump(
        {"feature_columns": list(feature_columns), "horizons_minutes": sorted(models), "model_type": model_type},
        output_dir / "metadata.joblib",
    )


def load_forecast_metadata(model_dir: str | Path) -> dict[str, object]:
    metadata_path = Path(model_dir) / "metadata.joblib"
    if not metadata_path.exists():
        return {"feature_columns": FEATURE_COLUMNS, "horizons_minutes": DEFAULT_HORIZONS_MINUTES, "model_type": "history"}
    return joblib.load(metadata_path)


def load_forecast_metadata_cached(model_dir: str | Path) -> dict[str, object]:
    key = str(Path(model_dir).resolve())
    if key not in _METADATA_CACHE:
        _METADATA_CACHE[key] = load_forecast_metadata(model_dir)
    return _METADATA_CACHE[key]


def load_forecast_models(model_dir: str | Path) -> dict[int, HistGradientBoostingRegressor]:
    model_dir = Path(model_dir)
    models: dict[int, HistGradientBoostingRegressor] = {}
    for model_path in sorted(model_dir.glob("glucose_forecast_*m.joblib")):
        horizon = int(model_path.stem.removeprefix("glucose_forecast_").removesuffix("m"))
        models[horizon] = joblib.load(model_path)
    return models


def load_forecast_models_cached(model_dir: str | Path) -> dict[int, HistGradientBoostingRegressor]:
    key = str(Path(model_dir).resolve())
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = load_forecast_models(model_dir)
        _MODEL_CACHE_LOAD_COUNT[key] = _MODEL_CACHE_LOAD_COUNT.get(key, 0) + 1
    return _MODEL_CACHE[key]  # type: ignore[return-value]


def clear_forecast_model_cache() -> None:
    _MODEL_CACHE.clear()
    _MODEL_CACHE_LOAD_COUNT.clear()
    _METADATA_CACHE.clear()
    _CALIBRATION_CACHE.clear()
    _EVENT_CLASSIFIER_CACHE.clear()
    _EVENT_THRESHOLD_CACHE.clear()
    _INTERVAL_CACHE.clear()


def forecast_model_cache_load_count(model_dir: str | Path) -> int:
    key = str(Path(model_dir).resolve())
    return _MODEL_CACHE_LOAD_COUNT.get(key, 0)


def forecast_from_recent_readings(
    readings: list[dict[str, object]],
    models: dict[int, HistGradientBoostingRegressor],
) -> ForecastResult:
    """Forecast 30/60/90m glucose from recent readings.

    At least 13 readings are required so all lag/rolling features are available.
    """
    if len(readings) < 13:
        raise ValueError("CGM 예측에는 최소 13개의 최근 5분 간격 혈당값이 필요합니다.")
    frame = pd.DataFrame(readings).rename(columns={"glucose": "glucose_mg_dl"})
    if "glucose_mg_dl" not in frame:
        raise ValueError("readings에는 glucose_mg_dl 또는 glucose 필드가 필요합니다.")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["patient_id"] = frame.get("patient_id", "api")
    frame["source_file"] = "api_recent_readings"
    featured = add_cgm_features(frame).dropna(subset=FEATURE_COLUMNS)
    if featured.empty:
        raise ValueError("feature를 만들 수 없습니다. 최근 readings 간격과 개수를 확인하세요.")
    x = featured.tail(1)[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    predictions = {horizon: round(float(model.predict(x)[0]), 2) for horizon, model in sorted(models.items())}
    return ForecastResult(predictions=predictions)


def _apply_api_calibration(raw_predictions: dict[int, float], calibration_table: pd.DataFrame) -> dict[int, float]:
    calibrated: dict[int, float] = {}
    for horizon, prediction in raw_predictions.items():
        predicted_range = glucose_range(np.asarray([prediction]))[0]
        match = calibration_table[
            (calibration_table["horizon_minutes"] == horizon)
            & (calibration_table["predicted_range"] == predicted_range)
        ]
        mean_error = float(match["mean_error"].iloc[0]) if not match.empty else 0.0
        calibrated[horizon] = round(float(prediction - mean_error), 2)
    return calibrated


def risk_flags_from_event_probabilities(
    event_probabilities: dict[int, dict[str, float]],
    event_thresholds: dict[str, dict[int, float]] | None = None,
) -> dict[int, dict[str, bool]]:
    thresholds = event_thresholds or {}
    flags: dict[int, dict[str, bool]] = {}
    for horizon, probabilities in event_probabilities.items():
        hypo_threshold = thresholds.get("hypo", {}).get(int(horizon), 0.5)
        hyper_threshold = thresholds.get("hyper", {}).get(int(horizon), 0.5)
        flags[int(horizon)] = {
            "hypo_risk": float(probabilities.get("hypo_probability", 0.0)) >= hypo_threshold,
            "hyper_risk": float(probabilities.get("hyper_probability", 0.0)) >= hyper_threshold,
        }
    return flags


# 예측 범위 폭(mg/dL) 기준 불확실성 등급 경계.
# 배포 모델의 범위 폭은 30분 약 64, 60분 약 107, 90분 약 136 mg/dL이다
# (reports/glucose_forecasting/prediction_interval_metrics.csv). 예전 경계(30/60)는
# 모든 시점이 "high"가 되어 정보가 없었으므로, 시점 간 차이가 드러나도록 다시 잡았다.
UNCERTAINTY_WIDTH_LOW_MAX = 80.0
UNCERTAINTY_WIDTH_MEDIUM_MAX = 120.0
# 실제 혈당 70 미만 구간은 시점마다 오차가 정상 구간보다 크다
# (test_final_range_metrics.csv: low 구간 MAE 14.8/31.8/45.2 vs normal 11.5/19.0/23.9).
LOW_GLUCOSE_UNCERTAINTY_THRESHOLD = 70.0
_UNCERTAINTY_LEVELS = ("low", "medium", "high")
_UNCERTAINTY_LEVEL_KO = {"low": "낮음", "medium": "중간", "high": "높음"}


def _uncertainty_level_from_width(width: float) -> str:
    if width < UNCERTAINTY_WIDTH_LOW_MAX:
        return "low"
    if width < UNCERTAINTY_WIDTH_MEDIUM_MAX:
        return "medium"
    return "high"


def intervals_from_predictions(
    predictions: dict[int, float],
    interval_config: dict[int, dict[str, float]] | None,
    current_glucose: float | None = None,
) -> tuple[dict[int, list[float]] | None, dict[int, str] | None, dict[int, str] | None]:
    """예측 범위와 시점별 불확실성 등급/문구를 만든다.

    등급은 범위 폭으로 정하고, 90분 이상은 UX 지침에 따라 항상 "high"로 둔다.
    현재 혈당이 70 미만이면 그 구간의 오차가 커서 한 단계 올린다.
    """
    if not interval_config:
        return None, None, None
    low_glucose_now = current_glucose is not None and float(current_glucose) < LOW_GLUCOSE_UNCERTAINTY_THRESHOLD
    intervals: dict[int, list[float]] = {}
    levels: dict[int, str] = {}
    messages: dict[int, str] = {}
    for horizon, prediction in predictions.items():
        config = interval_config.get(int(horizon))
        if not config:
            continue
        lower_error = float(config.get("lower_abs_error", config.get("p90_abs_error", 0.0)))
        upper_error = float(config.get("upper_abs_error", config.get("p90_abs_error", 0.0)))
        lower = round(max(0.0, float(prediction) - lower_error), 2)
        upper = round(float(prediction) + upper_error, 2)
        level = _uncertainty_level_from_width(upper - lower)
        if low_glucose_now:
            level = _UNCERTAINTY_LEVELS[min(_UNCERTAINTY_LEVELS.index(level) + 1, len(_UNCERTAINTY_LEVELS) - 1)]
        if int(horizon) >= 90:
            level = "high"
        intervals[int(horizon)] = [lower, upper]
        levels[int(horizon)] = level
        if int(horizon) >= 90:
            message = f"{horizon}분 예측은 불확실성이 높으므로 참고용 범위와 가능성 신호로만 확인하세요."
        else:
            message = (
                f"{horizon}분 예측의 불확실성은 {_UNCERTAINTY_LEVEL_KO[level]} 수준이며, "
                "범위는 최근 validation 오차를 바탕으로 한 참고용 범위입니다."
            )
        if low_glucose_now:
            message += " 현재 혈당이 낮은 구간이라 예측 오차가 평소보다 클 수 있습니다."
        messages[int(horizon)] = message
    return intervals or None, levels or None, messages or None


def _sum_recent_events(events: list[dict[str, object]], reference_time: pd.Timestamp, value_key: str, minutes: int) -> float:
    if not events:
        return 0.0
    frame = pd.DataFrame(events)
    if frame.empty or "timestamp" not in frame or value_key not in frame:
        return 0.0
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    values = pd.to_numeric(frame[value_key], errors="coerce").fillna(0.0)
    mask = (frame["timestamp"] <= reference_time) & (frame["timestamp"] > reference_time - pd.Timedelta(minutes=minutes))
    return float(values[mask].sum())


def build_enriched_features_from_raw_events(
    readings: list[dict[str, object]],
    *,
    meals: list[dict[str, object]] | None = None,
    bolus: list[dict[str, object]] | None = None,
    basal: list[dict[str, object]] | None = None,
    exercise: list[dict[str, object]] | None = None,
    sleep_indicator: float = 0.0,
    patient_id_numeric: float = 0.0,
    biosignals: dict[str, float] | None = None,
) -> dict[str, float]:
    if not readings:
        raise ValueError("readings가 비어 있습니다.")
    reference_time = pd.to_datetime(max(reading["timestamp"] for reading in readings))
    meals = meals or []
    bolus = bolus or []
    basal = basal or []
    exercise = exercise or []
    biosignals = biosignals or {}

    features: dict[str, float] = {
        "carbs_current": _sum_recent_events(meals, reference_time, "carbs_g", 5),
        "carbs_last_30m": _sum_recent_events(meals, reference_time, "carbs_g", 30),
        "carbs_last_60m": _sum_recent_events(meals, reference_time, "carbs_g", 60),
        "carbs_last_120m": _sum_recent_events(meals, reference_time, "carbs_g", 120),
        "carbs_last_180m": _sum_recent_events(meals, reference_time, "carbs_g", 180),
        "bolus_current": _sum_recent_events(bolus, reference_time, "insulin_units", 5),
        "bolus_last_30m": _sum_recent_events(bolus, reference_time, "insulin_units", 30),
        "bolus_last_60m": _sum_recent_events(bolus, reference_time, "insulin_units", 60),
        "bolus_last_120m": _sum_recent_events(bolus, reference_time, "insulin_units", 120),
        "bolus_last_180m": _sum_recent_events(bolus, reference_time, "insulin_units", 180),
        "sleep_indicator": float(sleep_indicator),
        "patient_id_numeric": float(patient_id_numeric),
        "hypo_event_current": 1.0 if float(readings[-1].get("glucose_mg_dl", readings[-1].get("glucose", 999))) < 70 else 0.0,
        "gsr_current": float(biosignals.get("gsr_current", 0.0)),
        "skin_temperature_current": float(biosignals.get("skin_temperature_current", 0.0)),
        "acceleration_current": float(biosignals.get("acceleration_current", 0.0)),
    }
    features["time_since_last_meal"] = np.select(
        [
            features["carbs_current"] > 0,
            features["carbs_last_30m"] > 0,
            features["carbs_last_60m"] > 0,
            features["carbs_last_120m"] > 0,
            features["carbs_last_180m"] > 0,
        ],
        [0.0, 30.0, 60.0, 120.0, 180.0],
        default=240.0,
    ).item()
    features["time_since_last_bolus"] = np.select(
        [
            features["bolus_current"] > 0,
            features["bolus_last_30m"] > 0,
            features["bolus_last_60m"] > 0,
            features["bolus_last_120m"] > 0,
            features["bolus_last_180m"] > 0,
        ],
        [0.0, 30.0, 60.0, 120.0, 180.0],
        default=240.0,
    ).item()
    features["meal_bolus_gap_minutes"] = float(features["time_since_last_meal"] - features["time_since_last_bolus"])
    features["carbs_decay_30m"] = features["carbs_last_30m"] * 0.85
    features["carbs_decay_60m"] = features["carbs_last_60m"] * 0.65
    features["carbs_decay_120m"] = features["carbs_last_120m"] * 0.35
    features["carbs_decay_180m"] = features["carbs_last_180m"] * 0.18
    features["carbs_on_board_proxy"] = (
        features["carbs_decay_30m"] + features["carbs_decay_60m"] + features["carbs_decay_120m"] + features["carbs_decay_180m"]
    )
    features["insulin_decay_60m"] = features["bolus_last_60m"] * 0.80
    features["insulin_decay_120m"] = features["bolus_last_120m"] * 0.55
    features["insulin_decay_180m"] = features["bolus_last_180m"] * 0.30
    features["insulin_decay_240m"] = features["bolus_last_180m"] * 0.15
    features["insulin_on_board_proxy"] = (
        features["insulin_decay_60m"] + features["insulin_decay_120m"] + features["insulin_decay_180m"] + features["insulin_decay_240m"]
    )
    features["carb_insulin_ratio_proxy"] = features["carbs_on_board_proxy"] / (features["insulin_on_board_proxy"] + 1.0)
    features["net_glucose_pressure_proxy"] = features["carbs_on_board_proxy"] - features["insulin_on_board_proxy"] * 12.0

    basal_frame = pd.DataFrame(basal)
    if not basal_frame.empty and {"timestamp", "rate_units_per_hour"}.issubset(basal_frame.columns):
        basal_frame["timestamp"] = pd.to_datetime(basal_frame["timestamp"])
        basal_frame["rate_units_per_hour"] = pd.to_numeric(basal_frame["rate_units_per_hour"], errors="coerce").fillna(0.0)
        past_basal = basal_frame[basal_frame["timestamp"] <= reference_time].sort_values("timestamp")
        features["basal_current"] = float(past_basal["rate_units_per_hour"].iloc[-1]) if not past_basal.empty else 0.0
        for minutes in (60, 120):
            mask = (basal_frame["timestamp"] <= reference_time) & (
                basal_frame["timestamp"] > reference_time - pd.Timedelta(minutes=minutes)
            )
            features[f"basal_mean_{minutes}m"] = float(basal_frame.loc[mask, "rate_units_per_hour"].mean()) if mask.any() else features["basal_current"]
    else:
        features["basal_current"] = 0.0
        features["basal_mean_60m"] = 0.0
        features["basal_mean_120m"] = 0.0
    features["basal_mean_180m"] = float(features.get("basal_mean_120m", 0.0))

    exercise_frame = pd.DataFrame(exercise)
    features["exercise_active"] = 0.0
    features["exercise_last_60m"] = 0.0
    features["exercise_last_120m"] = 0.0
    if not exercise_frame.empty and "timestamp" in exercise_frame:
        exercise_frame["timestamp"] = pd.to_datetime(exercise_frame["timestamp"])
        durations = pd.to_numeric(exercise_frame.get("duration_minutes", 0.0), errors="coerce").fillna(0.0)
        end_times = exercise_frame["timestamp"] + pd.to_timedelta(durations, unit="m")
        features["exercise_active"] = float(((exercise_frame["timestamp"] <= reference_time) & (end_times >= reference_time)).any())
        for minutes in (60, 120):
            recent = (end_times <= reference_time) & (end_times > reference_time - pd.Timedelta(minutes=minutes))
            features[f"exercise_last_{minutes}m"] = float(recent.any() or bool(features["exercise_active"]))
    features["exercise_last_180m"] = features.get("exercise_last_120m", 0.0)
    return features


def _expand_unknown_patient_rows(x: np.ndarray, feature_columns: list[str]) -> np.ndarray:
    """patient_id_numeric이 학습 환자 ID가 아니면 학습 환자 수만큼 행을 복제해 ID만 바꾼다.

    트리 모델은 처음 보는 ID(예: 기본값 0)를 가장 가까운 분기, 즉 가장 작은 ID인
    환자 540처럼 취급한다. 특정 환자 한 명 대신 학습 환자 전체의 평균 반응을 쓰기 위함이다.
    """
    if "patient_id_numeric" not in feature_columns:
        return x
    column = feature_columns.index("patient_id_numeric")
    if int(round(float(x[0, column]))) in OHIOT1DM_TRAINING_PATIENT_IDS:
        return x
    expanded = np.repeat(x[:1], len(OHIOT1DM_TRAINING_PATIENT_IDS), axis=0)
    expanded[:, column] = np.asarray(OHIOT1DM_TRAINING_PATIENT_IDS, dtype=x.dtype)
    return expanded


def forecast_from_enriched_payload(
    readings: list[dict[str, object]],
    event_features: dict[str, object],
    models: dict[int, RegressorMixin],
    *,
    calibration_table: pd.DataFrame | None = None,
    event_classifiers: dict[str, dict[int, HistGradientBoostingClassifier]] | None = None,
    event_thresholds: dict[str, dict[int, float]] | None = None,
    interval_config: dict[int, dict[str, float]] | None = None,
    feature_columns: Iterable[str] = ENRICHED_FEATURE_COLUMNS,
) -> ForecastResult:
    if len(readings) < 13:
        raise ValueError("CGM 예측에는 최소 13개의 최근 5분 간격 혈당값이 필요합니다.")
    frame = pd.DataFrame(readings).rename(columns={"glucose": "glucose_mg_dl"})
    if "glucose_mg_dl" not in frame:
        raise ValueError("readings에는 glucose_mg_dl 또는 glucose 필드가 필요합니다.")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["patient_id"] = frame.get("patient_id", "api")
    frame["source_file"] = "api_recent_readings"
    featured = add_cgm_features(frame)
    featured = add_long_horizon_features(featured)
    latest = featured.tail(1).copy()
    for column in ENRICHED_ONLY_FEATURE_COLUMNS + LONG_HORIZON_FEATURE_COLUMNS:
        latest[column] = float(event_features.get(column, latest[column].iloc[0] if column in latest else 0.0))
    resolved_features = _available_feature_columns(latest, feature_columns)
    if latest[resolved_features].isna().any().any():
        raise ValueError("feature를 만들 수 없습니다. 최근 readings 간격과 event feature를 확인하세요.")
    x = latest[resolved_features].to_numpy(dtype=np.float32)
    x = _expand_unknown_patient_rows(x, resolved_features)
    # 모르는 사용자는 학습 환자 ID별로 한 행씩 만들어 두었으므로 결과를 평균한다.
    raw_predictions = {
        horizon: round(float(np.mean(model.predict(x))), 2) for horizon, model in sorted(models.items())
    }
    calibrated_predictions = None
    if calibration_table is not None and not calibration_table.empty:
        calibrated_predictions = _apply_api_calibration(raw_predictions, calibration_table)
    event_probabilities: dict[int, dict[str, float]] = {}
    if event_classifiers:
        for event_name, horizon_models in event_classifiers.items():
            for horizon, model in horizon_models.items():
                event_x = x
                expected_features = getattr(model, "n_features_in_", None)
                if expected_features is not None:
                    expected_features = int(expected_features)
                    if expected_features > x.shape[1]:
                        continue
                    event_x = x[:, :expected_features]
                if hasattr(model, "predict_proba"):
                    probability = float(np.mean(model.predict_proba(event_x)[:, 1]))
                else:
                    probability = float(np.mean(model.predict(event_x)))
                event_probabilities.setdefault(int(horizon), {})[f"{event_name}_probability"] = round(probability, 4)
    intervals, uncertainty_level, uncertainty_message = intervals_from_predictions(
        calibrated_predictions or raw_predictions,
        interval_config,
        current_glucose=float(latest["glucose_mg_dl"].iloc[0]),
    )
    return ForecastResult(
        predictions=raw_predictions,
        calibrated_predictions=calibrated_predictions,
        event_probabilities=event_probabilities or None,
        risk_flags=risk_flags_from_event_probabilities(event_probabilities, event_thresholds) if event_probabilities else None,
        prediction_intervals=intervals,
        uncertainty_level=uncertainty_level,
        uncertainty_message=uncertainty_message,
    )
