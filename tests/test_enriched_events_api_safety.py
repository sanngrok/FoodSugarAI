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


class ConstantEventClassifier:
    def __init__(self, probability: float):
        self.probability = probability

    def predict_proba(self, x):
        negative = np.full(len(x), 1.0 - self.probability)
        positive = np.full(len(x), self.probability)
        return np.column_stack([negative, positive])


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


@pytest.fixture
def enriched_model_dir(tmp_path):
    clear_forecast_model_cache()
    for horizon, value in [(30, 120), (60, 150), (90, 68)]:
        joblib.dump(ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")
    for event_name, probability in [("hypo", 0.8), ("hyper", 0.1)]:
        for horizon in [30, 60, 90]:
            joblib.dump(ConstantEventClassifier(probability), tmp_path / f"glucose_event_{event_name}_{horizon}m.joblib")
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
                "carbs_current",
                "carbs_last_60m",
                "bolus_last_60m",
                "basal_current",
                "sleep_indicator",
                "patient_id_numeric",
            ],
            "horizons_minutes": [30, 60, 90],
            "model_type": "enriched",
        },
        tmp_path / "metadata.joblib",
    )
    (tmp_path / "range_calibrators.json").write_text(
        '[{"horizon_minutes":90,"predicted_range":"low","mean_error":0.0}]',
        encoding="utf-8",
    )
    (tmp_path / "event_thresholds.json").write_text(
        '{"thresholds":{"hypo":{"30":0.5,"60":0.5,"90":0.5},"hyper":{"30":0.5,"60":0.5,"90":0.5}}}',
        encoding="utf-8",
    )
    return tmp_path


def _payload(reading_count: int = 13):
    start = datetime(2026, 1, 1, 0, 0, 0)
    readings = [
        {"timestamp": str(start + timedelta(minutes=idx * 5)), "glucose_mg_dl": 110 + idx}
        for idx in range(reading_count)
    ]
    latest = readings[-1]["timestamp"]
    return {
        "readings": readings,
        "meals": [{"timestamp": latest, "carbs_g": 30}],
        "bolus": [{"timestamp": latest, "insulin_units": 2}],
        "basal": [{"timestamp": latest, "rate_units_per_hour": 1.0}],
        "sleep_indicator": 0,
    }


def test_enriched_events_response_uses_safety_language(client, monkeypatch, enriched_model_dir):
    from config.settings import settings

    monkeypatch.setattr(settings, "glucose_forecast_enriched_model_dir", enriched_model_dir)

    resp = client.post("/predict/cgm-forecast-enriched-events", json=_payload())

    assert resp.status_code == 200
    data = resp.json()
    assert "참고용" in data["reference_notice"]
    assert "의료진" in data["safety_warning"]
    assert data["risk_flags"]["90"]["hypo_risk"] is True
    assert data["risk_messages"]["90"]
    message_text = " ".join(data["risk_messages"]["90"])
    assert "가능성 신호" in message_text
    assert "확정" not in message_text
    assert "저혈당입니다" not in message_text
    assert "인슐린을 조절" not in message_text


def test_enriched_events_rejects_negative_inputs(client, monkeypatch, enriched_model_dir):
    from config.settings import settings

    monkeypatch.setattr(settings, "glucose_forecast_enriched_model_dir", enriched_model_dir)
    payload = _payload()
    payload["meals"][0]["carbs_g"] = -1

    resp = client.post("/predict/cgm-forecast-enriched-events", json=payload)

    assert resp.status_code == 422


def test_enriched_events_rejects_insufficient_readings_safely(client, monkeypatch, enriched_model_dir):
    from config.settings import settings

    monkeypatch.setattr(settings, "glucose_forecast_enriched_model_dir", enriched_model_dir)

    resp = client.post("/predict/cgm-forecast-enriched-events", json=_payload(reading_count=12))

    assert resp.status_code == 422
