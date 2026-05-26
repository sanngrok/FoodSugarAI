import json
from pathlib import Path

import pandas as pd


def test_validation_split_files_are_created_from_train_only():
    base = Path("data/processed/ohiot1dm")
    train_inner = pd.read_csv(base / "cgm_train_inner_enriched.csv")
    validation = pd.read_csv(base / "cgm_validation_enriched.csv")
    test = pd.read_csv(base / "cgm_test_enriched.csv")

    assert set(train_inner["inner_split"].unique()) == {"train_inner"}
    assert set(validation["inner_split"].unique()) == {"validation"}
    assert set(test["inner_split"].unique()) == {"test"}
    assert set(train_inner["split"].unique()) == {"train"}
    assert set(validation["split"].unique()) == {"train"}
    assert set(test["split"].unique()) == {"test"}


def test_validation_split_preserves_time_order():
    audit = pd.read_csv("reports/glucose_forecasting/validation_split_audit.csv")
    summary = json.loads(Path("reports/glucose_forecasting/validation_split_summary.json").read_text(encoding="utf-8"))

    assert not audit.empty
    assert audit["time_order_safe"].all()
    assert summary["source_split"] == "train"
    assert summary["test_split_used_for_selection"] is False
    assert summary["time_order_safe"] is True
