#!/usr/bin/env python3
"""Summarize low-performing K-Food classes and review candidates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


HARD_CLASSES = [
    "김치찌개",
    "동태찌개",
    "순두부찌개",
    "된장찌개",
    "곰탕_설렁탕",
    "갈비탕",
    "삼계탕",
    "갈비구이",
    "갈비찜",
    "삼겹살",
    "보쌈",
    "족발",
    "라면",
    "라볶이",
    "칼국수",
    "수제비",
    "감자전",
    "호박전",
    "파전",
    "비빔냉면",
    "물냉면",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def confusion_pairs(confusion_path: Path) -> list[dict[str, object]]:
    with confusion_path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        classes = header[1:]
        rows = []
        for row in reader:
            true = row[0]
            counts = [int(value) for value in row[1:]]
            total = sum(counts)
            correct = counts[classes.index(true)]
            for pred, count in zip(classes, counts):
                if pred == true or count == 0:
                    continue
                rows.append({
                    "true_class": true,
                    "pred_class": pred,
                    "count": count,
                    "true_total": total,
                    "true_accuracy": correct / total if total else 0.0,
                })
        return sorted(rows, key=lambda item: int(item["count"]), reverse=True)


def markdown_table(rows: list[dict[str, object]], columns: list[str], limit: int) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return lines


def load_per_class_by_name(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not path.exists():
        return {}
    return {row["class_name"]: row for row in read_csv(path)}


def hard_class_summary(
    current_rows: list[dict[str, str]],
    baseline_rows: dict[str, dict[str, str]],
    confusion_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    current_by_name = {row["class_name"]: row for row in current_rows}
    confusion_by_true: dict[str, int] = {}
    confusion_by_pred: dict[str, int] = {}
    for row in confusion_rows:
        true_name = str(row["true_class"])
        pred_name = str(row["pred_class"])
        count = int(row["count"])
        confusion_by_true[true_name] = confusion_by_true.get(true_name, 0) + count
        confusion_by_pred[pred_name] = confusion_by_pred.get(pred_name, 0) + count

    rows: list[dict[str, object]] = []
    for class_name in HARD_CLASSES:
        current = current_by_name.get(class_name)
        baseline = baseline_rows.get(class_name)
        if current is None:
            rows.append({
                "class_name": class_name,
                "present": False,
                "precision": "",
                "recall": "",
                "f1": "",
                "support": "",
                "baseline_f1": "",
                "delta_f1": "",
                "errors_as_true": "",
                "errors_as_pred": "",
            })
            continue
        current_f1 = float(current["f1"])
        baseline_f1 = float(baseline["f1"]) if baseline else None
        rows.append({
            "class_name": class_name,
            "present": True,
            "precision": f"{float(current['precision']):.6f}",
            "recall": f"{float(current['recall']):.6f}",
            "f1": f"{current_f1:.6f}",
            "support": int(float(current["support"])),
            "baseline_f1": f"{baseline_f1:.6f}" if baseline_f1 is not None else "",
            "delta_f1": f"{current_f1 - baseline_f1:.6f}" if baseline_f1 is not None else "",
            "errors_as_true": confusion_by_true.get(class_name, 0),
            "errors_as_pred": confusion_by_pred.get(class_name, 0),
        })
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-eval-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    per_class_path = args.eval_dir / "per_class_metrics.csv"
    confusion_path = args.eval_dir / "confusion_matrix.csv"
    high_conf_path = args.eval_dir / "high_confidence_errors.csv"
    if not per_class_path.exists():
        raise FileNotFoundError(per_class_path)
    if not confusion_path.exists():
        raise FileNotFoundError(confusion_path)

    per_class = read_csv(per_class_path)
    for row in per_class:
        for key in ("precision", "recall", "f1", "accuracy"):
            row[key] = f"{float(row[key]):.6f}"
        row["support"] = int(float(row["support"]))

    low_f1 = sorted(per_class, key=lambda row: float(row["f1"]))[:15]
    low_recall = sorted(per_class, key=lambda row: float(row["recall"]))[:15]
    low_precision = sorted(per_class, key=lambda row: float(row["precision"]))[:15]
    pairs = confusion_pairs(confusion_path)[:30]
    all_pairs = confusion_pairs(confusion_path)
    high_conf = read_csv(high_conf_path) if high_conf_path.exists() else []
    high_conf_top300 = high_conf[:300]
    baseline_rows = load_per_class_by_name(
        args.baseline_eval_dir / "per_class_metrics.csv" if args.baseline_eval_dir else None
    )
    hard_rows = hard_class_summary(per_class, baseline_rows, all_pairs)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    class_fields = ["class_index", "class_name", "precision", "recall", "f1", "accuracy", "support"]
    write_csv(args.output_dir / "low_f1_classes.csv", low_f1, class_fields)
    write_csv(args.output_dir / "low_recall_classes.csv", low_recall, class_fields)
    write_csv(args.output_dir / "low_precision_classes.csv", low_precision, class_fields)
    write_csv(
        args.output_dir / "top_confusion_pairs.csv",
        pairs,
        ["true_class", "pred_class", "count", "true_total", "true_accuracy"],
    )
    if high_conf:
        write_csv(args.output_dir / "high_confidence_errors_top300.csv", high_conf_top300, list(high_conf[0].keys()))
        write_csv(args.output_dir / "samples_to_review.csv", high_conf_top300, list(high_conf[0].keys()))
    else:
        write_csv(args.output_dir / "high_confidence_errors_top300.csv", [], ["image_path"])
        write_csv(args.output_dir / "samples_to_review.csv", [], ["image_path"])
    write_csv(
        args.output_dir / "hard_class_delta_summary.csv",
        hard_rows,
        [
            "class_name",
            "present",
            "precision",
            "recall",
            "f1",
            "support",
            "baseline_f1",
            "delta_f1",
            "errors_as_true",
            "errors_as_pred",
        ],
    )

    suggested = [
        "# Suggested Data Actions",
        "",
        "## 1. Label Review Priority",
        "",
        "Review `high_confidence_errors_top300.csv` first. These are the cases where the model was most confident but wrong.",
        "",
        "Review criteria:",
        "",
        "- Is the label actually wrong?",
        "- Does the image contain multiple foods?",
        "- Is the target food too small or occluded?",
        "- Is the class definition ambiguous?",
        "- Does this pair overlap visually with another class?",
        "",
        "## 2. Class-Specific Actions",
        "",
        "### Soup/stew/tang classes",
        "",
        "- Prioritize label review for 동태찌개, 김치찌개, 순두부찌개, 된장찌개, 곰탕_설렁탕, 갈비탕, 삼계탕.",
        "- Add or prioritize images where distinctive ingredients are visible, not only broth color.",
        "- Mark close-up broth-only images as ambiguous review candidates.",
        "",
        "### Jeon classes",
        "",
        "- Review 호박전, 감자전, 파전 confusion.",
        "- Prefer images where ingredient texture is visible.",
        "",
        "### Similar paired dishes",
        "",
        "- 떡볶이/라볶이: check whether noodles are visible.",
        "- 물냉면/비빔냉면: check broth/sauce visibility.",
        "- 족발/보쌈: check skin/fat texture and plating ambiguity.",
        "",
    ]
    (args.output_dir / "suggested_data_actions.md").write_text("\n".join(suggested), encoding="utf-8")

    readme = [
        "# K-Food Error Analysis",
        "",
        f"- eval_dir: `{args.eval_dir}`",
        f"- baseline_eval_dir: `{args.baseline_eval_dir or ''}`",
        f"- high_confidence_errors_available: `{bool(high_conf)}`",
        f"- high_confidence_errors_review_count: `{len(high_conf_top300)}`",
        "",
        "## Low F1 Classes",
        "",
        *markdown_table(low_f1, ["class_name", "f1", "precision", "recall", "support"], 15),
        "",
        "## Top Confusion Pairs",
        "",
        *markdown_table(pairs, ["true_class", "pred_class", "count", "true_accuracy"], 30),
        "",
        "## Hard Classes",
        "",
        *markdown_table(hard_rows, ["class_name", "f1", "precision", "recall", "support", "delta_f1"], len(hard_rows)),
        "",
    ]
    (args.output_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
