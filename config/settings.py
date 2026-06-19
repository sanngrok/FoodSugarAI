from pathlib import Path
from typing import Any

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # App
    app_name: str = "FoodSugar AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # Model paths
    classifier_mode: str = "ensemble"
    classifier_model_path: Path = BASE_DIR / "data" / "models" / "efficientnet_food.pt"
    classifier_ensemble_config_path: Path = BASE_DIR / "config" / "kfood_production_ensemble_config.json"
    predictor_model_path: Path = BASE_DIR / "data" / "models" / "xgboost_sugar.pkl"
    label_encoder_path: Path = BASE_DIR / "data" / "models" / "label_encoder.pkl"
    use_xgboost_predictor_model: bool = False
    glucose_forecast_model_dir: Path = BASE_DIR / "data" / "processed" / "glucose_models"
    glucose_forecast_enriched_model_dir: Path = BASE_DIR / "data" / "processed" / "glucose_models_enriched"

    # EfficientNet
    image_size: int = 224
    num_food_classes: int = 101       # Food-101 기준
    classifier_threshold: float = 0.5

    # XGBoost risk labels
    risk_labels: list[str] = ["낮음", "주의", "높음"]

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    max_upload_size_mb: int = 10

    foodsafety_api_key: str = ""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"dev", "development"}:
                return True
        return value

    @field_validator(
        "classifier_model_path",
        "classifier_ensemble_config_path",
        "predictor_model_path",
        "label_encoder_path",
        "glucose_forecast_model_dir",
        "glucose_forecast_enriched_model_dir",
        mode="before",
    )
    @classmethod
    def strip_path_values(cls, value: Any):
        if isinstance(value, str):
            return value.strip()
        return value


settings = Settings()
