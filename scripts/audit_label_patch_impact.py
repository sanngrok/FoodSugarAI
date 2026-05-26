#!/usr/bin/env python3
"""Audit how a K-Food label patch affects an ImageFolder split."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--exclude", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-subdir", type=str, default="train")
    parser.add_argument("--val-subdir", type=str, default="val")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def patch_key(row: dict[str, str]) -> tuple[str, str]:
    return row["old_label"].strip(), Path(row["image_path"]).name


def scan_split(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for class_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for image_path in sorted(path for path in class_dir.iterdir() if path.is_file() or path.is_symlink()):
            rows.append({
                "path": str(image_path),
                "class_name": class_dir.name,
                "filename": image_path.name,
            })
    return rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "split",
        "path",
        "class_name",
        "filename",
        "action",
        "new_label",
        "review_status",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    patch_rows = read_csv(args.patch)
    patch_by_key = {patch_key(row): row for row in patch_rows}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    affected_by_split: dict[str, list[dict[str, str]]] = {}
    per_class = Counter()
    per_action = Counter()
    for split, subdir in (("train", args.train_subdir), ("val", args.val_subdir)):
        affected: list[dict[str, str]] = []
        for row in scan_split(args.data_dir / subdir):
            patch = patch_by_key.get((row["class_name"], row["filename"]))
            if not patch:
                continue
            item = {
                "split": split,
                "path": row["path"],
                "class_name": row["class_name"],
                "filename": row["filename"],
                "action": patch["action"],
                "new_label": patch.get("new_label", ""),
                "review_status": patch.get("review_status", ""),
                "note": patch.get("note", ""),
            }
            affected.append(item)
            per_class[(split, row["class_name"], patch["action"])] += 1
            per_action[(split, patch["action"])] += 1
        affected_by_split[split] = affected

    write_rows(args.output_dir / "train_affected.csv", affected_by_split["train"])
    write_rows(args.output_dir / "val_affected.csv", affected_by_split["val"])

    with (args.output_dir / "per_class_impact.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["split", "class_name", "action", "count"])
        writer.writeheader()
        for (split, class_name, action), count in sorted(per_class.items()):
            writer.writerow({"split": split, "class_name": class_name, "action": action, "count": count})

    summary = {
        "data_dir": str(args.data_dir),
        "patch": str(args.patch),
        "exclude": str(args.exclude),
        "train_subdir": args.train_subdir,
        "val_subdir": args.val_subdir,
        "patch_rows": len(patch_rows),
        "train_affected": len(affected_by_split["train"]),
        "val_affected": len(affected_by_split["val"]),
        "per_action": {f"{split}:{action}": count for (split, action), count in sorted(per_action.items())},
    }
    (args.output_dir / "patch_impact_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# K-Food Label Patch Impact Audit",
        "",
        f"- data_dir: `{args.data_dir}`",
        f"- patch_rows: `{len(patch_rows)}`",
        f"- train_affected: `{len(affected_by_split['train'])}`",
        f"- val_affected: `{len(affected_by_split['val'])}`",
        "",
        "## Per Action",
        "",
        "| Split | Action | Count |",
        "|---|---|---:|",
    ]
    for (split, action), count in sorted(per_action.items()):
        lines.append(f"| {split} | {action} | {count} |")
    lines.extend([
        "",
        "## Judgment",
        "",
        "- If validation affected rows are used for `val_cleaned`, report it separately from `val_original_fixed`.",
        "- If train affected rows dominate, retraining on cleaned train is the main test.",
    ])
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
