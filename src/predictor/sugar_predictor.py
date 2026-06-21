"""
XGBoost 기반 혈당 위험도 예측기

입력 피처: 영양정보 (칼로리, 탄수화물, 당류, 단백질, 지방, 식이섬유, GI지수)
출력:  0=낮음, 1=주의, 2=높음
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

from config.settings import settings
from src.nutrition.nutrition_db import NutritionInfo

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "calories",
    "carbs",
    "sugar",
    "protein",
    "fat",
    "fiber",
    "glycemic_index",
]

RISK_LABELS = settings.risk_labels          # ["낮음", "주의", "높음"]
RISK_COLORS = ["#2ecc71", "#f39c12", "#e74c3c"]
RISK_EMOJIS = ["✅", "⚠️", "🚨"]


@dataclass
class PredictionResult:
    risk_level: int            # 0 / 1 / 2
    risk_label: str            # "낮음" / "주의" / "높음"
    risk_color: str
    risk_emoji: str
    probabilities: dict[str, float]   # {"낮음": 0.1, "주의": 0.3, "높음": 0.6}
    feature_importance: dict[str, float] | None = None
    serving_advice: str = ""


def _nutrition_to_features(info: NutritionInfo, portion_g: float = 100) -> list[float]:
    """NutritionInfo → numpy feature vector (portion_g 스케일 적용)"""
    scale = portion_g / 100.0
    return [
        info.calories * scale,
        info.carbs * scale,
        info.sugar * scale,
        info.protein * scale,
        info.fat * scale,
        info.fiber * scale,
        info.glycemic_index,          # GI는 스케일 무관
    ]


def _rule_based_predict(features: list[float]) -> PredictionResult:
    """
    학습된 모델이 없을 때 사용하는 규칙 기반 fallback.
    sugar, GI, carbs를 기준으로 위험도 계산.
    """
    sugar = features[FEATURE_NAMES.index("sugar")]
    gi = features[FEATURE_NAMES.index("glycemic_index")]
    carbs = features[FEATURE_NAMES.index("carbs")]

    score = 0
    if sugar > 20:
        score += 2
    elif sugar > 10:
        score += 1

    if gi > 70:
        score += 2
    elif gi > 55:
        score += 1

    if carbs > 40:
        score += 1

    level = min(score // 2, 2)
    probs = [0.0, 0.0, 0.0]
    probs[level] = 0.7
    if level > 0:
        probs[level - 1] = 0.2
    if level < 2:
        probs[level + 1] = 0.1
    # normalize
    total = sum(probs)
    probs = [p / total for p in probs]

    return _build_result(level, probs)


def _build_result(level: int, probs: list[float],
                  importances: dict | None = None) -> PredictionResult:
    prob_dict = {RISK_LABELS[i]: round(probs[i], 4) for i in range(3)}
    advice = _serving_advice(level, prob_dict)
    return PredictionResult(
        risk_level=level,
        risk_label=RISK_LABELS[level],
        risk_color=RISK_COLORS[level],
        risk_emoji=RISK_EMOJIS[level],
        probabilities=prob_dict,
        feature_importance=importances,
        serving_advice=advice,
    )


def _serving_advice(level: int, probs: dict) -> str:
    if level == 0:
        return "혈당 상승 가능성이 낮은 편입니다. 실제 반응은 개인과 섭취량에 따라 달라질 수 있습니다."
    if level == 1:
        return ("혈당 상승 가능성 신호가 보통 수준입니다. 섭취량과 함께 먹는 음식 구성을 참고해 확인하세요.")
    return ("혈당 상승 가능성 신호가 높은 편입니다. 단일 판단이 아니라 실제 측정값과 함께 참고하세요.")


class SugarPredictor:
    """XGBoost 혈당 위험도 예측 래퍼"""

    def __init__(self, model_path: Path | None = None, use_model: bool = True):
        self.model = None
        if not use_model:
            logger.warning("XGBoost 모델 로드를 비활성화했습니다. 규칙 기반 fallback을 사용합니다.")
            return
        model_path = model_path or settings.predictor_model_path
        if model_path.exists():
            self._load(model_path)
        else:
            logger.warning(
                "XGBoost 모델 파일(%s)이 없습니다. 규칙 기반 fallback을 사용합니다.",
                model_path,
            )

    def _load(self, path: Path) -> None:
        self.model = joblib.load(path)
        logger.info("XGBoost 모델 로드 완료: %s", path)

    def predict(
        self,
        nutrition: NutritionInfo,
        portion_g: float = 100,
    ) -> PredictionResult:
        """NutritionInfo + 섭취량(g) → PredictionResult"""
        features = _nutrition_to_features(nutrition, portion_g)

        if self.model is None:
            return _rule_based_predict(features)

        if np is None:
            raise ImportError("numpy가 설치되어 있지 않아 XGBoost 모델 추론을 사용할 수 없습니다.")
        x = np.array(features, dtype=np.float32).reshape(1, -1)
        level = int(self.model.predict(x)[0])
        probs = self.model.predict_proba(x)[0].tolist()

        importances = None
        if hasattr(self.model, "feature_importances_"):
            importances = dict(zip(FEATURE_NAMES, self.model.feature_importances_.tolist()))

        return _build_result(level, probs, importances)

    def predict_from_dict(
        self,
        nutrition_dict: dict,
        portion_g: float = 100,
    ) -> PredictionResult:
        """
        dict 형태 영양정보 직접 입력 지원
        예: {"calories": 250, "carbs": 35, "sugar": 15, ...}
        """
        from src.nutrition.nutrition_db import NutritionInfo as NI
        info = NI(
            food_name=nutrition_dict.get("food_name", "Unknown"),
            calories=float(nutrition_dict.get("calories", 0)),
            carbs=float(nutrition_dict.get("carbs", 0)),
            sugar=float(nutrition_dict.get("sugar", 0)),
            protein=float(nutrition_dict.get("protein", 0)),
            fat=float(nutrition_dict.get("fat", 0)),
            fiber=float(nutrition_dict.get("fiber", 0)),
            glycemic_index=float(nutrition_dict.get("glycemic_index", 50)),
        )
        return self.predict(info, portion_g)
