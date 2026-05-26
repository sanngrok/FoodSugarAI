import json
from pathlib import Path


def test_glucose_leakage_audit_documents_threshold_split_and_calibration_safety():
    audit_path = Path("reports/glucose_forecasting/leakage_audit.json")

    assert audit_path.exists()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert audit["threshold_selection"]["selection_split"]
    assert audit["threshold_selection"]["selection_split"] == "validation"
    assert audit["threshold_selection"]["evaluation_split"] == "test"
    assert audit["threshold_selection"]["threshold_selection_method"]
    assert audit["hypo_model_selection"]["selection_split"] == "validation"
    assert audit["calibration_selection"]["selection_split"] == "validation"
    assert audit["calibration"]["leakage_safe"] is True
    assert audit["calibration"]["forbidden_columns_found"] == []


def test_glucose_leakage_audit_no_longer_warns_about_test_threshold_selection():
    audit = json.loads(Path("reports/glucose_forecasting/leakage_audit.json").read_text(encoding="utf-8"))
    messages = [issue["message"] for issue in audit["issues"]]

    assert not any("final test set" in message for message in messages)
    assert audit["threshold_selection"]["leakage_warning"] is False
    assert audit["hypo_model_selection"]["leakage_warning"] is False
