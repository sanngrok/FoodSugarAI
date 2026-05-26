import pandas as pd

from src.glucose.forecasting import LONG_HORIZON_FEATURE_COLUMNS, add_cgm_features, add_long_horizon_features


def test_iob_cob_proxy_features_exist_without_future_leakage():
    timestamps = pd.date_range("2026-01-01", periods=40, freq="5min")
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "glucose_mg_dl": [100.0 + idx for idx in range(40)],
        "patient_id": ["1"] * 40,
        "source_file": ["s"] * 40,
        "carbs_current": [0.0] * 39 + [50.0],
        "carbs_last_30m": [0.0] * 39 + [50.0],
        "carbs_last_60m": [0.0] * 39 + [50.0],
        "carbs_last_120m": [0.0] * 39 + [50.0],
        "carbs_last_180m": [0.0] * 39 + [50.0],
        "bolus_current": [0.0] * 40,
        "bolus_last_30m": [0.0] * 40,
        "bolus_last_60m": [0.0] * 40,
        "bolus_last_120m": [0.0] * 40,
        "bolus_last_180m": [0.0] * 40,
    })

    featured = add_long_horizon_features(add_cgm_features(frame))

    assert set(LONG_HORIZON_FEATURE_COLUMNS).issubset(featured.columns)
    assert featured.loc[38, "carbs_on_board_proxy"] == 0
    assert featured.loc[39, "carbs_on_board_proxy"] > 0
    assert featured.loc[39, "time_since_last_meal"] == 0


def test_iob_cob_feature_reports_exist():
    for path in [
        "reports/glucose_forecasting/iob_cob_feature_audit.csv",
        "reports/glucose_forecasting/iob_cob_feature_summary.json",
    ]:
        assert pd.io.common.file_exists(path), path
