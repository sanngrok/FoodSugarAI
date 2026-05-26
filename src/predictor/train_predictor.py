"""
XGBoost 혈당 위험도 분류기 학습 스크립트

합성 데이터(영양정보 DB 기반)로 모델을 생성하거나
실제 라벨 데이터 CSV를 받아 학습합니다.

사용법:
    # 합성 데이터로 빠른 테스트 학습
    python -m src.predictor.train_predictor --synthetic

    # 실제 CSV로 학습
    python -m src.predictor.train_predictor --data /path/to/data.csv
"""

import argparse
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from config.settings import settings
from src.nutrition.nutrition_db import NUTRITION_DB
from src.predictor.sugar_predictor import FEATURE_NAMES, _nutrition_to_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _assign_label(info) -> int:
    """
    규칙 기반으로 합성 라벨 생성 (실제 학습 데이터 없을 때 사용)
    0=낮음, 1=주의, 2=위험
    """
    score = 0
    if info.sugar > 20:
        score += 2
    elif info.sugar > 10:
        score += 1
    if info.glycemic_index > 70:
        score += 2
    elif info.glycemic_index > 55:
        score += 1
    if info.carbs > 40:
        score += 1
    return min(score // 2, 2)


def generate_synthetic_data(n_augment: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """
    영양DB + 포션 변화(±20%) + 노이즈로 합성 학습 데이터 생성
    """
    X_list, y_list = [], []
    rng = np.random.default_rng(42)

    for info in NUTRITION_DB.values():
        label = _assign_label(info)
        base = _nutrition_to_features(info, portion_g=100)

        for _ in range(n_augment):
            noise = rng.normal(1.0, 0.08, size=len(FEATURE_NAMES))
            noise[-1] = 1.0  # GI 지수는 노이즈 없이 유지
            sample = base * noise
            sample = np.clip(sample, 0, None)
            X_list.append(sample)
            y_list.append(label)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)


def load_csv_data(csv_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    CSV 컬럼: calories, carbs, sugar, protein, fat, fiber, glycemic_index, risk_label
    risk_label: "낮음" / "주의" / "위험" 또는 0 / 1 / 2
    """
    df = pd.read_csv(csv_path)
    label_map = {"낮음": 0, "주의": 1, "위험": 2}
    if df["risk_label"].dtype == object:
        df["risk_label"] = df["risk_label"].map(label_map)
    X = df[FEATURE_NAMES].values.astype(np.float32)
    y = df["risk_label"].values.astype(np.int32)
    return X, y


def train(X: np.ndarray, y: np.ndarray) -> XGBClassifier:
    sample_weights = compute_sample_weight("balanced", y)

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )

    # 5-Fold CV
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")
    logger.info("CV F1-macro: %.4f ± %.4f", scores.mean(), scores.std())

    model.fit(X, y, sample_weight=sample_weights)

    # 전체 학습 데이터 리포트
    preds = model.predict(X)
    logger.info("\n%s", classification_report(y, preds,
                target_names=settings.risk_labels))
    return model


def main(use_synthetic: bool = True, csv_path: str | None = None) -> None:
    if use_synthetic:
        logger.info("합성 데이터 생성 중...")
        X, y = generate_synthetic_data(n_augment=50)
    else:
        logger.info("CSV 데이터 로드: %s", csv_path)
        X, y = load_csv_data(csv_path)

    logger.info("학습 데이터: X=%s, y분포=%s", X.shape,
                dict(zip(*np.unique(y, return_counts=True))))

    model = train(X, y)

    save_path = settings.predictor_model_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, save_path)
    logger.info("모델 저장: %s", save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--synthetic", action="store_true", help="합성 데이터로 학습")
    group.add_argument("--data", type=str, help="실제 CSV 파일 경로")
    args = parser.parse_args()

    if args.synthetic:
        main(use_synthetic=True)
    else:
        main(use_synthetic=False, csv_path=args.data)
