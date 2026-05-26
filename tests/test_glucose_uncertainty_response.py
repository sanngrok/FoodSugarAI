from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.classifier.food_classifier import ClassificationResult
from src.glucose.forecasting import clear_forecast_model_cache
from src.predictor.sugar_predictor import PredictionResult


class ConstantForecastModel:
    def __init__(self, value: float):
        self.value = value

    def predict(self, x):
        return np.full(len(x), self.value)


@pytest.fixture
def client():
    classifier = MagicMock()
    classifier.predict.return_value = ClassificationResult(
        food_key="pizza",
        food_name_ko="피자",
        confidence=0.9,
        top5=[("pizza", 0.9)],
    )
    predictor = MagicMock()
    predictor.predict.return_value = PredictionResult(
        risk_level=0,
        risk_label="낮음",
        risk_color="#2ecc71",
        risk_emoji="",
        probabilities={"낮음": 1.0},
        serving_advice="",
    )
    predictor.predict_from_dict.return_value = predictor.predict.return_value
    with patch("api.main.load_classifier", return_value=classifier), \
         patch("api.main.SugarPredictor", return_value=predictor):
        from api.main import app
        with TestClient(app) as test_client:
            yield test_client


def _payload():
    start = datetime(2026, 1, 1, 0, 0, 0)
    return {
        "readings": [
            {"timestamp": str(start + timedelta(minutes=idx * 5)), "glucose_mg_dl": 100 + idx}
            for idx in range(13)
        ],
        "event_features": {
            "carbs_last_60m": 35,
            "bolus_last_60m": 2,
            "basal_current": 1.0,
        },
    }


def test_enriched_response_contains_90m_uncertainty_warning(client, monkeypatch, tmp_path):
    from config.settings import settings

    clear_forecast_model_cache()
    for horizon, value in [(30, 120), (60, 150), (90, 170)]:
        joblib.dump(ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")
    joblib.dump(
        {
            "feature_columns": [
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
                "carbs_last_60m",
                "bolus_last_60m",
                "basal_current",
            ],
            "horizons_minutes": [30, 60, 90],
            "model_type": "enriched_long_horizon",
        },
        tmp_path / "metadata.joblib",
    )
    (tmp_path / "prediction_intervals.json").write_text(
        '{"intervals":{"30":{"p90_abs_error":10},"60":{"p90_abs_error":40},"90":{"p90_abs_error":80}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "glucose_forecast_enriched_model_dir", tmp_path)

    resp = client.post("/predict/cgm-forecast-enriched", json=_payload())

    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction_intervals_mg_dl"]["90"] == [90.0, 250.0]
    assert data["uncertainty_level"]["90"] == "high"
    assert "불확실성" in data["uncertainty_message"]["90"]
    assert "참고용" in data["uncertainty_message"]["90"]
    assert "참고용" in data["reference_notice"]
    assert "치료 지침" in data["reference_notice"]

