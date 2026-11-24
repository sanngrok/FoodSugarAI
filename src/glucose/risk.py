"""Nutrition-based glucose risk scoring.

The score is a conservative heuristic for product guidance, not a medical
diagnosis. It intentionally uses transparent nutrition features instead of
modifying any food classifier behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.glucose.constants import GLUCOSE_REFERENCE_NOTICE
from src.nutrition.nutrition_db import NutritionInfo

# 탄수화물 80g까지는 carb_component(최대 35점)가 선형으로 오른다. 그보다 많은 탄수화물은
# excess_carb_component로 최대 15점까지 완만하게 더 오른다(80g 초과분이 80g이면 약 9.5점).
# 예전에는 80g에서 멈춰서, 300g 넘는 한 끼의 점수가 양을 늘려도 오르지 않았다.
CARB_LINEAR_MAX_G = 80.0
EXCESS_CARB_MAX_POINTS = 15.0
EXCESS_CARB_SCALE_G = 80.0
# 식이섬유/단백질/지방 완충은 양 점수(portion_component)가 다 차는 300g까지만 양에 비례한다.
# 그 이상에서도 완충이 계속 커지면 양을 늘릴수록 점수가 내려가는 문제가 있었다.
BUFFERING_PORTION_CAP_G = 300.0


@dataclass(frozen=True)
class GlucoseRiskScore:
    score: float
    level: str
    factors: dict[str, float]
    reference_notice: str = GLUCOSE_REFERENCE_NOTICE


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def score_glucose_risk(nutrition: NutritionInfo, portion_g: float = 100.0) -> GlucoseRiskScore:
    """Return a 0-100 glucose-risk score from nutrition values.

    Inputs are assumed to be per 100 g. Portion-sensitive nutrients are scaled
    by ``portion_g`` while glycemic index is left unchanged.
    """
    scale = max(portion_g, 0.0) / 100.0
    carbs = max(nutrition.carbs * scale, 0.0)
    sugar = max(nutrition.sugar * scale, 0.0)
    fiber = max(nutrition.fiber * scale, 0.0)
    protein = max(nutrition.protein * scale, 0.0)
    fat = max(nutrition.fat * scale, 0.0)
    gi = _clamp(nutrition.glycemic_index, 0.0, 100.0)

    carb_component = min(carbs / CARB_LINEAR_MAX_G, 1.0) * 35.0
    excess_carbs = max(carbs - CARB_LINEAR_MAX_G, 0.0)
    excess_carb_component = EXCESS_CARB_MAX_POINTS * (1.0 - math.exp(-excess_carbs / EXCESS_CARB_SCALE_G))
    sugar_component = min(sugar / 35.0, 1.0) * 25.0
    gi_component = gi / 100.0 * 30.0
    portion_component = min(max(portion_g - 100.0, 0.0) / 200.0, 1.0) * 10.0

    # Fiber, protein, and fat can slow glucose absorption. Keep the adjustment
    # modest because this is a general-purpose reference score.
    buffer_scale = min(max(portion_g, 0.0), BUFFERING_PORTION_CAP_G) / 100.0
    buffer_fiber = max(nutrition.fiber * buffer_scale, 0.0)
    buffer_protein = max(nutrition.protein * buffer_scale, 0.0)
    buffer_fat = max(nutrition.fat * buffer_scale, 0.0)
    buffering = min(buffer_fiber / 10.0, 1.0) * 8.0
    buffering += min(buffer_protein / 30.0, 1.0) * 4.0
    buffering += min(buffer_fat / 35.0, 1.0) * 3.0

    score = _clamp(
        carb_component + excess_carb_component + sugar_component + gi_component + portion_component - buffering
    )
    if score < 35:
        level = "낮음"
    elif score < 65:
        level = "주의"
    else:
        level = "높음"

    return GlucoseRiskScore(
        score=round(score, 2),
        level=level,
        factors={
            "scaled_carbs_g": round(carbs, 3),
            "scaled_sugar_g": round(sugar, 3),
            "scaled_fiber_g": round(fiber, 3),
            "scaled_protein_g": round(protein, 3),
            "scaled_fat_g": round(fat, 3),
            "glycemic_index": round(gi, 3),
            "portion_g": round(portion_g, 3),
            "carb_component": round(carb_component, 3),
            "excess_carb_component": round(excess_carb_component, 3),
            "sugar_component": round(sugar_component, 3),
            "gi_component": round(gi_component, 3),
            "portion_component": round(portion_component, 3),
            "buffering_component": round(buffering, 3),
        },
    )
