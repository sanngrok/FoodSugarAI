#!/usr/bin/env python3
"""Build a nutrition lookup table for the 56-class Korean food classifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


NUMERIC_COLUMNS = [
    "calories",
    "carbs",
    "sugar",
    "protein",
    "fat",
    "fiber",
    "glycemic_index",
]

# Classes without an exact row in train_data.csv. These aliases select the
# closest prepared-food rows and avoid sauce/snack-only rows where possible.
ALIASES: dict[str, list[str]] = {
    "갈비구이": ["갈비구이_돼지고기", "갈비구이_소고기_양념", "갈비구이_왕갈비_양념", "등갈비구이"],
    "양념치킨": ["양념치킨볼"],
    "한과": ["구름한과", "서산생강한과", "수정한과 오란다", "미소찹쌀한과"],
    "후라이드치킨": ["유별난 후라이드치킨", "더뉴우리쌀후라이드치킨", "삼양후라이드치킨", "면사랑 순살후라이드치킨"],
}

COMPOSITES: dict[str, list[str]] = {
    "곰탕_설렁탕": ["곰탕", "설렁탕"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--classes",
        type=Path,
        default=Path("data/models/korean_food_classes_b3_full_fixed_v1.json"),
    )
    parser.add_argument(
        "--train-data",
        type=Path,
        default=Path("data/processed/train_data.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/kfood_nutrition_db.json"),
    )
    return parser.parse_args()


def summarize_rows(food_key: str, rows: pd.DataFrame, match_type: str) -> dict[str, object]:
    means = rows[NUMERIC_COLUMNS].mean(numeric_only=True)
    return {
        "food_name": food_key,
        "calories": round(float(means["calories"]), 4),
        "carbs": round(float(means["carbs"]), 4),
        "sugar": round(float(means["sugar"]), 4),
        "protein": round(float(means["protein"]), 4),
        "fat": round(float(means["fat"]), 4),
        "fiber": round(float(means["fiber"]), 4),
        "glycemic_index": round(float(means["glycemic_index"]), 4),
        "source_rows": int(len(rows)),
        "source_food_names": sorted(rows["food_name"].astype(str).unique().tolist()),
        "match_type": match_type,
    }


def main() -> None:
    args = parse_args()
    classes = json.loads(args.classes.read_text(encoding="utf-8"))
    df = pd.read_csv(args.train_data)
    output: dict[str, object] = {}
    missing: list[str] = []

    for food_key in classes:
        if food_key in COMPOSITES:
            rows = df[df["food_name"].isin(COMPOSITES[food_key])]
            match_type = "composite_exact"
        elif food_key in ALIASES:
            rows = df[df["food_name"].isin(ALIASES[food_key])]
            match_type = "curated_alias"
        else:
            rows = df[df["food_name"] == food_key]
            match_type = "exact"

        if rows.empty:
            missing.append(food_key)
            continue
        output[food_key] = summarize_rows(food_key, rows, match_type)

    if missing:
        raise ValueError(f"nutrition rows not found for: {missing}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "ok",
        "output": str(args.output),
        "num_classes": len(output),
        "match_types": {
            match_type: sum(1 for item in output.values() if item["match_type"] == match_type)
            for match_type in sorted({item["match_type"] for item in output.values()})
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
