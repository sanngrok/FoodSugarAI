"""
수집한 식품안전나라 데이터 → 혈당 위험도 라벨 부여 → 학습용 CSV 생성

GI(혈당지수) 데이터가 API에 없으므로:
  1. 식품군(group) 기반 GI 추정
  2. 당류·탄수화물 비율로 보정

사용법:
    python -m src.data.label_risk \
        --input  data/processed/foodsafety_raw.csv \
        --output data/processed/train_data.csv
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 식품군 → 평균 GI 추정표 (NUTRITION_DB와 동일 기준)
GROUP_GI_MAP = {
    # 곡류/빵류
    "곡류": 68, "빵류": 72, "면류": 58, "떡류": 75,
    # 당류/과자
    "당류": 80, "과자류": 74, "음료류": 65, "빙과류": 60,
    # 채소/과일
    "채소류": 38, "과일류": 52, "버섯류": 25, "해조류": 20,
    # 단백질
    "육류": 10, "어류": 10, "난류": 5, "두류": 30,
    "유류": 35, "유제품류": 35,
    # 기타
    "조미료류": 40, "유지류": 5, "기타": 50,
}
DEFAULT_GI = 50


def estimate_gi(row: pd.Series) -> float:
    """식품군 + 당류 비율로 GI 추정"""
    group = str(row.get("group", ""))
    gi_base = DEFAULT_GI
    for key, val in GROUP_GI_MAP.items():
        if key in group:
            gi_base = val
            break

    # 당류 비율이 높으면 GI 보정
    calories = row.get("calories", 0)
    sugar = row.get("sugar", 0)
    carbs = row.get("carbs", 0)

    if carbs > 0:
        sugar_ratio = sugar / carbs
        if sugar_ratio > 0.5:
            gi_base = min(gi_base + 15, 100)
        elif sugar_ratio > 0.3:
            gi_base = min(gi_base + 8, 100)

    return float(gi_base)


def assign_risk_label(row: pd.Series) -> int:
    """
    혈당 위험도 라벨 (0=낮음, 1=주의, 2=위험)
    근거: 당류·GI·탄수화물 3가지 기준 점수화
    """
    score = 0
    sugar = row.get("sugar", 0)
    gi = row.get("glycemic_index", 50)
    carbs = row.get("carbs", 0)
    fiber = row.get("fiber", 0)

    # 당류 점수
    if sugar > 20:
        score += 2
    elif sugar > 10:
        score += 1

    # GI 점수
    if gi > 70:
        score += 2
    elif gi > 55:
        score += 1

    # 탄수화물 점수
    if carbs > 40:
        score += 1

    # 식이섬유는 완충 효과 (GI 낮춤)
    if fiber > 5:
        score = max(score - 1, 0)

    return min(score // 2, 2)


def process(input_path: Path, output_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    logger.info("입력 데이터: %d행", len(df))

    # GI 추정
    df["glycemic_index"] = df.apply(estimate_gi, axis=1)

    # 위험도 라벨 부여
    df["risk_label"] = df.apply(assign_risk_label, axis=1)

    # 학습에 필요한 컬럼만 유지
    keep = ["food_name", "calories", "carbs", "sugar",
            "protein", "fat", "fiber", "glycemic_index", "risk_label"]
    df = df[[c for c in keep if c in df.columns]]

    # 라벨 분포 출력
    dist = df["risk_label"].value_counts().sort_index()
    label_names = {0: "낮음", 1: "주의", 2: "위험"}
    logger.info("라벨 분포:")
    for idx, cnt in dist.items():
        pct = cnt / len(df) * 100
        logger.info("  %s: %d건 (%.1f%%)", label_names.get(idx, idx), cnt, pct)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info("저장 완료: %s", output_path)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="data/processed/foodsafety_raw.csv")
    parser.add_argument("--output", default="data/processed/train_data.csv")
    args = parser.parse_args()
    process(Path(args.input), Path(args.output))
