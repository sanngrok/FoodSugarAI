#!/usr/bin/env python3
"""Build human-review priority CSVs from an AI draft review file."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


PRIORITY_ACTIONS = {"relabel", "remove", "needs_human_review"}
RELABEL_REMOVE_ACTIONS = {"relabel", "remove"}
NEEDS_REVIEW_ACTIONS = {"needs_human_review", "needs_class_definition", "needs_more_data"}


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader), list(reader.fieldnames)


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ai-draft", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.ai_draft)
    if "action" not in fieldnames:
        raise ValueError("input must include an action column")

    priority = [r for r in rows if r.get("action") in PRIORITY_ACTIONS]
    relabel_remove = [r for r in rows if r.get("action") in RELABEL_REMOVE_ACTIONS]
    needs_review = [r for r in rows if r.get("action") in NEEDS_REVIEW_ACTIONS]

    write_rows(
        args.output_dir / "high_conf_priority_relabel_remove_needs_review.csv",
        priority,
        fieldnames,
    )
    write_rows(
        args.output_dir / "high_conf_priority_relabel_remove_only.csv",
        relabel_remove,
        fieldnames,
    )
    write_rows(
        args.output_dir / "high_conf_priority_needs_human_review_only.csv",
        needs_review,
        fieldnames,
    )

    action_counts = Counter(r.get("action", "") for r in rows)
    print(f"input_rows={len(rows)}")
    print(f"priority_rows={len(priority)}")
    print(f"relabel_remove_rows={len(relabel_remove)}")
    print(f"needs_review_rows={len(needs_review)}")
    print(f"action_counts={dict(action_counts)}")


if __name__ == "__main__":
    main()
