import joblib
from datetime import datetime, timedelta

from src.glucose.forecasting import (
    clear_forecast_model_cache,
    forecast_from_enriched_payload,
    load_forecast_models_cached,
    load_prediction_intervals_cached,
)


class ConstantForecastModel:
    def __init__(self, value: float):
        self.value = value

    def predict(self, x):
        return [self.value] * len(x)


def _readings():
    start = datetime(2026, 1, 1, 0, 0, 0)
    return [
        {"timestamp": str(start + timedelta(minutes=idx * 5)), "glucose_mg_dl": 100 + idx}
        for idx in range(13)
    ]


def test_forecast_from_enriched_payload_returns_uncertainty(tmp_path):
    clear_forecast_model_cache()
    for horizon, value in [(30, 120), (60, 150), (90, 170)]:
        joblib.dump(ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")
    (tmp_path / "prediction_intervals.json").write_text(
        '{"intervals":{"30":{"p90_abs_error":10},"60":{"p90_abs_error":25},"90":{"p90_abs_error":45}}}',
        encoding="utf-8",
    )
    models = load_forecast_models_cached(tmp_path)
    intervals = load_prediction_intervals_cached(tmp_path)

    result = forecast_from_enriched_payload(_readings(), {}, models, interval_config=intervals)

    assert result.prediction_intervals[90] == [125.0, 215.0]
    assert result.uncertainty_level[90] == "high"
    assert "참고용" in result.uncertainty_message[90]
