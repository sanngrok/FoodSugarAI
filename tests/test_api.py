"""FastAPI 엔드포인트 통합 테스트"""

import io
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.classifier.food_classifier import ClassificationResult
from src.glucose.forecasting import clear_forecast_model_cache, forecast_model_cache_load_count
from src.predictor.sugar_predictor import PredictionResult


def _make_image_bytes() -> bytes:
    """1x1 빨간 픽셀 PNG 생성"""
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color=(200, 100, 50)).save(buf, format="JPEG")
    return buf.getvalue()


class _ConstantForecastModel:
    def __init__(self, value: float):
        self.value = value

    def predict(self, x):
        return np.full(len(x), self.value)


class _ConstantEventClassifier:
    def __init__(self, probability: float):
        self.probability = probability

    def predict_proba(self, x):
        negative = np.full(len(x), 1.0 - self.probability)
        positive = np.full(len(x), self.probability)
        return np.column_stack([negative, positive])


@pytest.fixture
def mock_classifier():
    clf = MagicMock()
    clf.predict.return_value = ClassificationResult(
        food_key="pizza",
        food_name_ko="피자",
        confidence=0.92,
        top5=[("pizza", 0.92), ("lasagna", 0.04), ("spaghetti_bolognese", 0.02),
              ("garlic_bread", 0.01), ("nachos", 0.01)],
    )
    return clf


@pytest.fixture
def mock_predictor():
    pred = MagicMock()
    pred.predict.return_value = PredictionResult(
        risk_level=1,
        risk_label="주의",
        risk_color="#f39c12",
        risk_emoji="⚠️",
        probabilities={"낮음": 0.1, "주의": 0.7, "높음": 0.2},
        serving_advice="섭취량을 줄이세요.",
    )
    pred.predict_from_dict.return_value = pred.predict.return_value
    return pred


@pytest.fixture
def client(mock_classifier, mock_predictor):
    # Patch FoodClassifier and SugarPredictor in the lifespan so that
    # no actual model is loaded (avoids torch/xgboost crashes in CI/test envs).
    with patch("api.main.load_classifier", return_value=mock_classifier), \
         patch("api.main.SugarPredictor", return_value=mock_predictor):
        from api.main import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestClassifyEndpoint:
    def test_classify_image(self, client):
        resp = client.post(
            "/predict/classify",
            files={"file": ("food.jpg", _make_image_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["food_key"] == "pizza"
        assert data["confidence"] == pytest.approx(0.92)
        assert len(data["top5"]) == 5

    def test_classify_invalid_file(self, client):
        resp = client.post(
            "/predict/classify",
            files={"file": ("bad.jpg", b"not an image", "image/jpeg")},
        )
        assert resp.status_code == 400


class TestRiskEndpoint:
    def test_predict_risk(self, client):
        payload = {
            "food_name": "피자",
            "calories": 266,
            "carbs": 33,
            "sugar": 3.5,
            "protein": 11,
            "fat": 10,
            "fiber": 2.3,
            "glycemic_index": 60,
            "portion_g": 200,
        }
        resp = client.post("/predict/risk", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_label"] in ("낮음", "주의", "높음")
        assert abs(sum(data["probabilities"].values()) - 1.0) < 0.01
        assert "참고용" in data["reference_notice"]

    def test_glucose_risk_score(self, client):
        payload = {
            "food_name": "떡볶이",
            "calories": 220,
            "carbs": 45,
            "sugar": 12,
            "protein": 5,
            "fat": 4,
            "fiber": 2,
            "glycemic_index": 70,
            "portion_g": 150,
        }
        resp = client.post("/predict/glucose-risk", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert 0 <= data["score"] <= 100
        assert data["level"] in ("낮음", "주의", "높음")
        assert "참고용" in data["reference_notice"]

    def test_invalid_portion(self, client):
        payload = {
            "calories": 200, "carbs": 30, "sugar": 10,
            "protein": 8, "fat": 5, "portion_g": -10,
        }
        resp = client.post("/predict/risk", json=payload)
        assert resp.status_code == 422  # validation error


class TestAnalyzeEndpoint:
    def test_full_analysis(self, client):
        resp = client.post(
            "/predict/analyze",
            files={"file": ("food.jpg", _make_image_bytes(), "image/jpeg")},
            data={"portion_g": "150"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "classification" in data
        assert "risk" in data
        assert "glucose_risk" in data
        assert data["classification"]["food_key"] == "pizza"
        assert data["glucose_risk"]["level"] in ("낮음", "주의", "높음")


class TestCGMForecastEndpoint:
    def _payload(self):
        start = datetime(2026, 1, 1, 0, 0, 0)
        return {
            "readings": [
                {"timestamp": str(start + timedelta(minutes=idx * 5)), "glucose_mg_dl": 100 + idx}
                for idx in range(13)
            ]
        }

    def test_cgm_forecast_missing_model_dir_returns_503(self, client, monkeypatch, tmp_path):
        from config.settings import settings

        clear_forecast_model_cache()
        monkeypatch.setattr(settings, "glucose_forecast_model_dir", tmp_path / "missing")

        resp = client.post("/predict/cgm-forecast", json=self._payload())

        assert resp.status_code == 503

    def test_cgm_forecast_uses_model_cache(self, client, monkeypatch, tmp_path):
        from config.settings import settings

        clear_forecast_model_cache()
        for horizon, value in [(30, 120), (60, 140), (90, 160)]:
            joblib.dump(_ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")
        monkeypatch.setattr(settings, "glucose_forecast_model_dir", tmp_path)

        first = client.post("/predict/cgm-forecast", json=self._payload())
        second = client.post("/predict/cgm-forecast", json=self._payload())

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["predictions_mg_dl"] == {"30": 120.0, "60": 140.0, "90": 160.0}
        assert "참고용" in first.json()["reference_notice"]
        assert forecast_model_cache_load_count(tmp_path) == 1

    def test_cgm_forecast_enriched_returns_calibration_and_events(self, client, monkeypatch, tmp_path):
        from config.settings import settings

        clear_forecast_model_cache()
        for horizon, value in [(30, 120), (60, 190), (90, 60)]:
            joblib.dump(_ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")
        for event_name, probability in [("hypo", 0.2), ("hyper", 0.7)]:
            for horizon in [30, 60, 90]:
                joblib.dump(
                    _ConstantEventClassifier(probability),
                    tmp_path / f"glucose_event_{event_name}_{horizon}m.joblib",
                )
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
                    "patient_id_numeric",
                ],
                "horizons_minutes": [30, 60, 90],
                "model_type": "enriched",
            },
            tmp_path / "metadata.joblib",
        )
        (tmp_path / "range_calibrators.json").write_text(
            """[
  {"horizon_minutes":30,"predicted_range":"normal","mean_error":2.0},
  {"horizon_minutes":60,"predicted_range":"high","mean_error":-5.0},
  {"horizon_minutes":90,"predicted_range":"low","mean_error":10.0}
]""",
            encoding="utf-8",
        )
        (tmp_path / "event_thresholds.json").write_text(
            '{"thresholds":{"hypo":{"30":0.15,"60":0.15,"90":0.15},"hyper":{"30":0.5,"60":0.5,"90":0.5}}}',
            encoding="utf-8",
        )
        monkeypatch.setattr(settings, "glucose_forecast_enriched_model_dir", tmp_path)
        payload = self._payload()
        payload["event_features"] = {
            "carbs_last_60m": 45,
            "bolus_last_60m": 4,
            "basal_current": 1.0,
            "patient_id_numeric": 540,
        }

        resp = client.post("/predict/cgm-forecast-enriched", json=payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["predictions_mg_dl"] == {"30": 120.0, "60": 190.0, "90": 60.0}
        assert data["calibrated_predictions_mg_dl"] == {"30": 118.0, "60": 195.0, "90": 50.0}
        assert data["event_probabilities"]["30"]["hypo_probability"] == 0.2
        assert data["event_probabilities"]["60"]["hyper_probability"] == 0.7
        assert data["risk_flags"]["30"]["hypo_risk"] is True
        assert data["risk_flags"]["60"]["hyper_risk"] is True
        assert "참고용" in data["reference_notice"]
        assert "의료진" in data["safety_warning"]

    def test_cgm_forecast_enriched_events_accepts_raw_events(self, client, monkeypatch, tmp_path):
        from config.settings import settings

        clear_forecast_model_cache()
        for horizon, value in [(30, 120), (60, 190), (90, 60)]:
            joblib.dump(_ConstantForecastModel(value), tmp_path / f"glucose_forecast_{horizon}m.joblib")
        for event_name, probability in [("hypo", 0.2), ("hyper", 0.7)]:
            for horizon in [30, 60, 90]:
                joblib.dump(
                    _ConstantEventClassifier(probability),
                    tmp_path / f"glucose_event_{event_name}_{horizon}m.joblib",
                )
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
                    "exercise_active",
                    "sleep_indicator",
                    "patient_id_numeric",
                ],
                "horizons_minutes": [30, 60, 90],
                "model_type": "enriched",
            },
            tmp_path / "metadata.joblib",
        )
        (tmp_path / "range_calibrators.json").write_text(
            '[{"horizon_minutes":30,"predicted_range":"normal","mean_error":2.0}]',
            encoding="utf-8",
        )
        (tmp_path / "event_thresholds.json").write_text(
            '{"thresholds":{"hypo":{"30":0.15,"60":0.15,"90":0.15},"hyper":{"30":0.5,"60":0.5,"90":0.5}}}',
            encoding="utf-8",
        )
        monkeypatch.setattr(settings, "glucose_forecast_enriched_model_dir", tmp_path)
        payload = self._payload()
        latest = payload["readings"][-1]["timestamp"]
        payload.update({
            "meals": [{"timestamp": latest, "carbs_g": 42}],
            "bolus": [{"timestamp": latest, "insulin_units": 4}],
            "basal": [{"timestamp": latest, "rate_units_per_hour": 1.2}],
            "exercise": [{"timestamp": latest, "duration_minutes": 30, "intensity": "moderate"}],
            "sleep_indicator": 0,
            "patient_id_numeric": 540,
        })

        resp = client.post("/predict/cgm-forecast-enriched-events", json=payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["model_type"] == "enriched_events"
        assert data["engineered_event_features"]["carbs_current"] == 42
        assert data["engineered_event_features"]["bolus_last_60m"] == 4
        assert data["risk_flags"]["30"]["hypo_risk"] is True
        assert "참고용" in data["reference_notice"]
