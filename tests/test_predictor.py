"""XGBoost 혈당 위험도 예측기 단위 테스트"""

import numpy as np
import pytest

from src.nutrition.nutrition_db import NutritionInfo, get_nutrition
from src.predictor.sugar_predictor import (
    SugarPredictor,
    _nutrition_to_features,
    _rule_based_predict,
    FEATURE_NAMES,
)


@pytest.fixture
def predictor():
    # 모델 파일 없이도 rule-based fallback으로 동작
    return SugarPredictor(model_path=None.__class__.__new__(type(None)))


@pytest.fixture
def predictor_no_model(tmp_path):
    return SugarPredictor(model_path=tmp_path / "nonexistent.pkl")


# ── 피처 변환 ────────────────────────────────────────────────────────────────
class TestNutritionToFeatures:
    def test_feature_length(self):
        info = NutritionInfo("테스트", 200, 30, 10, 8, 5, 2, 55)
        feat = _nutrition_to_features(info)
        assert len(feat) == len(FEATURE_NAMES)

    def test_portion_scaling(self):
        info = NutritionInfo("테스트", 200, 30, 10, 8, 5, 2, 55)
        feat_100 = _nutrition_to_features(info, 100)
        feat_200 = _nutrition_to_features(info, 200)
        # GI는 포션과 무관
        assert feat_200[FEATURE_NAMES.index("glycemic_index")] == feat_100[FEATURE_NAMES.index("glycemic_index")]
        # 칼로리는 2배
        assert np.isclose(feat_200[FEATURE_NAMES.index("calories")],
                          feat_100[FEATURE_NAMES.index("calories")] * 2)


# ── Rule-based 예측 ───────────────────────────────────────────────────────────
class TestRuleBasedPredict:
    def _make_features(self, sugar, gi, carbs):
        info = NutritionInfo("t", 200, carbs, sugar, 5, 5, 2, gi)
        return _nutrition_to_features(info)

    def test_low_risk(self):
        feat = self._make_features(sugar=2, gi=30, carbs=5)
        result = _rule_based_predict(feat)
        assert result.risk_level == 0
        assert result.risk_label == "낮음"

    def test_caution_risk(self):
        feat = self._make_features(sugar=12, gi=58, carbs=30)
        result = _rule_based_predict(feat)
        assert result.risk_level in (1, 2)

    def test_high_risk(self):
        feat = self._make_features(sugar=35, gi=85, carbs=60)
        result = _rule_based_predict(feat)
        assert result.risk_level == 2
        assert result.risk_label == "위험"

    def test_probabilities_sum_to_one(self):
        feat = self._make_features(sugar=15, gi=65, carbs=40)
        result = _rule_based_predict(feat)
        total = sum(result.probabilities.values())
        assert abs(total - 1.0) < 1e-5


# ── SugarPredictor (fallback 모드) ──────────────────────────────────────────
class TestSugarPredictor:
    def test_predict_from_db(self, predictor_no_model):
        info = get_nutrition("donuts")
        assert info is not None
        result = predictor_no_model.predict(info, portion_g=100)
        assert result.risk_level in (0, 1, 2)
        assert result.risk_label in ("낮음", "주의", "위험")
        assert result.serving_advice

    def test_predict_from_dict(self, predictor_no_model):
        result = predictor_no_model.predict_from_dict({
            "food_name": "테스트",
            "calories": 350,
            "carbs": 55,
            "sugar": 30,
            "protein": 5,
            "fat": 12,
            "fiber": 1,
            "glycemic_index": 80,
        }, portion_g=150)
        assert result.risk_level == 2  # 고당도 → 위험

    def test_low_sugar_food(self, predictor_no_model):
        info = get_nutrition("steak")
        result = predictor_no_model.predict(info)
        assert result.risk_level == 0  # 스테이크: 당류/탄수화물 0


# ── 영양DB ────────────────────────────────────────────────────────────────────
class TestNutritionDB:
    def test_known_food(self):
        info = get_nutrition("pizza")
        assert info is not None
        assert info.sugar >= 0

    def test_unknown_food(self):
        assert get_nutrition("unknown_food_xyz") is None

    def test_all_foods_have_valid_gi(self):
        from src.nutrition.nutrition_db import NUTRITION_DB
        for key, info in NUTRITION_DB.items():
            assert 0 <= info.glycemic_index <= 100, f"{key} GI 범위 오류"
