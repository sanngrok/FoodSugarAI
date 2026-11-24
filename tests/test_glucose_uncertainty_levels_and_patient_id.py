"""불확실성 등급이 시점마다 구분되는지, 모르는 환자 ID가 학습 환자 평균으로 처리되는지 확인한다."""

from datetime import datetime, timedelta

import numpy as np

from src.glucose.constants import OHIOT1DM_TRAINING_PATIENT_IDS
from src.glucose.forecasting import (
    ENRICHED_FEATURE_COLUMNS,
    forecast_from_enriched_payload,
    intervals_from_predictions,
)

# 배포 모델의 prediction_intervals.json과 같은 크기(범위 폭 약 64 / 107 / 136 mg/dL)
DEPLOYED_LIKE_INTERVALS = {
    30: {"lower_abs_error": 32.3, "upper_abs_error": 32.2},
    60: {"lower_abs_error": 53.6, "upper_abs_error": 53.5},
    90: {"lower_abs_error": 68.1, "upper_abs_error": 68.0},
}
PATIENT_COLUMN = ENRICHED_FEATURE_COLUMNS.index("patient_id_numeric")


class PatientDependentModel:
    """patient_id_numeric 값에 따라 다른 값을 내는 가짜 회귀 모델."""

    def predict(self, x):
        return 100.0 + (np.asarray(x)[:, PATIENT_COLUMN] - 540.0)


class PatientDependentClassifier:
    n_features_in_ = len(ENRICHED_FEATURE_COLUMNS)

    def predict_proba(self, x):
        positive = np.where(np.asarray(x)[:, PATIENT_COLUMN] == 540.0, 0.9, 0.1)
        return np.column_stack([1.0 - positive, positive])


def _readings(value: float = 110.0, count: int = 37):
    start = datetime(2026, 5, 26, 9, 0)
    return [
        {"timestamp": (start + timedelta(minutes=5 * i)).isoformat(), "glucose_mg_dl": value}
        for i in range(count)
    ]


def test_deployed_interval_widths_give_distinct_levels_per_horizon():
    _, levels, messages = intervals_from_predictions({30: 110.0, 60: 120.0, 90: 140.0}, DEPLOYED_LIKE_INTERVALS)

    assert levels == {30: "low", 60: "medium", 90: "high"}
    assert "낮음" in messages[30]
    assert "중간" in messages[60]
    assert "high" not in messages[90]
    assert "불확실성이 높으므로" in messages[90]
    assert all("참고용" in message for message in messages.values())


def test_low_current_glucose_raises_uncertainty_one_level():
    _, levels, messages = intervals_from_predictions(
        {30: 80.0, 60: 120.0, 90: 180.0}, DEPLOYED_LIKE_INTERVALS, current_glucose=65.0
    )

    assert levels == {30: "medium", 60: "high", 90: "high"}
    assert all("낮은 구간" in message for message in messages.values())


def test_90m_is_always_high_even_with_narrow_interval():
    _, levels, _ = intervals_from_predictions({90: 150.0}, {90: {"p90_abs_error": 5.0}})

    assert levels[90] == "high"


def test_unknown_patient_id_averages_over_training_patients():
    models = {30: PatientDependentModel()}
    expected = round(float(np.mean([100.0 + (pid - 540.0) for pid in OHIOT1DM_TRAINING_PATIENT_IDS])), 2)

    for unknown_id in (0.0, 999.0):
        result = forecast_from_enriched_payload(
            _readings(), {"patient_id_numeric": unknown_id}, models, feature_columns=ENRICHED_FEATURE_COLUMNS
        )
        assert result.predictions[30] == expected

    # 학습 환자 540과 같은 값이 나오면 안 된다 (예전 동작)
    assert expected != 100.0


def test_known_patient_id_is_used_as_is():
    models = {30: PatientDependentModel()}

    result = forecast_from_enriched_payload(
        _readings(), {"patient_id_numeric": 570.0}, models, feature_columns=ENRICHED_FEATURE_COLUMNS
    )

    assert result.predictions[30] == 130.0


def test_unknown_patient_id_averages_event_probabilities():
    models = {30: PatientDependentModel()}
    classifiers = {"hypo": {30: PatientDependentClassifier()}}

    result = forecast_from_enriched_payload(
        _readings(), {}, models, event_classifiers=classifiers, feature_columns=ENRICHED_FEATURE_COLUMNS
    )

    expected = round((0.9 + 0.1 * (len(OHIOT1DM_TRAINING_PATIENT_IDS) - 1)) / len(OHIOT1DM_TRAINING_PATIENT_IDS), 4)
    assert result.event_probabilities[30]["hypo_probability"] == expected
