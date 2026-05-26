#!/usr/bin/env python3
"""Build K-Food label patch and exclude lists from a reviewed CSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REMOVE_STATUSES = {
    "ambiguous",
    "multi_food",
    "bad_crop",
    "low_quality",
    "out_of_scope",
    "unclear",
    "class_definition_overlap",
}
RELABEL_STATUSES = {"wrong_label"}
KEEP_STATUSES = {"correct", "model_error"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed", type=Path, required=True)
    parser.add_argument("--patch-output", type=Path, required=True)
    parser.add_argument("--exclude-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    return parser.parse_args()


def normalized_action(row: dict[str, str]) -> str:
    action = row.get("action", "").strip()
    status = row.get("review_status", "").strip()
    if action in {"relabel", "remove", "keep"}:
        return action
    if status in RELABEL_STATUSES:
        return "relabel"
    if status in REMOVE_STATUSES or status == "class_definition_overlap":
        return "remove"
    if status in KEEP_STATUSES:
        return "keep"
    return "keep"


def main() -> None:
    args = parse_args()
    with args.reviewed.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    patch_rows: list[dict[str, str]] = []
    exclude_rows: list[dict[str, str]] = []
    skipped_rows: list[dict[str, str]] = []
    for row in rows:
        action = normalized_action(row)
        image_path = row.get("image_path", "").strip()
        old_label = (row.get("true_label") or row.get("current_label") or "").strip()
        new_label = row.get("corrected_label", "").strip()
        status = row.get("review_status", "").strip()
        note = row.get("review_note", "").strip()
        if action == "relabel":
            if not new_label:
                skipped_rows.append({**row, "skip_reason": "missing_corrected_label"})
                continue
            patch_rows.append({
                "image_path": image_path,
                "old_label": old_label,
                "new_label": new_label,
                "action": "relabel",
                "review_status": status,
                "note": note or "review_top300_wrong_label",
            })
        elif action == "remove":
            item = {
                "image_path": image_path,
                "old_label": old_label,
                "new_label": "",
                "action": "remove",
                "review_status": status,
                "note": note or f"review_top300_{status}",
            }
            patch_rows.append(item)
            exclude_rows.append(item)

    args.patch_output.parent.mkdir(parents=True, exist_ok=True)
    args.exclude_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["image_path", "old_label", "new_label", "action", "review_status", "note"]
    with args.patch_output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patch_rows)
    with args.exclude_output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(exclude_rows)

    action_counts = Counter(row["action"] for row in patch_rows)
    status_counts = Counter(row["review_status"] for row in patch_rows)
    new_label_counts = Counter(row["new_label"] or "blank" for row in patch_rows)
    summary = {
        "reviewed": str(args.reviewed),
        "patch_output": str(args.patch_output),
        "exclude_output": str(args.exclude_output),
        "reviewed_rows": len(rows),
        "patch_rows": len(patch_rows),
        "exclude_rows": len(exclude_rows),
        "skipped_rows": len(skipped_rows),
        "action_counts": dict(action_counts),
        "status_counts": dict(status_counts),
        "new_label_counts": dict(new_label_counts),
        "skipped": skipped_rows,
    }

    lines = [
        "# K-Food Label Patch v1 Summary",
        "",
        f"- reviewed: `{args.reviewed}`",
        f"- patch_output: `{args.patch_output}`",
        f"- exclude_output: `{args.exclude_output}`",
        f"- reviewed_rows: `{len(rows)}`",
        f"- patch_rows: `{len(patch_rows)}`",
        f"- exclude_rows: `{len(exclude_rows)}`",
        f"- skipped_rows: `{len(skipped_rows)}`",
        "",
        "## Action Counts",
        "",
        "| Action | Count |",
        "|---|---:|",
    ]
    for action, count in sorted(action_counts.items()):
        lines.append(f"| {action} | {count} |")
    lines.extend([
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in sorted(status_counts.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
    ])
    args.report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.patch_output)


if __name__ == "__main__":
    main()
