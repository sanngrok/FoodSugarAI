from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.glucose.constants import GLUCOSE_REFERENCE_NOTICE, GLUCOSE_RISK_INTERPRETATION, GLUCOSE_SAFETY_WARNING


class NutritionInput(BaseModel):
    food_name: str = "Unknown"
    calories: float = Field(..., ge=0, description="칼로리 (kcal/100g)")
    carbs: float = Field(..., ge=0, description="탄수화물 (g/100g)")
    sugar: float = Field(..., ge=0, description="당류 (g/100g)")
    protein: float = Field(..., ge=0, description="단백질 (g/100g)")
    fat: float = Field(..., ge=0, description="지방 (g/100g)")
    fiber: float = Field(0.0, ge=0, description="식이섬유 (g/100g)")
    glycemic_index: float = Field(50.0, ge=0, le=100, description="GI 지수")
    portion_g: float = Field(100.0, gt=0, description="섭취량 (g)")


class ClassificationResponse(BaseModel):
    food_key: str
    food_name_ko: str
    confidence: float
    top5: list[tuple[str, float]]


class RiskResponse(BaseModel):
    risk_level: int
    risk_label: str
    risk_color: str
    risk_emoji: str
    probabilities: dict[str, float]
    feature_importance: dict[str, float] | None = None
    serving_advice: str
    reference_notice: str = GLUCOSE_REFERENCE_NOTICE
    risk_interpretation: str = GLUCOSE_RISK_INTERPRETATION
    safety_warning: str = GLUCOSE_SAFETY_WARNING


class HealthResponse(BaseModel):
    status: str
    version: str
    classifier_ready: bool
    predictor_ready: bool
    classifier_error: str | None = None


class GlucoseRiskResponse(BaseModel):
    score: float
    level: str
    factors: dict[str, float]
    reference_notice: str = GLUCOSE_REFERENCE_NOTICE
    risk_interpretation: str = GLUCOSE_RISK_INTERPRETATION
    safety_warning: str = GLUCOSE_SAFETY_WARNING


class FullAnalysisResponse(BaseModel):
    classification: ClassificationResponse
    nutrition: NutritionInput | None
    risk: RiskResponse
    glucose_risk: GlucoseRiskResponse | None = None


class CGMReading(BaseModel):
    timestamp: str
    glucose_mg_dl: float = Field(..., gt=0, le=600, description="CGM glucose value in mg/dL")

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_parseable(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception as exc:
            raise ValueError("timestamp는 ISO-8601 날짜/시간 문자열이어야 합니다.") from exc
        return value


class CGMForecastRequest(BaseModel):
    readings: list[CGMReading] = Field(..., min_length=13)


class CGMForecastResponse(BaseModel):
    predictions_mg_dl: dict[int, float]
    horizons_minutes: list[int]
    reference_notice: str = GLUCOSE_REFERENCE_NOTICE
    risk_interpretation: str = GLUCOSE_RISK_INTERPRETATION
    safety_warning: str = GLUCOSE_SAFETY_WARNING


class CGMEnrichedFeatures(BaseModel):
    carbs_current: float = 0.0
    carbs_last_30m: float = 0.0
    carbs_last_60m: float = 0.0
    carbs_last_120m: float = 0.0
    carbs_last_180m: float = 0.0
    bolus_current: float = 0.0
    bolus_last_30m: float = 0.0
    bolus_last_60m: float = 0.0
    bolus_last_120m: float = 0.0
    bolus_last_180m: float = 0.0
    basal_current: float = 0.0
    basal_mean_60m: float = 0.0
    basal_mean_120m: float = 0.0
    exercise_active: float = 0.0
    exercise_last_60m: float = 0.0
    exercise_last_120m: float = 0.0
    sleep_indicator: float = 0.0
    hypo_event_current: float = 0.0
    gsr_current: float = 0.0
    skin_temperature_current: float = 0.0
    acceleration_current: float = 0.0
    patient_id_numeric: float = 0.0
    time_since_last_meal: float = 240.0
    time_since_last_bolus: float = 240.0
    meal_bolus_gap_minutes: float = 0.0
    carbs_on_board_proxy: float = 0.0
    insulin_on_board_proxy: float = 0.0
    net_glucose_pressure_proxy: float = 0.0


class CGMEnrichedForecastRequest(CGMForecastRequest):
    event_features: CGMEnrichedFeatures = Field(default_factory=CGMEnrichedFeatures)


class CGMEnrichedForecastResponse(CGMForecastResponse):
    calibrated_predictions_mg_dl: dict[int, float] | None = None
    prediction_intervals_mg_dl: dict[int, list[float]] | None = None
    uncertainty_level: dict[int, str] | None = None
    uncertainty_message: dict[int, str] | None = None
    event_probabilities: dict[int, dict[str, float]] | None = None
    risk_flags: dict[int, dict[str, bool]] | None = None
    risk_messages: dict[int, list[str]] | None = None
    model_type: str = "enriched"


class RawMealEvent(BaseModel):
    timestamp: str
    carbs_g: float = Field(..., ge=0)


class RawBolusEvent(BaseModel):
    timestamp: str
    insulin_units: float = Field(..., ge=0)


class RawBasalEvent(BaseModel):
    timestamp: str
    rate_units_per_hour: float = Field(..., ge=0)


class RawExerciseEvent(BaseModel):
    timestamp: str
    duration_minutes: float = Field(0.0, ge=0)
    intensity: str | None = None


class CGMBiosignalFeatures(BaseModel):
    gsr_current: float = 0.0
    skin_temperature_current: float = 0.0
    acceleration_current: float = 0.0


class CGMForecastEnrichedEventsRequest(CGMForecastRequest):
    meals: list[RawMealEvent] = Field(default_factory=list)
    bolus: list[RawBolusEvent] = Field(default_factory=list)
    basal: list[RawBasalEvent] = Field(default_factory=list)
    exercise: list[RawExerciseEvent] = Field(default_factory=list)
    sleep_indicator: float = 0.0
    patient_id_numeric: float = 0.0
    biosignals: CGMBiosignalFeatures = Field(default_factory=CGMBiosignalFeatures)


class CGMForecastEnrichedEventsResponse(CGMEnrichedForecastResponse):
    engineered_event_features: CGMEnrichedFeatures
    model_type: str = "enriched_events"
