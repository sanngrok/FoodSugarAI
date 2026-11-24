"""
FoodSugar AI — FastAPI 애플리케이션 진입점

실행:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, predict
from config.settings import settings
from src.predictor.sugar_predictor import SugarPredictor
from src.classifier.ensemble_food_classifier import EnsembleFoodClassifier
from src.classifier.food_classifier import FoodClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_classifier():
    """Load the configured production classifier.

    The K-Food 92% ensemble is preferred when its config exists. Falling back to
    FoodClassifier keeps local/dev environments usable when model artifacts have
    not been downloaded yet.
    """
    classifier_mode = settings.classifier_mode.strip().lower()
    if classifier_mode == "none":
        logger.info("분류기 로드를 비활성화했습니다: CLASSIFIER_MODE=none")
        return None
    if classifier_mode == "single":
        logger.info("단일 FoodClassifier 사용: %s", settings.classifier_model_path)
        return FoodClassifier(model_path=settings.classifier_model_path)
    ensemble_config = settings.classifier_ensemble_config_path
    if ensemble_config and ensemble_config.exists():
        logger.info("운영 ensemble config 사용: %s", ensemble_config)
        return EnsembleFoodClassifier(ensemble_config)
    logger.info("단일 FoodClassifier 사용")
    return FoodClassifier()


@asynccontextmanager
async def lifespan(application: FastAPI):
    # startup — production defaults to the rule-based sugar predictor because
    # eager xgboost loading can conflict with torch/MPS ensemble inference on macOS.
    logger.info("모델 로딩 시작...")
    application.state.predictor = SugarPredictor(use_model=settings.use_xgboost_predictor_model)
    application.state.classifier_error = None
    try:
        application.state.classifier = load_classifier()
    except Exception as e:
        logger.exception("분류기 로드 실패: %s", e)
        application.state.classifier = None
        application.state.classifier_error = str(e)
    # CGM 예측 모델도 시작 시 한 번 로드해 본다. 실패해도 서버는 계속 뜨고,
    # 원인은 /health 의 cgm_forecast_error 로 확인할 수 있다.
    application.state.cgm_forecast_ready, application.state.cgm_forecast_error = (
        predict.check_cgm_forecast_readiness()
    )
    if application.state.cgm_forecast_error:
        logger.warning("CGM 예측 모델 준비 안 됨: %s", application.state.cgm_forecast_error)
    logger.info("모델 로딩 완료")

    yield  # 서버 실행 중

    # shutdown
    logger.info("서버 종료")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "음식 이미지를 EfficientNet-B0으로 분류하고, "
        "영양정보 기반으로 혈당 부담 참고 수준(낮음/주의/높음)을 예측합니다."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(predict.router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
