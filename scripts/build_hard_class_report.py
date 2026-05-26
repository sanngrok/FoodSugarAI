#!/usr/bin/env python3
"""Build a focused hard-class report from K-Food error analysis outputs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def action_for_class(class_name: str) -> str:
    soup_keywords = ("찌개", "탕", "국", "곰탕", "설렁탕", "삼계탕")
    if any(keyword in class_name for keyword in soup_keywords):
        return "review broth-only images; prioritize images with distinctive ingredients"
    if class_name in {"떡볶이", "라볶이"}:
        return "review noodle visibility and class boundary"
    if class_name in {"물냉면", "비빔냉면"}:
        return "review broth/sauce visibility"
    if class_name in {"족발", "보쌈"}:
        return "review meat texture and plating ambiguity"
    if class_name.endswith("전"):
        return "review ingredient texture and crop quality"
    return "review high-confidence errors and add diverse clean examples"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--error-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    low_f1 = read_csv(args.error_dir / "low_f1_classes.csv")
    low_recall = read_csv(args.error_dir / "low_recall_classes.csv")
    low_precision = read_csv(args.error_dir / "low_precision_classes.csv")
    pairs = read_csv(args.error_dir / "top_confusion_pairs.csv")
    high_conf = read_csv(args.error_dir / "high_confidence_errors_top300.csv")

    hard_names = []
    for row in low_f1[:15] + low_recall[:10] + low_precision[:10]:
        name = row.get("class_name", "")
        if name and name not in hard_names:
            hard_names.append(name)

    error_counter: Counter[str] = Counter()
    pred_counter: Counter[str] = Counter()
    for row in high_conf:
        error_counter[row.get("true_class", "")] += 1
        pred_counter[row.get("pred_class", "")] += 1

    pair_by_true: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pairs:
        pair_by_true[row.get("true_class", "")].append(row)

    hard_class_rows: list[dict[str, object]] = []
    low_f1_by_name = {row.get("class_name", ""): row for row in low_f1}
    for name in hard_names:
        metric = low_f1_by_name.get(name, {})
        pair_text = "; ".join(
            f"{row.get('pred_class')}({row.get('count')})"
            for row in pair_by_true.get(name, [])[:3]
        )
        hard_class_rows.append({
            "class_name": name,
            "f1": metric.get("f1", ""),
            "precision": metric.get("precision", ""),
            "recall": metric.get("recall", ""),
            "support": metric.get("support", ""),
            "high_conf_errors_as_true": error_counter.get(name, 0),
            "high_conf_errors_as_pred": pred_counter.get(name, 0),
            "top_confusions": pair_text,
            "recommended_action": action_for_class(name),
        })

    pair_rows: list[dict[str, object]] = []
    for row in pairs[:30]:
        true_class = row.get("true_class", "")
        pred_class = row.get("pred_class", "")
        pair_rows.append({
            "true_class": true_class,
            "pred_class": pred_class,
            "count": row.get("count", ""),
            "true_total": row.get("true_total", ""),
            "true_accuracy": row.get("true_accuracy", ""),
            "recommended_action": f"{action_for_class(true_class)}; compare against {pred_class}",
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.output_dir / "hard_classes.csv",
        hard_class_rows,
        [
            "class_name",
            "f1",
            "precision",
            "recall",
            "support",
            "high_conf_errors_as_true",
            "high_conf_errors_as_pred",
            "top_confusions",
            "recommended_action",
        ],
    )
    write_csv(
        args.output_dir / "hard_pairs.csv",
        pair_rows,
        ["true_class", "pred_class", "count", "true_total", "true_accuracy", "recommended_action"],
    )

    lines = [
        "# K-Food Hard Class Report",
        "",
        f"- source_error_dir: `{args.error_dir}`",
        f"- hard_class_count: `{len(hard_class_rows)}`",
        f"- hard_pair_count: `{len(pair_rows)}`",
        "",
        "## Hard Classes",
        "",
        "| Class | F1 | Recall | High-Conf Errors | Action |",
        "|---|---:|---:|---:|---|",
    ]
    for row in hard_class_rows[:20]:
        lines.append(
            f"| {row['class_name']} | {row['f1']} | {row['recall']} | "
            f"{row['high_conf_errors_as_true']} | {row['recommended_action']} |"
        )
    lines.extend([
        "",
        "## Hard Pairs",
        "",
        "| True | Pred | Count | True Accuracy |",
        "|---|---|---:|---:|",
    ])
    for row in pair_rows[:20]:
        lines.append(
            f"| {row['true_class']} | {row['pred_class']} | {row['count']} | {row['true_accuracy']} |"
        )
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
