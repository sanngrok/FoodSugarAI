from src.glucose.privacy import mask_glucose_payload_for_log


def test_glucose_log_masking_hides_raw_health_values():
    payload = {
        "request_id": "req_123",
        "readings": [
            {"timestamp": "2026-01-01T00:00:00", "glucose_mg_dl": 123},
            {"timestamp": "2026-01-01T00:05:00", "glucose_mg_dl": 126},
        ],
        "meals": [{"timestamp": "2026-01-01T00:00:00", "carbs_g": 45}],
        "bolus": [{"timestamp": "2026-01-01T00:00:00", "insulin_units": 4}],
        "patient_id_numeric": 540,
        "endpoint": "/predict/cgm-forecast-enriched-events",
    }

    masked = mask_glucose_payload_for_log(payload)
    text = str(masked)

    assert masked["request_id"] == "req_123"
    assert masked["readings_count"] == 2
    assert masked["meals_count"] == 1
    assert masked["bolus_count"] == 1
    assert masked["readings"] == "[masked]"
    assert masked["patient_id_numeric"] == "[masked]"
    assert "123" in text
    assert "glucose_mg_dl" not in text
    assert "insulin_units" not in text
    assert "carbs_g" not in text
    assert "540" not in text

