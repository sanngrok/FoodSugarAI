from datetime import datetime, timedelta

import numpy as np

from src.glucose.forecasting import forecast_from_enriched_payload


class ConstantRegressor:
    def predict(self, x):
        return np.full(len(x), 150.0)


class LegacyEventClassifier:
    n_features_in_ = 16

    def predict_proba(self, x):
        assert x.shape[1] == self.n_features_in_
        return np.column_stack([np.full(len(x), 0.7), np.full(len(x), 0.3)])


def _readings(count: int = 37):
    start = datetime(2026, 1, 1, 12, 0, 0)
    return [
        {"timestamp": str(start + timedelta(minutes=idx * 5)), "glucose_mg_dl": 100 + idx}
        for idx in range(count)
    ]


def test_legacy_event_classifier_accepts_prefix_features_with_long_horizon_input():
    feature_columns = [
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
        "glucose_slope_60m",
        "glucose_slope_120m",
    ]

    result = forecast_from_enriched_payload(
        _readings(),
        {},
        {30: ConstantRegressor()},
        event_classifiers={"hypo": {30: LegacyEventClassifier()}},
        event_thresholds={"hypo": {30: 0.2}, "hyper": {}},
        feature_columns=feature_columns,
    )

    assert result.event_probabilities == {30: {"hypo_probability": 0.3}}
    assert result.risk_flags == {30: {"hypo_risk": True, "hyper_risk": False}}
