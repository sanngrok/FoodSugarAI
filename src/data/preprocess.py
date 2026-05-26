"""
식품영양성분 데이터 전처리 파이프라인

단계:
  1. 결측치 처리
  2. 단위 통일 및 텍스트 정규화
  3. 이상치 제거
  4. 중복 제거
  5. 인코딩 및 스케일링

사용법:
    python -m src.data.preprocess
    python -m src.data.preprocess --input data/processed/foodsafety_raw.csv \
                                  --output-dir data/processed
"""

import argparse
import logging
import re
import unicodedata
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NUMERIC_COLS = ["calories", "protein", "fat", "carbs", "sugar", "fiber"]

# 이상치 제거 기준 (100g 기준 생리적 상한선)
OUTLIER_HARD_LIMITS = {
    "calories": (1, 999),   # API 최대값 999 kcal
    "protein":  (0, 100),   # 100g당 단백질 100g 초과는 물리적으로 불가
    "fat":      (0, 100),
    "carbs":    (0, 100),
    "sugar":    (0, 100),
    "fiber":    (0, 90),
}

# 거시영양소-칼로리 불일치 허용 배율 (macro_cal / reported_calories)
# 식이섬유·알코올·당알코올 등으로 약간 차이 있어 3배까지 허용
MACRO_CAL_RATIO_MAX = 3.0


# ──────────────────────────────────────────────────────────────────────────────
# 1. 결측치 처리
# ──────────────────────────────────────────────────────────────────────────────

def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # 수치형: 음수 → 0 으로 대체 (결측과 동일 처리)
    for col in NUMERIC_COLS:
        neg = (df[col] < 0).sum()
        if neg:
            logger.info("  [결측] %s 음수 %d건 → 0 대체", col, neg)
        df[col] = df[col].clip(lower=0)

    # food_name 빈 문자열 → 행 삭제
    df = df[df["food_name"].str.strip().astype(bool)].copy()

    # origin 빈 값 → "미분류" 대체
    df["origin"] = df["origin"].fillna("미분류").replace("", "미분류")

    logger.info("[결측치 처리] %d → %d행 (-%d)", before, len(df), before - len(df))
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 2. 단위 통일 및 텍스트 정규화
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """food_name 정규화: 유니코드 정규화, 연속 공백 제거, 앞뒤 공백 제거"""
    name = unicodedata.normalize("NFC", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _normalize_origin(origin: str) -> str:
    """origin 오타·변형 통일"""
    origin = str(origin).strip()
    mapping = {
        "가공식품(분석함량)": "가공식품",
        "가공식품(업체제공)": "가공식품",
        "외식(프랜차이즈 등 업체 제공 영양정보)": "외식_업체제공",
        "외식(재료량 기반 산출 함량)": "외식_산출",
        "외식(분석 함량)": "외식_분석",
        "가정식(분석 함량)": "가정식",
        "산업체급식(재료량 기반 산출 함량)": "산업체급식",
        "초등학교급식(재료량 기반 산출 함량)": "초등급식",
        "중고등학교급식(재료량 기반 산출 함량)": "중고등급식",
        "유치원급식(재료량 기반 산출 함량)": "유치원급식",
        "어린이집급식(재료량 기반 산출 함량)": "어린이집급식",
    }
    return mapping.get(origin, origin)


def normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    df["food_name"] = df["food_name"].map(_normalize_name)
    df["origin"] = df["origin"].map(_normalize_origin)

    # 수치형 소수점 2자리 통일
    for col in NUMERIC_COLS:
        df[col] = df[col].round(2)

    # serving_g: 100g 단위 정수로 유지 (fetch 단계에서 이미 처리됐으나 재확인)
    df["serving_g"] = df["serving_g"].clip(lower=1).astype(int)

    logger.info("[텍스트 정규화] food_name / origin 정규화 완료")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 3. 이상치 제거
# ──────────────────────────────────────────────────────────────────────────────

def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    mask = pd.Series(True, index=df.index)

    # 3-a. 절대 상한/하한 적용
    for col, (lo, hi) in OUTLIER_HARD_LIMITS.items():
        out = ~df[col].between(lo, hi)
        if out.sum():
            logger.info("  [이상치] %s 범위[%s~%s] 초과 %d건 제거", col, lo, hi, out.sum())
        mask &= ~out

    df = df[mask].copy()

    # 3-b. 거시영양소-칼로리 불일치 제거
    #      단백질·지방·탄수화물로 계산한 칼로리가 신고 칼로리의 3배 이상이면
    #      단위 오류(1회 제공량 기준 값을 100g 칼럼에 입력한 경우) 로 판단
    df["_macro_cal"] = df["protein"] * 4 + df["fat"] * 9 + df["carbs"] * 4
    ratio = df["_macro_cal"] / (df["calories"] + 1)
    bad_ratio = ratio > MACRO_CAL_RATIO_MAX
    if bad_ratio.sum():
        logger.info("  [이상치] macro/칼로리 비율>%.1f 건수: %d건 제거",
                    MACRO_CAL_RATIO_MAX, bad_ratio.sum())
    df = df[~bad_ratio].drop(columns=["_macro_cal"])

    logger.info("[이상치 제거] %d → %d행 (-%d)", before, len(df), before - len(df))
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 4. 중복 제거
# ──────────────────────────────────────────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # 모든 수치 컬럼이 완전히 동일한 중복 행 제거
    exact_dup = df.duplicated(subset=["food_name"] + NUMERIC_COLS, keep="first")
    df = df[~exact_dup].copy()
    logger.info("  [중복] 완전 중복 %d건 제거", exact_dup.sum())

    # food_name이 같고 수치가 다른 경우 → 수치 평균으로 통합
    dup_names = df[df.duplicated("food_name", keep=False)]["food_name"].unique()
    if len(dup_names):
        agg_dict = {col: "mean" for col in NUMERIC_COLS}
        agg_dict["serving_g"] = "first"
        agg_dict["origin"] = "first"
        non_dup = df[~df["food_name"].isin(dup_names)]
        dup_df  = (df[df["food_name"].isin(dup_names)]
                   .groupby("food_name", as_index=False)
                   .agg(agg_dict))
        for col in NUMERIC_COLS:
            dup_df[col] = dup_df[col].round(2)
        df = pd.concat([non_dup, dup_df], ignore_index=True)
        logger.info("  [중복] food_name 중복 %d종 → 수치 평균으로 통합", len(dup_names))

    logger.info("[중복 제거] %d → %d행 (-%d)", before, len(df), before - len(df))
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 5. 인코딩 및 스케일링
# ──────────────────────────────────────────────────────────────────────────────

def encode_and_scale(
    df: pd.DataFrame,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
        clean_df  : 정제된 원본 (스케일링 없음, 인코딩만 추가)
        scaled_df : StandardScaler 적용본
    """
    # ── 5-a. origin 레이블 인코딩 ─────────────────────────────────────────────
    le = LabelEncoder()
    df["origin_encoded"] = le.fit_transform(df["origin"])
    le_path = output_dir / "label_encoder_origin.pkl"
    joblib.dump(le, le_path)
    logger.info("  [인코딩] origin LabelEncoder 저장: %s (%d클래스)", le_path, len(le.classes_))

    clean_df = df.copy()

    # ── 5-b. StandardScaler ───────────────────────────────────────────────────
    scaler_std = StandardScaler()
    scaled_values = scaler_std.fit_transform(df[NUMERIC_COLS])
    std_path = output_dir / "scaler_standard.pkl"
    joblib.dump(scaler_std, std_path)
    logger.info("  [스케일링] StandardScaler 저장: %s", std_path)

    scaled_df = df.copy()
    scaled_df[NUMERIC_COLS] = np.round(scaled_values, 6)

    # ── 5-c. MinMaxScaler (참고용 저장) ──────────────────────────────────────
    scaler_mm = MinMaxScaler()
    scaler_mm.fit(df[NUMERIC_COLS])
    mm_path = output_dir / "scaler_minmax.pkl"
    joblib.dump(scaler_mm, mm_path)
    logger.info("  [스케일링] MinMaxScaler 저장: %s", mm_path)

    return clean_df, scaled_df


# ──────────────────────────────────────────────────────────────────────────────
# 메인 파이프라인
# ──────────────────────────────────────────────────────────────────────────────

def run(input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir = Path("data/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== 전처리 시작: %s ===", input_path)
    df = pd.read_csv(input_path)
    logger.info("원본 데이터: %d행 × %d열", *df.shape)

    df = handle_missing(df)
    df = normalize_text(df)
    df = remove_outliers(df)
    df = remove_duplicates(df)

    clean_df, scaled_df = encode_and_scale(df, model_dir)

    # 저장
    clean_path  = output_dir / "foodsafety_clean.csv"
    scaled_path = output_dir / "foodsafety_scaled.csv"
    clean_df.to_csv(clean_path,  index=False, encoding="utf-8-sig")
    scaled_df.to_csv(scaled_path, index=False, encoding="utf-8-sig")

    logger.info("=== 전처리 완료 ===")
    logger.info("  정제본  : %s (%d행)", clean_path,  len(clean_df))
    logger.info("  스케일본: %s (%d행)", scaled_path, len(scaled_df))

    # 요약 통계 출력
    logger.info("\n[최종 수치 통계]\n%s", clean_df[NUMERIC_COLS].describe().round(2).to_string())
    logger.info("\n[origin 분포]\n%s", clean_df["origin"].value_counts().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",      default="data/processed/foodsafety_raw.csv")
    parser.add_argument("--output-dir", default="data/processed")
    args = parser.parse_args()
    run(Path(args.input), Path(args.output_dir))
