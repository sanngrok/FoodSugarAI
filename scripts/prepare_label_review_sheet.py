#!/usr/bin/env python3
"""Create a human review sheet from high-confidence K-Food errors."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(args.input)

    with args.input.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = [
        "rank",
        "image_path",
        "true_label",
        "pred_label",
        "confidence",
        "top3",
        "review_status",
        "corrected_label",
        "review_note",
        "action",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({
                "rank": rank,
                "image_path": row.get("image_path", ""),
                "true_label": row.get("true_class", row.get("true_label", "")),
                "pred_label": row.get("pred_class", row.get("pred_label", "")),
                "confidence": row.get("confidence", ""),
                "top3": row.get("top3", ""),
                "review_status": "",
                "corrected_label": "",
                "review_note": "",
                "action": "",
            })
    print(args.output)


if __name__ == "__main__":
    main()
