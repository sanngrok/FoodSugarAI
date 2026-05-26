from pathlib import Path

import pandas as pd

from src.glucose.constants import GLUCOSE_REFERENCE_NOTICE
from src.glucose.forecasting import forecast_from_recent_readings
from src.glucose.ohiot1dm import parse_ohiot1dm_xml
from src.glucose.risk import score_glucose_risk
from src.nutrition.nutrition_db import NutritionInfo


class _ConstantModel:
    def __init__(self, value):
        self.value = value

    def predict(self, x):
        return [self.value for _ in range(len(x))]


def test_glucose_risk_score_contains_reference_notice():
    info = NutritionInfo(
        food_name="테스트",
        calories=300,
        carbs=55,
        sugar=22,
        protein=6,
        fat=8,
        fiber=2,
        glycemic_index=70,
    )

    result = score_glucose_risk(info, portion_g=150)

    assert 0 <= result.score <= 100
    assert result.level in {"낮음", "주의", "높음"}
    assert result.reference_notice == GLUCOSE_REFERENCE_NOTICE
    assert result.factors["scaled_carbs_g"] == 82.5


def test_parse_ohiot1dm_xml_extracts_glucose_rows(tmp_path):
    xml_path = tmp_path / "001-ws-training.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<patient id="001" weight="70" insulin_type="Novalog">
  <glucose_level>
    <event ts="01-01-2026 00:00:00" value="100"/>
    <event ts="01-01-2026 00:05:00" value="105"/>
  </glucose_level>
  <meal>
    <event ts="01-01-2026 00:10:00" type="Snack" carbs="12"/>
  </meal>
</patient>
""",
        encoding="utf-8",
    )

    frame = parse_ohiot1dm_xml(xml_path, year=2026, split="train")

    assert len(frame) == 2
    assert frame["patient_id"].tolist() == ["001", "001"]
    assert frame["glucose_mg_dl"].tolist() == [100.0, 105.0]
    assert frame["split"].iloc[0] == "train"


def test_forecast_from_recent_readings_returns_all_horizons():
    timestamps = pd.date_range("2026-01-01 00:00:00", periods=13, freq="5min")
    readings = [
        {"timestamp": str(timestamp), "glucose_mg_dl": 100 + idx}
        for idx, timestamp in enumerate(timestamps)
    ]
    models = {
        30: _ConstantModel(120),
        60: _ConstantModel(140),
        90: _ConstantModel(160),
    }

    result = forecast_from_recent_readings(readings, models)

    assert result.predictions == {30: 120.0, 60: 140.0, 90: 160.0}
    assert result.reference_notice == GLUCOSE_REFERENCE_NOTICE
