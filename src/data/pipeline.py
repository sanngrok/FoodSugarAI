"""
식품안전나라 API → 수집 → 라벨링 → XGBoost 학습 통합 파이프라인

사용법:
    python -m src.data.pipeline --api-key YOUR_KEY --total 10000
"""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW_PATH   = Path("data/processed/foodsafety_raw.csv")
TRAIN_PATH = Path("data/processed/train_data.csv")


def run(api_key: str, total: int, skip_fetch: bool = False) -> None:
    # ── 1단계: 수집 ──────────────────────────────────────────────────────────
    if skip_fetch and RAW_PATH.exists():
        logger.info("수집 단계 스킵 (--skip-fetch). 기존 파일 사용: %s", RAW_PATH)
    else:
        from src.data.fetch_foodsafety import main as fetch_main
        fetch_main(api_key=api_key, total=total, out_path=RAW_PATH)

    # ── 2단계: 라벨링 ────────────────────────────────────────────────────────
    from src.data.label_risk import process
    df = process(input_path=RAW_PATH, output_path=TRAIN_PATH)

    # ── 3단계: XGBoost 학습 ──────────────────────────────────────────────────
    import numpy as np
    from src.predictor.train_predictor import load_csv_data, train
    import joblib
    from config.settings import settings

    logger.info("XGBoost 학습 시작...")
    X, y = load_csv_data(str(TRAIN_PATH))
    logger.info("학습 데이터: %d건, 피처: %d개", len(X), X.shape[1])

    model = train(X, y)

    save_path = settings.predictor_model_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, save_path)
    logger.info("모델 저장 완료: %s", save_path)
    logger.info("파이프라인 완료!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="식품안전나라 → XGBoost 학습 파이프라인")
    parser.add_argument("--api-key", default=os.getenv("FOODSAFETY_API_KEY", ""))
    parser.add_argument("--total", type=int, default=10000, help="수집 건수 (기본 10,000)")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="이미 수집된 CSV가 있으면 API 호출 생략")
    args = parser.parse_args()

    if not args.skip_fetch and not args.api_key:
        raise SystemExit(
            "API 키가 없습니다.\n"
            "  방법 1) .env 파일에 FOODSAFETY_API_KEY=발급키 추가\n"
            "  방법 2) --api-key 옵션으로 직접 전달"
        )

    run(args.api_key, args.total, args.skip_fetch)
