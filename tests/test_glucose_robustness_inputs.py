from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from api.schemas.models import CGMReading
from src.glucose.forecasting import build_enriched_features_from_raw_events, forecast_from_enriched_payload


class ConstantForecastModel:
    def __init__(self, value: float):
        self.value = value

    def predict(self, x):
        return [self.value] * len(x)


def _readings(count: int = 13):
    start = datetime(2026, 1, 1, 0, 0, 0)
    return [
        {"timestamp": str(start + timedelta(minutes=idx * 5)), "glucose_mg_dl": 110 + idx}
        for idx in range(count)
    ]


def test_missing_meal_bolus_basal_inputs_fallback_to_zero_features():
    features = build_enriched_features_from_raw_events(_readings(), meals=[], bolus=[], basal=[])

    assert features["carbs_last_60m"] == 0.0
    assert features["bolus_last_60m"] == 0.0
    assert features["basal_current"] == 0.0
    assert features["time_since_last_meal"] == 240.0
    assert features["time_since_last_bolus"] == 240.0


def test_insufficient_cgm_readings_raise_safe_validation_error():
    with pytest.raises(ValueError, match="최소 13개"):
        forecast_from_enriched_payload(
            _readings(count=12),
            {},
            {30: ConstantForecastModel(120)},
        )


def test_invalid_timestamp_is_rejected_by_schema():
    with pytest.raises(ValidationError):
        CGMReading(timestamp="not-a-time", glucose_mg_dl=120)


def test_out_of_range_glucose_is_rejected_by_schema():
    with pytest.raises(ValidationError):
        CGMReading(timestamp="2026-01-01T00:00:00", glucose_mg_dl=999)

