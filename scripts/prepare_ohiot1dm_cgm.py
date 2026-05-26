#!/usr/bin/env python3
"""Convert OhioT1DM XML files into CGM time-series CSV files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.glucose.ohiot1dm import ENRICHED_EVENT_COLUMNS, enrich_ohiot1dm_directory, parse_ohiot1dm_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="OhioT1DM root directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/ohiot1dm"),
        help="Directory for converted CGM CSV files.",
    )
    parser.add_argument(
        "--enriched",
        action="store_true",
        help="Also create leakage-safe meal/insulin/exercise/sleep enriched CGM CSV files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = parse_ohiot1dm_directory(args.input_dir)
    if frame.empty:
        raise RuntimeError(f"No CGM rows parsed from {args.input_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = args.output_dir / "cgm_timeseries.csv"
    frame.to_csv(all_path, index=False)

    summary: dict[str, object] = {
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "rows": int(len(frame)),
        "patients": int(frame["patient_id"].nunique()),
        "years": sorted(frame["year"].unique().tolist()),
        "splits": sorted(frame["split"].unique().tolist()),
        "glucose_min": float(frame["glucose_mg_dl"].min()),
        "glucose_max": float(frame["glucose_mg_dl"].max()),
    }
    for split, split_frame in frame.groupby("split"):
        split_path = args.output_dir / f"cgm_{split}.csv"
        split_frame.to_csv(split_path, index=False)
        summary[f"{split}_rows"] = int(len(split_frame))
        summary[f"{split}_patients"] = int(split_frame["patient_id"].nunique())

    if args.enriched:
        enriched = enrich_ohiot1dm_directory(args.input_dir)
        if enriched.empty:
            raise RuntimeError(f"No enriched CGM rows parsed from {args.input_dir}")
        enriched_path = args.output_dir / "cgm_timeseries_enriched.csv"
        enriched.to_csv(enriched_path, index=False)
        for split, split_frame in enriched.groupby("split"):
            split_frame.to_csv(args.output_dir / f"cgm_{split}_enriched.csv", index=False)
            summary[f"{split}_enriched_rows"] = int(len(split_frame))
        feature_audit = []
        for column in ENRICHED_EVENT_COLUMNS:
            if column not in enriched:
                continue
            nonzero = int((enriched[column].fillna(0) != 0).sum())
            feature_audit.append({
                "feature": column,
                "nonzero_rows": nonzero,
                "coverage_rate": nonzero / max(len(enriched), 1),
                "mean": float(enriched[column].fillna(0).mean()),
            })
        audit_path = Path("reports/glucose_forecasting/feature_enrichment_audit.csv")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        import pandas as pd
        pd.DataFrame(feature_audit).to_csv(audit_path, index=False)
        summary["enriched_output"] = str(enriched_path)
        summary["feature_enrichment_audit"] = str(audit_path)

    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    readme = [
        "# OhioT1DM CGM Conversion",
        "",
        f"- input_dir: `{args.input_dir}`",
        f"- rows: `{summary['rows']}`",
        f"- patients: `{summary['patients']}`",
        f"- train_rows: `{summary.get('train_rows', 0)}`",
        f"- test_rows: `{summary.get('test_rows', 0)}`",
        f"- output: `{all_path}`",
        f"- enriched_output: `{summary.get('enriched_output', '')}`",
        "",
        "This file contains CGM glucose-level events only. It is intended for",
        "forecasting experiments and is not a medical device dataset product.",
    ]
    (args.output_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
