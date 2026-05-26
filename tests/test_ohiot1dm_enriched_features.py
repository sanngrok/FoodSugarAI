from pathlib import Path

import pandas as pd

from src.glucose.forecasting import build_training_table


def test_enriched_csv_files_are_created():
    assert Path("data/processed/ohiot1dm/cgm_timeseries_enriched.csv").exists()
    assert Path("data/processed/ohiot1dm/cgm_train_enriched.csv").exists()
    assert Path("data/processed/ohiot1dm/cgm_test_enriched.csv").exists()


def test_enriched_feature_columns_exist_and_split_is_preserved():
    df = pd.read_csv("data/processed/ohiot1dm/cgm_timeseries_enriched.csv", nrows=1000)
    required = {
        "carbs_current",
        "carbs_last_30m",
        "bolus_current",
        "bolus_last_60m",
        "basal_current",
        "basal_mean_60m",
        "exercise_active",
        "exercise_last_120m",
        "sleep_indicator",
        "day_of_week",
        "patient_id_numeric",
    }

    assert required.issubset(df.columns)
    assert set(df["split"].unique()).issubset({"train", "test"})


def test_targets_use_future_values_only_as_targets_not_features():
    df = pd.read_csv("data/processed/ohiot1dm/cgm_train_enriched.csv", parse_dates=["timestamp"])
    one_source = df[df["source_file"] == df["source_file"].iloc[0]].head(80)
    table = build_training_table(one_source, horizons_minutes=[30])

    assert "target_30m" in table.columns
    assert "target_30m" not in [
        "glucose_mg_dl",
        "lag_1",
        "lag_2",
        "lag_3",
        "carbs_last_30m",
        "bolus_last_30m",
    ]
    deltas = (
        table.groupby("source_file")["timestamp"].shift(-6) - table["timestamp"]
    ).dt.total_seconds() / 60
    assert deltas.dropna().head(10).between(27.5, 32.5).all()
