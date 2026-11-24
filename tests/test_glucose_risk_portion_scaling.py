"""혈당 부담 점수가 300g을 넘는 큰 한 끼에서도 양에 따라 계속 오르는지 확인한다."""

import pytest

from src.glucose.risk import score_glucose_risk
from src.nutrition.nutrition_db import NutritionInfo

# kfood_nutrition_db.json의 비빔밥 100g 값 (GI는 nutrition_db의 proxy 68)
BIBIMBAP = NutritionInfo(
    food_name="비빔밥", calories=171.1, carbs=29.74, sugar=1.98, protein=4.63, fat=3.7, fiber=0.96, glycemic_index=68.0
)
# 식이섬유/단백질/지방이 많아 예전 공식에서 큰 양일수록 점수가 내려가던 형태
HIGH_BUFFER_MEAL = NutritionInfo(
    food_name="테스트", calories=200, carbs=25, sugar=3, protein=12, fat=9, fiber=6, glycemic_index=55
)


@pytest.mark.parametrize("info", [BIBIMBAP, HIGH_BUFFER_MEAL])
def test_score_never_decreases_above_300g(info):
    scores = [score_glucose_risk(info, portion).score for portion in range(300, 1001, 10)]

    assert all(later >= earlier for earlier, later in zip(scores, scores[1:]))


def test_large_bibimbap_keeps_rising_and_reaches_high():
    score_300 = score_glucose_risk(BIBIMBAP, 300)
    score_450 = score_glucose_risk(BIBIMBAP, 450)
    score_600 = score_glucose_risk(BIBIMBAP, 600)

    assert score_300.score < score_450.score < score_600.score
    assert score_450.level == "높음"
    assert score_450.factors["excess_carb_component"] > 0


def test_meals_up_to_80g_carbs_score_as_before():
    # 탄수화물 80g, 300g 이하에서는 예전 공식과 같은 값이어야 한다 (README 예시 41.98).
    result = score_glucose_risk(BIBIMBAP, 150)

    assert result.score == 41.98
    assert result.factors["excess_carb_component"] == 0.0
