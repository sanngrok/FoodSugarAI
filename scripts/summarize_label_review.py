#!/usr/bin/env python3
"""Summarize a completed K-Food label review CSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


NOISY_STATUSES = (
    "wrong_label",
    "ambiguous",
    "multi_food",
    "bad_crop",
    "class_definition_overlap",
    "low_quality",
    "out_of_scope",
    "unclear",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def counter_dict(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    counts = Counter((row.get(key, "").strip() or "blank") for row in rows)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def write_counts(path: Path, label: str, counts: dict[str, int]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[label, "count"])
        writer.writeheader()
        for value, count in counts.items():
            writer.writerow({label: value, "count": count})


def write_filtered(path: Path, rows: list[dict[str, str]], statuses: set[str]) -> None:
    selected = [row for row in rows if row.get("review_status", "").strip() in statuses]
    fieldnames = list(rows[0].keys()) if rows else ["image_path", "review_status"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)


def main() -> None:
    args = parse_args()
    if not args.reviewed.exists():
        raise FileNotFoundError(args.reviewed)

    with args.reviewed.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    status_counts = counter_dict(rows, "review_status")
    action_counts = counter_dict(rows, "action")
    corrected_counts = counter_dict(rows, "corrected_label")
    reviewed_count = total - status_counts.get("blank", 0)
    noisy_labels = sum(status_counts.get(name, 0) for name in NOISY_STATUSES)
    noisy_ratio = noisy_labels / total if total else 0.0

    summary = {
        "reviewed": str(args.reviewed),
        "total_rows": total,
        "reviewed_count": reviewed_count,
        "reviewed_ratio": reviewed_count / total if total else 0.0,
        "noisy_label_count": noisy_labels,
        "noisy_label_ratio": noisy_ratio,
        "review_status_counts": status_counts,
        "action_counts": action_counts,
        "corrected_label_counts": corrected_counts,
        "noisy_statuses": list(NOISY_STATUSES),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "label_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "review_counts.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_counts(args.output_dir / "review_status_counts.csv", "review_status", status_counts)
    write_counts(args.output_dir / "action_counts.csv", "action", action_counts)
    write_counts(args.output_dir / "corrected_label_counts.csv", "corrected_label", corrected_counts)
    write_filtered(args.output_dir / "wrong_label_cases.csv", rows, {"wrong_label"})
    write_filtered(args.output_dir / "ambiguous_cases.csv", rows, {"ambiguous"})
    write_filtered(
        args.output_dir / "remove_candidates.csv",
        rows,
        {"ambiguous", "multi_food", "bad_crop", "low_quality", "out_of_scope", "unclear"},
    )
    write_filtered(
        args.output_dir / "class_definition_overlap_cases.csv",
        rows,
        {"class_definition_overlap"},
    )

    lines = [
        "# K-Food Label Review Summary",
        "",
        f"- reviewed: `{args.reviewed}`",
        f"- total_rows: `{total}`",
        f"- reviewed_count: `{reviewed_count}`",
        f"- noisy_label_ratio: `{noisy_ratio:.6f}`",
        "",
        "## Review Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in status_counts.items():
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Decision Rule",
        "",
        f"- Noisy statuses: `{', '.join(NOISY_STATUSES)}`.",
        "- If noisy statuses >= 10%, prioritize cleaned data retraining.",
        "- If noisy statuses < 5%, prioritize model diversity and ensemble weighting.",
    ])
    readme_text = "\n".join(lines) + "\n"
    (args.output_dir / "README.md").write_text(readme_text, encoding="utf-8")
    (args.output_dir / "label_audit_summary.md").write_text(readme_text, encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
