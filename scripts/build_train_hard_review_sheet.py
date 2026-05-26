#!/usr/bin/env python3
"""Build a train-focused hard-class K-Food label review sheet."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG", ".BMP", ".WEBP"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--hard-classes", type=Path, required=True)
    parser.add_argument("--hard-pairs", type=Path, required=True)
    parser.add_argument("--train-affected", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=500)
    parser.add_argument("--top-classes", type=int, default=20)
    parser.add_argument("--top-pairs", type=int, default=30)
    parser.add_argument("--per-pair-side", type=int, default=6)
    parser.add_argument("--per-class-extra", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def class_images(train_dir: Path, class_name: str) -> list[Path]:
    class_dir = train_dir / class_name
    if not class_dir.exists():
        return []
    return sorted(path for path in class_dir.iterdir() if path.suffix in IMAGE_EXTS)


def add_candidate(
    rows: list[dict[str, str]],
    seen: set[tuple[str, str]],
    image_path: Path,
    true_label: str,
    candidate_label: str,
    source: str,
    reason: str,
    prefill: dict[str, str] | None = None,
) -> None:
    key = (true_label, image_path.name)
    if key in seen:
        return
    seen.add(key)
    prefill = prefill or {}
    rows.append({
        "rank": str(len(rows) + 1),
        "image_path": str(image_path),
        "true_label": true_label,
        "pred_label": candidate_label,
        "confidence": "",
        "top3": "",
        "review_status": prefill.get("review_status", ""),
        "corrected_label": prefill.get("corrected_label", ""),
        "review_note": prefill.get("review_note", ""),
        "action": prefill.get("action", ""),
        "review_source": source,
        "priority_reason": reason,
    })


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    train_dir = args.data_dir / "train"
    hard_classes = read_csv(args.hard_classes)[: args.top_classes]
    hard_pairs = read_csv(args.hard_pairs)[: args.top_pairs]
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    if args.train_affected and args.train_affected.exists():
        for item in read_csv(args.train_affected):
            prefill = {
                "review_status": item.get("review_status", ""),
                "corrected_label": item.get("new_label", ""),
                "review_note": item.get("note", ""),
                "action": item.get("action", ""),
            }
            add_candidate(
                rows,
                seen,
                Path(item["path"]),
                item["class_name"],
                item.get("new_label", "") or "remove_candidate",
                "existing_ai_patch_train_affected",
                "Already matched by the AI draft patch on fixed_v1 train; confirm before applying to cleaned train.",
                prefill=prefill,
            )

    for pair in hard_pairs:
        true_class = pair["true_class"]
        pred_class = pair["pred_class"]
        count = pair.get("count", "")
        for source_class, compare_class, side in (
            (true_class, pred_class, "true_side"),
            (pred_class, true_class, "pred_side"),
        ):
            images = class_images(train_dir, source_class)
            rng.shuffle(images)
            for path in images[: args.per_pair_side]:
                add_candidate(
                    rows,
                    seen,
                    path,
                    source_class,
                    compare_class,
                    f"hard_pair_{side}",
                    f"Review boundary pair {true_class} vs {pred_class}; val confusion count={count}.",
                )
                if len(rows) >= args.max_samples:
                    break
            if len(rows) >= args.max_samples:
                break
        if len(rows) >= args.max_samples:
            break

    for item in hard_classes:
        class_name = item["class_name"]
        images = class_images(train_dir, class_name)
        rng.shuffle(images)
        reason = (
            f"Low F1 hard class review; f1={item.get('f1', '')}, "
            f"recall={item.get('recall', '')}, top_confusions={item.get('top_confusions', '')}."
        )
        candidate_label = item.get("top_confusions", "").split("(")[0].split(";")[0].strip()
        for path in images[: args.per_class_extra]:
            add_candidate(
                rows,
                seen,
                path,
                class_name,
                candidate_label or "hard_class_review",
                "hard_class_extra",
                reason,
            )
            if len(rows) >= args.max_samples:
                break
        if len(rows) >= args.max_samples:
            break

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
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
        "review_source",
        "priority_reason",
    ]
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    source_counts = Counter(row["review_source"] for row in rows)
    class_counts = Counter(row["true_label"] for row in rows)
    summary = {
        "data_dir": str(args.data_dir),
        "output_csv": str(args.output_csv),
        "num_samples": len(rows),
        "max_samples": args.max_samples,
        "seed": args.seed,
        "source_counts": dict(source_counts),
        "top_class_counts": dict(class_counts.most_common(30)),
        "note": "Train-focused review candidates only; not a model prediction result.",
    }
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Train Hard-Class Review Sheet",
        "",
        f"- data_dir: `{args.data_dir}`",
        f"- output_csv: `{args.output_csv}`",
        f"- num_samples: `{len(rows)}`",
        f"- seed: `{args.seed}`",
        "",
        "## Source Counts",
        "",
        "| Source | Count |",
        "|---|---:|",
    ]
    for source, count in source_counts.most_common():
        lines.append(f"| {source} | {count} |")
    lines.extend([
        "",
        "## Top Class Counts",
        "",
        "| Class | Count |",
        "|---|---:|",
    ])
    for class_name, count in class_counts.most_common(30):
        lines.append(f"| {class_name} | {count} |")
    lines.extend([
        "",
        "## Important",
        "",
        "This sheet samples fixed_v1 train images around hard classes and hard pairs.",
        "Rows are candidates for human review, not confirmed label errors.",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
    ])
    args.report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_csv)


if __name__ == "__main__":
    main()
