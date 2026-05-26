"""
공공데이터포털(data.go.kr) 식품영양성분DB API → 영양정보 수집 스크립트
서비스: 식품의약품안전처_식품영양성분 DB 정보

사용법:
    python -m src.data.fetch_foodsafety

    # 또는 직접 키 지정
    python -m src.data.fetch_foodsafety --api-key YOUR_KEY --total 5000
"""

import argparse
import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = (
    "http://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02"
    "/getFoodNtrCpntDbInq02"
)

# 응답 필드 → 컬럼명 매핑
FIELD_MAP = {
    "FOOD_NM_KR":   "food_name",   # 식품명
    "AMT_NUM1":     "calories",    # 에너지(kcal)
    "AMT_NUM3":     "protein",     # 단백질(g)
    "AMT_NUM4":     "fat",         # 지방(g)
    "AMT_NUM6":     "carbs",       # 탄수화물(g)
    "AMT_NUM7":     "sugar",       # 총당류(g)
    "AMT_NUM8":     "fiber",       # 총식이섬유(g)
    "SERVING_SIZE": "serving_g",   # 1회 제공량(g)
    "FOOD_OR_NM":   "origin",      # 원산지
    "GROUP_NM":     "group",       # 식품군
}

PAGE_SIZE = 500  # 1회 최대 요청 건수 (FoodNtrCpntDbInfo02 API 상한)


def fetch_batch(api_key: str, page_no: int) -> list[dict] | None:
    params = {
        "serviceKey": api_key,
        "pageNo":     page_no,
        "numOfRows":  PAGE_SIZE,
        "type":       "json",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("요청 실패 (page %d): %s", page_no, e)
        return []

    # 응답 구조 파싱
    body = data.get("body", {})
    items = body.get("items", [])
    total_count = body.get("totalCount", 0)

    if page_no == 1:
        logger.info("전체 데이터 수: %d건", total_count)

    if not items:
        logger.info("page %d 데이터 없음 — 수집 완료", page_no)
        return None  # 종료 신호

    logger.info("  page %d 수신: %d건", page_no, len(items))
    return items


def fetch_all(api_key: str, total: int = 5000) -> pd.DataFrame:
    all_rows = []
    page_no = 1
    while len(all_rows) < total:
        batch = fetch_batch(api_key, page_no)
        if batch is None:
            break
        all_rows.extend(batch)
        if len(batch) < PAGE_SIZE:  # 마지막 페이지
            break
        page_no += 1
        time.sleep(0.3)

    if not all_rows:
        raise RuntimeError("수집된 데이터가 없습니다. API 키와 서비스 승인 상태를 확인하세요.")

    df = pd.DataFrame(all_rows[:total])
    existing = {k: v for k, v in FIELD_MAP.items() if k in df.columns}
    df = df[list(existing.keys())].rename(columns=existing)
    logger.info("총 %d건 수집 완료", len(df))
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = ["calories", "carbs", "sugar", "protein", "fat", "fiber"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df = df[df["calories"] > 0].reset_index(drop=True)

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    # 100g 기준 정규화 — SERVING_SIZE가 "100g" 형식일 수 있으므로 숫자만 추출
    if "serving_g" in df.columns:
        df["serving_g"] = (
            df["serving_g"].astype(str)
            .str.extract(r"([\d.]+)", expand=False)
        )
        df["serving_g"] = pd.to_numeric(df["serving_g"], errors="coerce").fillna(100.0)
        df["serving_g"] = df["serving_g"].replace(0, 100.0)
        ratio = 100.0 / df["serving_g"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = (df[col] * ratio).round(2)

    logger.info("정제 후 %d건", len(df))
    return df


def main(api_key: str, total: int, out_path: Path) -> None:
    logger.info("공공데이터포털 식품영양성분 API 수집 시작 (목표: %d건)", total)
    df = fetch_all(api_key, total)
    df = clean(df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info("저장 완료: %s (%d건)", out_path, len(df))
    print(df.head(5).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.getenv("FOODSAFETY_API_KEY", ""))
    parser.add_argument("--total", type=int, default=5000)
    parser.add_argument("--out", default="data/processed/foodsafety_raw.csv")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit(
            "API 키가 없습니다.\n"
            "  방법 1) .env 파일에 FOODSAFETY_API_KEY=발급키 추가\n"
            "  방법 2) --api-key 옵션으로 직접 전달"
        )

    main(args.api_key, args.total, Path(args.out))
