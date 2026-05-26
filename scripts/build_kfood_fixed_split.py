#!/usr/bin/env python3
"""Build a B0-baseline-safe fixed K-Food split from korean_food_1000."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def read_manifest(path: Path) -> list[tuple[Path, int]]:
    rows: list[tuple[Path, int]] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append((Path(row["path"]), int(row["label_index"])))
    return rows


def collect_imagefolder_split(data_dir: Path, split: str, classes: list[str]) -> list[tuple[Path, int]]:
    rows: list[tuple[Path, int]] = []
    for label_index, class_name in enumerate(classes):
        class_dir = data_dir / split / class_name
        if not class_dir.exists():
            raise FileNotFoundError(class_dir)
        for path in sorted(class_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                rows.append((path, label_index))
    return rows


def unique_by_class_filename(rows: list[tuple[Path, int]]) -> list[tuple[Path, int]]:
    seen: set[str] = set()
    unique_rows: list[tuple[Path, int]] = []
    for path, label_index in rows:
        key = f"{path.parent.name}/{path.name}"
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append((path, label_index))
    return unique_rows


def symlink_rows(rows: list[tuple[Path, int]], output_dir: Path, split: str, classes: list[str]) -> None:
    for source, label_index in rows:
        class_name = classes[label_index]
        target_dir = output_dir / split / class_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists() or target.is_symlink():
            raise FileExistsError(target)
        target.symlink_to(source.resolve())


def write_manifest(path: Path, rows: list[tuple[Path, int]], classes: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["path", "label_index", "class_name", "filename", "resolved_path"],
        )
        writer.writeheader()
        for source, label_index in rows:
            writer.writerow({
                "path": str(source),
                "label_index": label_index,
                "class_name": classes[label_index],
                "filename": source.name,
                "resolved_path": str(source.resolve()),
            })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-data-dir", type=Path, default=Path("data/raw/korean_food_1000"))
    parser.add_argument("--classes", type=Path, default=Path("data/models/korean_food_classes.json"))
    parser.add_argument("--old-train-overlap-manifest", type=Path, required=True)
    parser.add_argument("--fixed-val-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"output already exists: {args.output_dir}")

    classes = json.loads(args.classes.read_text(encoding="utf-8"))
    if not isinstance(classes, list):
        raise ValueError("classes JSON must be a list")

    current_train = collect_imagefolder_split(args.source_data_dir, "train", classes)
    old_train_overlap_val = read_manifest(args.old_train_overlap_manifest)
    fixed_val = read_manifest(args.fixed_val_manifest)

    train_rows = unique_by_class_filename([*current_train, *old_train_overlap_val])
    val_rows = unique_by_class_filename(fixed_val)
    train_keys = {f"{path.parent.name}/{path.name}" for path, _ in train_rows}
    val_keys = {f"{path.parent.name}/{path.name}" for path, _ in val_rows}
    overlap = train_keys & val_keys
    if overlap:
        raise RuntimeError(f"train/val class+filename overlap: {len(overlap)}")

    symlink_rows(train_rows, args.output_dir, "train", classes)
    symlink_rows(val_rows, args.output_dir, "val", classes)
    write_manifest(args.output_dir / "train_manifest.csv", train_rows, classes)
    write_manifest(args.output_dir / "val_manifest.csv", val_rows, classes)

    meta = {
        "source_data_dir": str(args.source_data_dir),
        "classes": str(args.classes),
        "old_train_overlap_manifest": str(args.old_train_overlap_manifest),
        "fixed_val_manifest": str(args.fixed_val_manifest),
        "output_dir": str(args.output_dir),
        "train_count": len(train_rows),
        "val_count": len(val_rows),
        "num_classes": len(classes),
        "split_policy": (
            "train = korean_food_1000/train + old_train_filename_overlap_new_val; "
            "val = minus_old_train_filename_overlap (old_val_filename_overlap_new_val)"
        ),
    }
    (args.output_dir / "split_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    readme = [
        "# K-Food Fixed V1 Split",
        "",
        "This split removes old-train filename overlap from validation for B0-baseline-safe evaluation.",
        "",
        f"- source_data_dir: `{args.source_data_dir}`",
        f"- train_count: `{len(train_rows)}`",
        f"- val_count: `{len(val_rows)}`",
        f"- num_classes: `{len(classes)}`",
        "",
        "## Policy",
        "",
        "- `train` = `korean_food_1000/train` plus the 4,474 validation samples that matched old train by class+filename.",
        "- `val` = the 6,720 samples that did not match old train by class+filename.",
        "- There is no train/val class+filename overlap in this split.",
        "",
        "## Caveat",
        "",
        "This is safer than the previous full validation for the old B0 baseline, but it is still derived from the same source dataset.",
    ]
    (args.output_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
