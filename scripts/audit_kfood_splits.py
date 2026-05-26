#!/usr/bin/env python3
"""Audit overlap among old/new K-Food ImageFolder splits."""

from __future__ import annotations

import argparse
import csv
import json
from itertools import combinations
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def collect_split(root: Path, split: str) -> list[dict[str, str]]:
    split_dir = root / split
    if not split_dir.exists():
        raise FileNotFoundError(split_dir)

    rows: list[dict[str, str]] = []
    for class_dir in sorted(path for path in split_dir.iterdir() if path.is_dir()):
        for image_path in sorted(class_dir.rglob("*")):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            resolved = image_path.resolve()
            rows.append({
                "dataset": root.name,
                "split": split,
                "class_name": class_dir.name,
                "path": str(image_path),
                "resolved_path": str(resolved),
                "filename": image_path.name,
                "class_filename": f"{class_dir.name}/{image_path.name}",
            })
    return rows


def index_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row[key], []).append(row)
    return indexed


def build_overlap(
    left_name: str,
    left_rows: list[dict[str, str]],
    right_name: str,
    right_rows: list[dict[str, str]],
    key: str,
) -> list[dict[str, str]]:
    left_index = index_rows(left_rows, key)
    right_index = index_rows(right_rows, key)
    rows: list[dict[str, str]] = []
    for value in sorted(set(left_index) & set(right_index)):
        for left in left_index[value]:
            for right in right_index[value]:
                rows.append({
                    "match_key": key,
                    "match_value": value,
                    "left_split": left_name,
                    "left_class": left["class_name"],
                    "left_path": left["path"],
                    "left_resolved_path": left["resolved_path"],
                    "right_split": right_name,
                    "right_class": right["class_name"],
                    "right_path": right["path"],
                    "right_resolved_path": right["resolved_path"],
                })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-data-dir", type=Path, required=True)
    parser.add_argument("--new-data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    splits = {
        "old_train": collect_split(args.old_data_dir, "train"),
        "old_val": collect_split(args.old_data_dir, "val"),
        "new_train": collect_split(args.new_data_dir, "train"),
        "new_val": collect_split(args.new_data_dir, "val"),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_fields = [
        "match_key",
        "match_value",
        "left_split",
        "left_class",
        "left_path",
        "left_resolved_path",
        "right_split",
        "right_class",
        "right_path",
        "right_resolved_path",
    ]
    required_outputs = {
        ("old_train", "new_val"): "old_train_new_val_overlap.csv",
        ("old_val", "new_train"): "old_val_new_train_overlap.csv",
        ("old_val", "new_val"): "old_val_new_val_overlap.csv",
        ("old_train", "new_train"): "old_train_new_train_overlap.csv",
    }

    summary: dict[str, object] = {
        "old_data_dir": str(args.old_data_dir),
        "new_data_dir": str(args.new_data_dir),
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "overlaps": {},
    }
    all_overlap_rows: list[dict[str, str]] = []
    filename_overlap_rows: list[dict[str, str]] = []

    for left_name, right_name in combinations(splits.keys(), 2):
        left_rows = splits[left_name]
        right_rows = splits[right_name]
        resolved_rows = build_overlap(left_name, left_rows, right_name, right_rows, "resolved_path")
        filename_rows = build_overlap(left_name, left_rows, right_name, right_rows, "class_filename")
        pair_key = f"{left_name}__{right_name}"
        summary["overlaps"][pair_key] = {
            "resolved_path_rows": len(resolved_rows),
            "resolved_path_unique": len({row["match_value"] for row in resolved_rows}),
            "class_filename_rows": len(filename_rows),
            "class_filename_unique": len({row["match_value"] for row in filename_rows}),
        }
        all_overlap_rows.extend(resolved_rows)
        filename_overlap_rows.extend(filename_rows)
        output_name = required_outputs.get((left_name, right_name))
        if output_name:
            write_csv(args.output_dir / output_name, resolved_rows, csv_fields)

    write_csv(args.output_dir / "all_resolved_path_overlaps.csv", all_overlap_rows, csv_fields)
    write_csv(args.output_dir / "all_class_filename_overlaps.csv", filename_overlap_rows, csv_fields)
    (args.output_dir / "overlap_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    old_train_new_val = summary["overlaps"]["old_train__new_val"]
    lines = [
        "# K-Food Split Leakage Audit",
        "",
        f"- old_data_dir: `{args.old_data_dir}`",
        f"- new_data_dir: `{args.new_data_dir}`",
        "",
        "## Split Counts",
        "",
        "| Split | Count |",
        "|---|---:|",
    ]
    for split_name, count in summary["split_counts"].items():
        lines.append(f"| {split_name} | {count} |")
    lines.extend([
        "",
        "## Overlap Summary",
        "",
        "| Pair | Resolved Unique | Class+Filename Unique |",
        "|---|---:|---:|",
    ])
    for pair_key, item in summary["overlaps"].items():
        lines.append(
            f"| {pair_key} | {item['resolved_path_unique']} | {item['class_filename_unique']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        f"- old_train -> new_val resolved overlap: `{old_train_new_val['resolved_path_unique']}`",
        "- If this value is large, ensembles containing models trained on the old split can be inflated on the new validation split.",
        "- `class_filename` overlap is a softer filename-level check; resolved-path overlap is the stronger leakage signal.",
    ])
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
