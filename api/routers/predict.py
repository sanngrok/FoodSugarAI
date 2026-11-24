import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from PIL import Image, ImageStat

from api.schemas.models import (
    CGMEnrichedForecastRequest,
    CGMEnrichedForecastResponse,
    CGMEnrichedFeatures,
    CGMForecastEnrichedEventsRequest,
    CGMForecastEnrichedEventsResponse,
    CGMForecastRequest,
    CGMForecastResponse,
    ClassificationResponse,
    FullAnalysisResponse,
    GlucoseRiskResponse,
    NutritionInput,
    RiskResponse,
)
from config.settings import settings
from src.classifier.food_classifier import ClassificationResult
from src.glucose.constants import GLUCOSE_REFERENCE_NOTICE, GLUCOSE_RISK_INTERPRETATION, GLUCOSE_SAFETY_WARNING
try:
    from src.glucose.forecasting import (
        ENRICHED_FEATURE_COLUMNS,
        build_enriched_features_from_raw_events,
        forecast_from_enriched_payload,
        forecast_from_recent_readings,
        load_event_classifiers_cached,
        load_event_thresholds_cached,
        load_forecast_metadata_cached,
        load_forecast_models_cached,
        load_prediction_intervals_cached,
        load_range_calibrators_cached,
    )
    _CGM_FORECASTING_AVAILABLE = True
    _CGM_FORECASTING_IMPORT_ERROR = ""
except ImportError as exc:
    ENRICHED_FEATURE_COLUMNS = []
    _CGM_FORECASTING_AVAILABLE = False
    _CGM_FORECASTING_IMPORT_ERROR = str(exc)
from src.glucose.risk import score_glucose_risk
from src.nutrition.nutrition_db import NUTRITION_DB, get_nutrition
from src.nutrition.nutrition_db import NutritionInfo
from src.utils.image_utils import load_image, validate_image

router = APIRouter(prefix="/predict", tags=["Predict"])
logger = logging.getLogger(__name__)


# ── torch 없을 때 이미지 색상으로 음식을 추정하는 fallback ────────────────────────
_COLOR_MAP = {
    # (hue_center, hue_range) → 유력 후보 음식 키 리스트
    "red_orange": ["pizza", "tomato", "nachos", "churros", "apple_pie"],
    "yellow":     ["french_fries", "waffles", "macarons", "omelette", "pancakes"],
    "brown":      ["steak", "hamburger", "chocolate_cake", "donuts", "fried_rice"],
    "green":      ["greek_salad", "seaweed_salad", "edamame", "guacamole", "caesar_salad"],
    "white_beige":["sushi", "ramen", "miso_soup", "rice", "pho"],
    "orange":     ["carrot_cake", "salmon", "grilled_salmon", "lobster_bisque", "tiramisu"],
}


def _color_based_fallback(image: Image.Image) -> ClassificationResult:
    """
    평균 색상(HSV)으로 음식 카테고리를 추정해 DB에서 후보를 선택.
    torch 미설치 환경 전용 fallback.
    """
    import colorsys

    img_small = image.convert("RGB").resize((64, 64))
    r, g, b = [channel / 255.0 for channel in ImageStat.Stat(img_small).mean[:3]]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue_deg = h * 360

    if s < 0.15:
        candidates = _COLOR_MAP["white_beige"]
    elif 0 <= hue_deg < 30 or hue_deg >= 330:
        candidates = _COLOR_MAP["red_orange"]
    elif 30 <= hue_deg < 60:
        candidates = _COLOR_MAP["yellow"]
    elif 60 <= hue_deg < 150:
        candidates = _COLOR_MAP["green"]
    elif 150 <= hue_deg < 250:
        candidates = _COLOR_MAP["white_beige"]
    else:
        candidates = _COLOR_MAP["brown"]

    # brightness 기반 보정: 어두운 이미지 → 구운/볶은 음식
    if v < 0.35:
        candidates = _COLOR_MAP["brown"]

    # 후보 중 DB에 있는 것만 필터
    valid = [c for c in candidates if c in NUTRITION_DB]
    if not valid:
        valid = ["pizza"]

    food_key = valid[0]
    info = get_nutrition(food_key)
    food_name_ko = info.food_name if info else food_key.replace("_", " ").title()

    # 가짜 top5 (confidence 낮게 설정 — 실제 모델 아님을 표시)
    top5 = [(k, round(1.0 / len(valid) * (0.5 if i > 0 else 1.0), 3))
            for i, k in enumerate(valid[:5])]

    logger.warning("EfficientNet 미사용 — 색상 기반 fallback: %s", food_key)

    return ClassificationResult(
        food_key=food_key,
        food_name_ko=f"{food_name_ko} (색상 추정)",
        confidence=top5[0][1],
        top5=top5,
    )


def _clf_result_to_response(result) -> ClassificationResponse:
    return ClassificationResponse(
        food_key=result.food_key,
        food_name_ko=result.food_name_ko,
        confidence=round(result.confidence, 4),
        top5=[(k, round(v, 4)) for k, v in result.top5],
    )


def _risk_result_to_response(result) -> RiskResponse:
    return RiskResponse(
        risk_level=result.risk_level,
        risk_label=result.risk_label,
        risk_color=result.risk_color,
        risk_emoji=result.risk_emoji,
        probabilities=result.probabilities,
        feature_importance=result.feature_importance,
        serving_advice=result.serving_advice,
        reference_notice=GLUCOSE_REFERENCE_NOTICE,
        risk_interpretation=GLUCOSE_RISK_INTERPRETATION,
        safety_warning=GLUCOSE_SAFETY_WARNING,
    )


def _nutrition_input_to_info(nutrition: NutritionInput) -> NutritionInfo:
    return NutritionInfo(
        food_name=nutrition.food_name,
        calories=nutrition.calories,
        carbs=nutrition.carbs,
        sugar=nutrition.sugar,
        protein=nutrition.protein,
        fat=nutrition.fat,
        fiber=nutrition.fiber,
        glycemic_index=nutrition.glycemic_index,
    )


def _risk_messages_from_flags(risk_flags: dict[int, dict[str, bool]] | None) -> dict[int, list[str]] | None:
    if not risk_flags:
        return None
    messages: dict[int, list[str]] = {}
    for horizon, flags in sorted(risk_flags.items()):
        horizon_messages: list[str] = []
        if flags.get("hypo_risk"):
            horizon_messages.append(
                f"{horizon}분 뒤 저혈당 가능성 신호가 감지되었습니다. 실제 혈당 측정값과 증상을 우선 확인하세요."
            )
        if flags.get("hyper_risk"):
            horizon_messages.append(
                f"{horizon}분 뒤 고혈당 가능성 신호가 감지되었습니다. 실제 혈당 측정값과 증상을 우선 확인하세요."
            )
        if horizon_messages:
            messages[int(horizon)] = horizon_messages
    return messages or None


_CGM_MODEL_LOAD_FAILED_DETAIL = (
    "CGM 예측 모델을 불러오지 못했습니다. "
    "서버의 scikit-learn 등 라이브러리 버전이 모델을 저장한 환경과 다를 수 있습니다. "
    "자세한 원인은 /health 의 cgm_forecast_error 를 확인하세요."
)


def _read_enriched_cgm_artifacts(model_dir) -> dict[str, object]:
    """enriched 모델과 함께 쓰는 보조 artifact를 forecast_from_enriched_payload 인자 형태로 읽는다."""
    metadata = load_forecast_metadata_cached(model_dir)
    return {
        "calibration_table": load_range_calibrators_cached(model_dir),
        "event_classifiers": load_event_classifiers_cached(model_dir),
        "event_thresholds": load_event_thresholds_cached(model_dir),
        "interval_config": load_prediction_intervals_cached(model_dir),
        "feature_columns": metadata.get("feature_columns", ENRICHED_FEATURE_COLUMNS),
    }


def _load_cgm_artifacts_or_503(loader, model_dir):
    """
    저장된 CGM 모델 파일을 읽지 못하면(예: scikit-learn 버전 불일치로 unpickle 실패)
    원인을 알 수 없는 500 대신 이유가 담긴 503을 반환한다.
    """
    try:
        return loader(model_dir)
    except Exception as exc:
        logger.exception("CGM 예측 모델 로드 실패: %s", model_dir)
        raise HTTPException(status_code=503, detail=_CGM_MODEL_LOAD_FAILED_DETAIL) from exc


def check_cgm_forecast_readiness() -> tuple[bool, str | None]:
    """
    CGM 예측에 필요한 모델 파일을 한 번 로드해 보고 (준비 여부, 문제 설명)을 반환한다.

    서버 시작 시 호출해 /health 에 노출한다. 엔드포인트와 같은 cache를 쓰므로 성공하면
    첫 요청 전에 모델이 미리 로드된다. 예외를 던지지 않는다.
    """
    if not _CGM_FORECASTING_AVAILABLE:
        return False, f"CGM 예측 의존성을 불러오지 못했습니다: {_CGM_FORECASTING_IMPORT_ERROR}"
    problems: list[str] = []
    for label, model_dir, has_enriched_artifacts in (
        ("cgm-forecast", settings.glucose_forecast_model_dir, False),
        ("cgm-forecast-enriched", settings.glucose_forecast_enriched_model_dir, True),
    ):
        try:
            if not model_dir.exists():
                problems.append(f"{label}: 모델 폴더가 없습니다 ({model_dir.name})")
                continue
            if not load_forecast_models_cached(model_dir):
                problems.append(f"{label}: 모델 파일이 없습니다 ({model_dir.name})")
                continue
            if has_enriched_artifacts:
                _read_enriched_cgm_artifacts(model_dir)
        except Exception as exc:
            logger.exception("CGM 예측 모델 점검 실패: %s", model_dir)
            problems.append(
                f"{label}: {type(exc).__name__}: {exc} (설치된 scikit-learn {_installed_sklearn_version()})"
            )
    return not problems, "; ".join(problems) or None


def _installed_sklearn_version() -> str:
    try:
        from importlib.metadata import version

        return version("scikit-learn")
    except Exception:
        return "unknown"


@router.post("/classify", response_model=ClassificationResponse,
             summary="음식 이미지 분류")
async def classify_image(
    request: Request,
    file: UploadFile = File(..., description="음식 이미지 파일"),
):
    """
    업로드된 이미지를 EfficientNet-B0으로 분류합니다.
    Food-101 101개 클래스 중 top-5 결과를 반환합니다.
    """
    data = await file.read()
    try:
        validate_image(data, max_mb=settings.max_upload_size_mb)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    image = load_image(data)
    classifier = request.app.state.classifier
    if classifier is None:
        result = _color_based_fallback(image)
    else:
        result = classifier.predict(image)
    return _clf_result_to_response(result)


@router.post("/risk", response_model=RiskResponse,
             summary="영양정보 기반 혈당 위험도 예측")
async def predict_risk(
    request: Request,
    nutrition: NutritionInput,
):
    """
    영양정보를 직접 입력받아 XGBoost로 혈당 위험도를 예측합니다.
    """
    predictor = request.app.state.predictor
    result = predictor.predict_from_dict(
        nutrition.model_dump(),
        portion_g=nutrition.portion_g,
    )
    return _risk_result_to_response(result)


@router.post("/glucose-risk", response_model=GlucoseRiskResponse,
             summary="영양성분 기반 참고용 혈당 위험도 점수")
async def glucose_risk_score(nutrition: NutritionInput):
    """
    영양성분과 섭취량을 바탕으로 0-100 참고용 혈당 위험도 점수를 계산합니다.
    의료 진단이나 치료 지침이 아닙니다.
    """
    score = score_glucose_risk(_nutrition_input_to_info(nutrition), portion_g=nutrition.portion_g)
    return GlucoseRiskResponse(
        score=score.score,
        level=score.level,
        factors=score.factors,
        reference_notice=score.reference_notice,
    )


@router.post("/cgm-forecast", response_model=CGMForecastResponse,
             summary="최근 CGM 기반 30/60/90분 뒤 혈당 예측")
async def cgm_forecast(payload: CGMForecastRequest):
    """
    최근 5분 간격 CGM 값을 이용해 30/60/90분 뒤 혈당을 예측합니다.
    의료 진단이나 치료 지침이 아닙니다.
    """
    if not _CGM_FORECASTING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "이 배포 환경에서는 CGM 예측 의존성이 비활성화되어 있습니다. "
                "서버형 백엔드 배포에서 사용할 수 있습니다."
            ),
        )
    if not settings.glucose_forecast_model_dir.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "CGM 예측 모델이 없습니다. "
                "scripts/prepare_ohiot1dm_cgm.py 및 scripts/train_glucose_forecaster.py를 먼저 실행하세요."
            ),
        )
    models = _load_cgm_artifacts_or_503(load_forecast_models_cached, settings.glucose_forecast_model_dir)
    if not models:
        raise HTTPException(status_code=503, detail="CGM 예측 모델 파일을 찾지 못했습니다.")
    try:
        result = forecast_from_recent_readings(
            [reading.model_dump() for reading in payload.readings],
            models,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CGMForecastResponse(
        predictions_mg_dl=result.predictions,
        horizons_minutes=sorted(result.predictions),
        reference_notice=result.reference_notice,
        risk_interpretation=GLUCOSE_RISK_INTERPRETATION,
        safety_warning=GLUCOSE_SAFETY_WARNING,
    )


@router.post("/cgm-forecast-enriched", response_model=CGMEnrichedForecastResponse,
             summary="최근 CGM + 식사/인슐린 feature 기반 보정 혈당 예측")
async def cgm_forecast_enriched(payload: CGMEnrichedForecastRequest):
    """
    최근 CGM 값과 식사/인슐린/운동/수면 feature를 이용해 30/60/90분 뒤 혈당을 예측합니다.
    raw 예측, range-aware 보정 예측, 저/고혈당 가능성 확률을 함께 반환합니다.
    의료 진단이나 치료 지침이 아닙니다.
    """
    if not _CGM_FORECASTING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "이 배포 환경에서는 enriched CGM 예측 의존성이 비활성화되어 있습니다. "
                "서버형 백엔드 배포에서 사용할 수 있습니다."
            ),
        )
    model_dir = settings.glucose_forecast_enriched_model_dir
    if not model_dir.exists():
        raise HTTPException(
            status_code=503,
            detail="enriched CGM 예측 모델이 없습니다. scripts/train_glucose_forecaster.py를 먼저 실행하세요.",
        )
    models = _load_cgm_artifacts_or_503(load_forecast_models_cached, model_dir)
    if not models:
        raise HTTPException(status_code=503, detail="enriched CGM 예측 모델 파일을 찾지 못했습니다.")
    artifacts = _load_cgm_artifacts_or_503(_read_enriched_cgm_artifacts, model_dir)
    try:
        result = forecast_from_enriched_payload(
            [reading.model_dump() for reading in payload.readings],
            payload.event_features.model_dump(),
            models,
            **artifacts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CGMEnrichedForecastResponse(
        predictions_mg_dl=result.predictions,
        calibrated_predictions_mg_dl=result.calibrated_predictions,
        prediction_intervals_mg_dl=result.prediction_intervals,
        uncertainty_level=result.uncertainty_level,
        uncertainty_message=result.uncertainty_message,
        event_probabilities=result.event_probabilities,
        risk_flags=result.risk_flags,
        risk_messages=_risk_messages_from_flags(result.risk_flags),
        horizons_minutes=sorted(result.predictions),
        reference_notice=result.reference_notice,
        risk_interpretation=GLUCOSE_RISK_INTERPRETATION,
        safety_warning=GLUCOSE_SAFETY_WARNING,
    )


@router.post("/cgm-forecast-enriched-events", response_model=CGMForecastEnrichedEventsResponse,
             summary="raw 식사/인슐린/운동 이벤트 기반 보정 혈당 예측")
async def cgm_forecast_enriched_events(payload: CGMForecastEnrichedEventsRequest):
    """
    raw CGM readings와 식사/볼루스/기저/운동 이벤트를 API 내부에서 rolling feature로 바꾼 뒤
    30/60/90분 뒤 혈당 예측, range-aware 보정값, 저/고혈당 가능성 flag를 반환합니다.
    의료 진단이나 치료 지침이 아닙니다.
    """
    if not _CGM_FORECASTING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "이 배포 환경에서는 enriched CGM 이벤트 예측 의존성이 비활성화되어 있습니다. "
                "서버형 백엔드 배포에서 사용할 수 있습니다."
            ),
        )
    model_dir = settings.glucose_forecast_enriched_model_dir
    if not model_dir.exists():
        raise HTTPException(
            status_code=503,
            detail="enriched CGM 예측 모델이 없습니다. scripts/train_glucose_forecaster.py를 먼저 실행하세요.",
        )
    models = _load_cgm_artifacts_or_503(load_forecast_models_cached, model_dir)
    if not models:
        raise HTTPException(status_code=503, detail="enriched CGM 예측 모델 파일을 찾지 못했습니다.")
    artifacts = _load_cgm_artifacts_or_503(_read_enriched_cgm_artifacts, model_dir)
    readings = [reading.model_dump() for reading in payload.readings]
    try:
        event_features = build_enriched_features_from_raw_events(
            readings,
            meals=[event.model_dump() for event in payload.meals],
            bolus=[event.model_dump() for event in payload.bolus],
            basal=[event.model_dump() for event in payload.basal],
            exercise=[event.model_dump() for event in payload.exercise],
            sleep_indicator=payload.sleep_indicator,
            patient_id_numeric=payload.patient_id_numeric,
            biosignals=payload.biosignals.model_dump(),
        )
        result = forecast_from_enriched_payload(
            readings,
            event_features,
            models,
            **artifacts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CGMForecastEnrichedEventsResponse(
        predictions_mg_dl=result.predictions,
        calibrated_predictions_mg_dl=result.calibrated_predictions,
        prediction_intervals_mg_dl=result.prediction_intervals,
        uncertainty_level=result.uncertainty_level,
        uncertainty_message=result.uncertainty_message,
        event_probabilities=result.event_probabilities,
        risk_flags=result.risk_flags,
        risk_messages=_risk_messages_from_flags(result.risk_flags),
        engineered_event_features=CGMEnrichedFeatures(**event_features),
        horizons_minutes=sorted(result.predictions),
        reference_notice=result.reference_notice,
        risk_interpretation=GLUCOSE_RISK_INTERPRETATION,
        safety_warning=GLUCOSE_SAFETY_WARNING,
    )


@router.post("/analyze", response_model=FullAnalysisResponse,
             summary="이미지 → 분류 → 영양정보 조회 → 혈당 위험도 통합 분석")
async def full_analysis(
    request: Request,
    file: UploadFile = File(..., description="음식 이미지"),
    portion_g: float = Form(100.0, gt=0, description="섭취량 (g)"),
):
    """
    이미지 업로드 한 번으로:
    1. EfficientNet-B0으로 음식 분류
    2. 영양DB에서 영양정보 조회
    3. XGBoost로 혈당 위험도 예측

    까지 통합 처리합니다.
    """
    data = await file.read()
    try:
        validate_image(data, max_mb=settings.max_upload_size_mb)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    image = load_image(data)
    classifier = request.app.state.classifier
    predictor = request.app.state.predictor

    # 1. 분류 — torch 미설치 시 색상 기반 fallback
    if classifier is None:
        clf_result = _color_based_fallback(image)
    else:
        clf_result = classifier.predict(image)
    clf_response = _clf_result_to_response(clf_result)

    # 2. 영양정보 조회
    nutrition_info = get_nutrition(clf_result.food_key)
    nutrition_response = None
    glucose_risk_response = None
    if nutrition_info:
        nutrition_response = NutritionInput(
            food_name=nutrition_info.food_name,
            calories=nutrition_info.calories,
            carbs=nutrition_info.carbs,
            sugar=nutrition_info.sugar,
            protein=nutrition_info.protein,
            fat=nutrition_info.fat,
            fiber=nutrition_info.fiber,
            glycemic_index=nutrition_info.glycemic_index,
            portion_g=portion_g,
        )
        risk_result = predictor.predict(nutrition_info, portion_g=portion_g)
        glucose_score = score_glucose_risk(nutrition_info, portion_g=portion_g)
        glucose_risk_response = GlucoseRiskResponse(
            score=glucose_score.score,
            level=glucose_score.level,
            factors=glucose_score.factors,
            reference_notice=glucose_score.reference_notice,
        )
    else:
        logger.warning("영양DB에 '%s' 없음 — 기본값으로 위험도 예측", clf_result.food_key)
        risk_result = predictor.predict_from_dict(
            {"food_name": clf_result.food_key}, portion_g=portion_g
        )

    return FullAnalysisResponse(
        classification=clf_response,
        nutrition=nutrition_response,
        risk=_risk_result_to_response(risk_result),
        glucose_risk=glucose_risk_response,
    )
