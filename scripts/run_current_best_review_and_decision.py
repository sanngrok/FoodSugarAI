#!/usr/bin/env python3
"""Run safe current-best review checks and decision prerequisites.

This runner intentionally does not start B3 full training or cleaned split creation.
It only summarizes human review files when they exist and records the current decision state.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HIGH_REVIEW = ROOT / "reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv"
TRAIN_REVIEW = ROOT / "reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv"
HIGH_SUMMARY_DIR = ROOT / "reports/current_best/error_analysis/review_summary_high_conf_top300"
PATCH_OUTPUT = ROOT / "data/processed/kfood_train_hard_pair_patch_v2.csv"
EXCLUDE_OUTPUT = ROOT / "data/processed/kfood_train_hard_pair_exclude_v2.csv"
PATCH_REPORT = ROOT / "reports/current_best/hard_class_report/train_hard_pair_patch_v2_summary.md"
PATCH_AUDIT_DIR = ROOT / "reports/current_best/hard_class_report/train_hard_pair_patch_impact"
STATUS_JSON = ROOT / "reports/current_best/review_and_decision_status.json"
STATUS_MD = ROOT / "reports/current_best/review_and_decision_status.md"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def status_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    for row in read_csv(path):
        status = row.get("review_status", "").strip() or "blank"
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def label_boundary_ratio(counts: dict[str, int]) -> float | None:
    total = sum(counts.values())
    if total == 0:
        return None
    noisy = sum(
        counts.get(status, 0)
        for status in (
            "wrong_label",
            "ambiguous",
            "multi_food",
            "bad_crop",
            "class_definition_overlap",
            "unclear",
        )
    )
    return noisy / total


def patch_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    return max(0, sum(1 for _ in path.open(encoding="utf-8")) - 1)


def decision(high_counts: dict[str, int], train_patch_rows: int | None) -> str:
    ratio = label_boundary_ratio(high_counts)
    if ratio is None:
        return "waiting_for_human_review"
    if ratio >= 0.20:
        return "label_hard_pair_cleaning_first"
    if ratio < 0.10 and high_counts.get("model_error", 0) > sum(high_counts.values()) * 0.5:
        return "consider_b3_full"
    if train_patch_rows is not None and train_patch_rows >= 300:
        return "cleaned_train_v1_candidate"
    return "mixed_or_wait_for_train_review"


def write_status(payload: dict[str, object]) -> None:
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Current Best Review And Decision Status",
        "",
        f"- high_conf_review_exists: `{payload['high_conf_review_exists']}`",
        f"- train_review_exists: `{payload['train_review_exists']}`",
        f"- high_conf_label_boundary_ratio: `{payload.get('high_conf_label_boundary_ratio')}`",
        f"- train_patch_rows: `{payload.get('train_patch_rows')}`",
        f"- decision: `{payload['decision']}`",
        "",
        "## High-Confidence Review Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in (payload.get("high_conf_status_counts") or {}).items():
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Train Review Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in (payload.get("train_status_counts") or {}).items():
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- This runner does not start B3 full training.",
        "- This runner does not create cleaned_train_v1.",
        "- Missing human review files keep the decision in a waiting state.",
    ])
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summarize-if-available", action="store_true")
    parser.add_argument("--build-patch-if-available", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.summarize_if_available and HIGH_REVIEW.exists():
        run([
            sys.executable,
            "scripts/summarize_label_review.py",
            "--reviewed",
            str(HIGH_REVIEW.relative_to(ROOT)),
            "--output-dir",
            str(HIGH_SUMMARY_DIR.relative_to(ROOT)),
        ])

    if args.build_patch_if_available and TRAIN_REVIEW.exists():
        run([
            sys.executable,
            "scripts/build_kfood_label_patch.py",
            "--reviewed",
            str(TRAIN_REVIEW.relative_to(ROOT)),
            "--patch-output",
            str(PATCH_OUTPUT.relative_to(ROOT)),
            "--exclude-output",
            str(EXCLUDE_OUTPUT.relative_to(ROOT)),
            "--report-output",
            str(PATCH_REPORT.relative_to(ROOT)),
        ])
        run([
            sys.executable,
            "scripts/audit_label_patch_impact.py",
            "--data-dir",
            "data/raw/korean_food_fixed_v1",
            "--patch",
            str(PATCH_OUTPUT.relative_to(ROOT)),
            "--exclude",
            str(EXCLUDE_OUTPUT.relative_to(ROOT)),
            "--output-dir",
            str(PATCH_AUDIT_DIR.relative_to(ROOT)),
        ])

    high_counts = status_counts(HIGH_REVIEW)
    train_counts = status_counts(TRAIN_REVIEW)
    train_patch_rows = patch_rows(PATCH_OUTPUT)
    ratio = label_boundary_ratio(high_counts)
    payload = {
        "high_conf_review_exists": HIGH_REVIEW.exists(),
        "train_review_exists": TRAIN_REVIEW.exists(),
        "high_conf_status_counts": high_counts,
        "train_status_counts": train_counts,
        "high_conf_label_boundary_ratio": ratio,
        "train_patch_rows": train_patch_rows,
        "decision": decision(high_counts, train_patch_rows),
        "outputs": {
            "status_json": str(STATUS_JSON.relative_to(ROOT)),
            "status_md": str(STATUS_MD.relative_to(ROOT)),
            "high_summary_dir": str(HIGH_SUMMARY_DIR.relative_to(ROOT)),
            "patch_output": str(PATCH_OUTPUT.relative_to(ROOT)),
            "exclude_output": str(EXCLUDE_OUTPUT.relative_to(ROOT)),
            "patch_audit_dir": str(PATCH_AUDIT_DIR.relative_to(ROOT)),
        },
    }
    write_status(payload)
    print(STATUS_MD.relative_to(ROOT))


if __name__ == "__main__":
    main()
