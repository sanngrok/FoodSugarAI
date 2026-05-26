"""Prepare a cleaned K-Food ImageFolder split from label patch files."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from collections import Counter
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG", ".BMP", ".WEBP"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-data-dir", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--exclude", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["symlink", "copy", "hardlink"], default="symlink")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--train-subdir", type=str, default="train")
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--keep-original-val", action="store_true")
    parser.add_argument("--make-cleaned-val", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def patch_key(row: dict[str, str]) -> tuple[str, str]:
    return row["old_label"].strip(), Path(row["image_path"]).name


def scan_split(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for class_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for image_path in sorted(path for path in class_dir.iterdir() if path.suffix in IMAGE_EXTS):
            rows.append({
                "path": str(image_path),
                "class_name": class_dir.name,
                "filename": image_path.name,
            })
    return rows


def link_or_copy(source: Path, dest: Path, mode: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        return
    if mode == "symlink":
        os.symlink(source.resolve(), dest)
    elif mode == "hardlink":
        os.link(source.resolve(), dest)
    else:
        shutil.copy2(source, dest)


def materialize_split(
    rows: list[dict[str, str]],
    output_root: Path,
    patch_by_key: dict[tuple[str, str], dict[str, str]],
    mode: str,
    apply_patch: bool,
) -> tuple[list[dict[str, str]], Counter]:
    manifest_rows: list[dict[str, str]] = []
    counts: Counter = Counter()
    for row in rows:
        key = (row["class_name"], row["filename"])
        patch = patch_by_key.get(key) if apply_patch else None
        action = patch["action"] if patch else "keep"
        if action == "remove":
            counts["removed"] += 1
            manifest_rows.append({
                **row,
                "output_path": "",
                "output_class_name": "",
                "action": "remove",
                "review_status": patch.get("review_status", "") if patch else "",
                "note": patch.get("note", "") if patch else "",
            })
            continue
        output_class = patch.get("new_label", row["class_name"]).strip() if patch and action == "relabel" else row["class_name"]
        dest = output_root / output_class / row["filename"]
        link_or_copy(Path(row["path"]), dest, mode)
        counts[action] += 1
        manifest_rows.append({
            **row,
            "output_path": str(dest),
            "output_class_name": output_class,
            "action": action,
            "review_status": patch.get("review_status", "") if patch else "",
            "note": patch.get("note", "") if patch else "",
        })
    return manifest_rows, counts


def ensure_class_dirs(root: Path, classes: list[str]) -> None:
    for class_name in classes:
        (root / class_name).mkdir(parents=True, exist_ok=True)


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "split",
        "path",
        "class_name",
        "filename",
        "output_path",
        "output_class_name",
        "action",
        "review_status",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if args.output_dir.resolve() == args.base_data_dir.resolve():
        raise ValueError("output-dir must differ from base-data-dir")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"output-dir exists and is not empty: {args.output_dir}")

    patch_rows = read_csv(args.patch)
    patch_by_key = {patch_key(row): row for row in patch_rows}
    train_rows = scan_split(args.base_data_dir / args.train_subdir)
    val_rows = scan_split(args.base_data_dir / args.val_subdir)
    classes = sorted({row["class_name"] for row in train_rows})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ensure_class_dirs(args.output_dir / "train", classes)
    train_manifest, train_counts = materialize_split(
        train_rows,
        args.output_dir / "train",
        patch_by_key,
        args.mode,
        apply_patch=True,
    )
    for row in train_manifest:
        row["split"] = "train"

    all_manifest_rows = list(train_manifest)
    val_counts: dict[str, dict[str, int]] = {}
    if args.keep_original_val:
        ensure_class_dirs(args.output_dir / "val_original_fixed", classes)
        original_manifest, original_counts = materialize_split(
            val_rows,
            args.output_dir / "val_original_fixed",
            patch_by_key,
            args.mode,
            apply_patch=False,
        )
        for row in original_manifest:
            row["split"] = "val_original_fixed"
        all_manifest_rows.extend(original_manifest)
        val_counts["val_original_fixed"] = dict(original_counts)

    if args.make_cleaned_val:
        ensure_class_dirs(args.output_dir / "val_cleaned", classes)
        cleaned_manifest, cleaned_counts = materialize_split(
            val_rows,
            args.output_dir / "val_cleaned",
            patch_by_key,
            args.mode,
            apply_patch=True,
        )
        for row in cleaned_manifest:
            row["split"] = "val_cleaned"
        all_manifest_rows.extend(cleaned_manifest)
        val_counts["val_cleaned"] = dict(cleaned_counts)

    write_manifest(args.manifest, all_manifest_rows)
    write_manifest(args.output_dir / "cleaned_manifest.csv", all_manifest_rows)
    split_meta = {
        "base_data_dir": str(args.base_data_dir),
        "patch": str(args.patch),
        "exclude": str(args.exclude),
        "output_dir": str(args.output_dir),
        "mode": args.mode,
        "train_count": sum(1 for row in train_manifest if row["action"] != "remove"),
        "val_original_fixed_count": sum(1 for row in all_manifest_rows if row["split"] == "val_original_fixed" and row["action"] != "remove"),
        "val_cleaned_count": sum(1 for row in all_manifest_rows if row["split"] == "val_cleaned" and row["action"] != "remove"),
        "num_classes": len(classes),
        "train_action_counts": dict(train_counts),
        "val_action_counts": val_counts,
        "review_basis": "AI visual draft candidate unless reviewed CSV was human-verified externally",
    }
    (args.output_dir / "split_meta.json").write_text(
        json.dumps(split_meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# K-Food cleaned_v1 Split",
        "",
        f"- base_data_dir: `{args.base_data_dir}`",
        f"- patch: `{args.patch}`",
        f"- output_dir: `{args.output_dir}`",
        f"- mode: `{args.mode}`",
        f"- train_count: `{split_meta['train_count']}`",
        f"- val_original_fixed_count: `{split_meta['val_original_fixed_count']}`",
        f"- val_cleaned_count: `{split_meta['val_cleaned_count']}`",
        "",
        "## Important",
        "",
        "This split is a candidate if the reviewed CSV comes from AI visual draft rather than human verification.",
        "Use `val_original_fixed` for fair comparison with existing fixed_v1 metrics.",
        "Use `val_cleaned` only as corrected-label diagnostic reporting.",
    ]
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
