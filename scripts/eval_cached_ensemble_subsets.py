#!/usr/bin/env python3
"""Evaluate cached ensemble logits on leakage-related validation subsets."""

from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path

import torch
from sklearn.metrics import f1_score


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_overlap_paths(path: Path, left_split: str, right_split: str) -> set[str]:
    paths: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["left_split"] == left_split and row["right_split"] == right_split:
                paths.add(row["right_path"])
    return paths


def metrics_for_logits(logits: torch.Tensor, labels: torch.Tensor, num_classes: int) -> dict[str, float]:
    if labels.numel() == 0:
        return {"count": 0, "top1": 0.0, "top3": 0.0, "macro_f1": 0.0}
    probs = torch.softmax(logits, dim=1)
    preds = probs.argmax(dim=1)
    top3 = probs.topk(k=min(3, num_classes), dim=1).indices
    return {
        "count": int(labels.numel()),
        "top1": float(preds.eq(labels).float().mean().item()),
        "top3": float(top3.eq(labels[:, None]).any(dim=1).float().mean().item()),
        "macro_f1": float(
            f1_score(
                labels.tolist(),
                preds.tolist(),
                labels=list(range(num_classes)),
                average="macro",
                zero_division=0,
            )
        ),
    }


def weighted_logits(logits: torch.Tensor, weights: list[float]) -> torch.Tensor:
    return (logits * torch.tensor(weights, dtype=logits.dtype).view(-1, 1, 1)).sum(dim=0)


def normalized_weight_grid(num_models: int, step: float) -> list[list[float]]:
    units = round(1.0 / step)
    if abs(units * step - 1.0) > 1e-8:
        raise ValueError("--weight-step must divide 1.0 exactly")
    weights: list[list[float]] = []
    for values in product(range(units + 1), repeat=num_models - 1):
        used = sum(values)
        if used > units:
            continue
        full = [*values, units - used]
        weights.append([value / units for value in full])
    return weights


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "ensemble",
        "subset",
        "count",
        "ratio",
        "top1",
        "top3",
        "macro_f1",
        "weights",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--class-filename-overlaps", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--weight-step", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cache = torch.load(args.cache, map_location="cpu")
    metrics = load_json(args.metrics)

    names = list(cache["names"])
    paths = list(cache["paths"])
    labels = cache["labels"].long()
    logits = cache["logits"].float()
    num_classes = logits.shape[-1]

    old_train_new_val = load_overlap_paths(args.class_filename_overlaps, "old_train", "new_val")
    old_val_new_val = load_overlap_paths(args.class_filename_overlaps, "old_val", "new_val")
    all_indices = set(range(len(paths)))
    old_train_indices = {idx for idx, path in enumerate(paths) if path in old_train_new_val}
    old_val_indices = {idx for idx, path in enumerate(paths) if path in old_val_new_val}
    clean_minus_old_train = all_indices - old_train_indices
    clean_minus_any_old = all_indices - old_train_indices - old_val_indices

    subsets = {
        "full": sorted(all_indices),
        "old_train_filename_overlap_new_val": sorted(old_train_indices),
        "old_val_filename_overlap_new_val": sorted(old_val_indices),
        "minus_old_train_filename_overlap": sorted(clean_minus_old_train),
        "minus_old_train_and_old_val_filename_overlap": sorted(clean_minus_any_old),
    }

    weight_sets: dict[str, list[float]] = {
        "simple_average": [1.0 / len(names) for _ in names],
        "weighted_selected": [float(metrics["best_weights"][name]) for name in names],
    }
    if "diagnostic_full_best_weights" in metrics:
        weight_sets["diagnostic_full_best"] = [
            float(metrics["diagnostic_full_best_weights"][name]) for name in names
        ]
    for model_idx, name in enumerate(names):
        one_hot = [0.0 for _ in names]
        one_hot[model_idx] = 1.0
        weight_sets[f"single_{name}"] = one_hot

    rows: list[dict[str, object]] = []
    total = len(paths)
    for ensemble_name, weights in weight_sets.items():
        combined = weighted_logits(logits, weights)
        for subset_name, indices in subsets.items():
            index_tensor = torch.tensor(indices, dtype=torch.long)
            subset_metrics = metrics_for_logits(
                combined.index_select(0, index_tensor),
                labels.index_select(0, index_tensor),
                num_classes,
            )
            rows.append({
                "ensemble": ensemble_name,
                "subset": subset_name,
                "count": subset_metrics["count"],
                "ratio": subset_metrics["count"] / total if total else 0.0,
                "top1": subset_metrics["top1"],
                "top3": subset_metrics["top3"],
                "macro_f1": subset_metrics["macro_f1"],
                "weights": json.dumps(dict(zip(names, weights)), ensure_ascii=False),
            })

    sweep_rows: list[dict[str, object]] = []
    for subset_name in (
        "minus_old_train_filename_overlap",
        "old_val_filename_overlap_new_val",
        "old_train_filename_overlap_new_val",
        "full",
    ):
        indices = subsets[subset_name]
        if not indices:
            continue
        index_tensor = torch.tensor(indices, dtype=torch.long)
        subset_labels = labels.index_select(0, index_tensor)
        for weights in normalized_weight_grid(len(names), args.weight_step):
            combined = weighted_logits(logits, weights)
            subset_metrics = metrics_for_logits(
                combined.index_select(0, index_tensor),
                subset_labels,
                num_classes,
            )
            row: dict[str, object] = {
                "subset": subset_name,
                "count": subset_metrics["count"],
                "top1": subset_metrics["top1"],
                "top3": subset_metrics["top3"],
                "macro_f1": subset_metrics["macro_f1"],
            }
            row.update({f"w_{name}": weight for name, weight in zip(names, weights)})
            sweep_rows.append(row)
    sweep_rows.sort(
        key=lambda row: (str(row["subset"]), -float(row["top1"]), -float(row["macro_f1"]))
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "subset_metrics.csv", rows)
    subset_dir = args.output_dir / "subset_manifests"
    subset_dir.mkdir(parents=True, exist_ok=True)
    for subset_name, indices in subsets.items():
        with (subset_dir / f"{subset_name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "label_index"])
            writer.writeheader()
            for idx in indices:
                writer.writerow({"path": paths[idx], "label_index": int(labels[idx])})
    sweep_fields = ["subset", "count", *[f"w_{name}" for name in names], "top1", "top3", "macro_f1"]
    with (args.output_dir / "subset_weight_sweep.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sweep_fields)
        writer.writeheader()
        for row in sweep_rows:
            writer.writerow(row)

    summary = {
        "cache": str(args.cache),
        "metrics": str(args.metrics),
        "class_filename_overlaps": str(args.class_filename_overlaps),
        "names": names,
        "subset_counts": {
            name: len(indices)
            for name, indices in subsets.items()
        },
        "weight_sets": {
            name: dict(zip(names, weights))
            for name, weights in weight_sets.items()
        },
        "weight_step": args.weight_step,
        "subset_weight_sweep_best": {
            subset_name: next(
                row for row in sweep_rows if row["subset"] == subset_name
            )
            for subset_name in sorted({str(row["subset"]) for row in sweep_rows})
        },
        "rows": rows,
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    selected_rows = {
        (row["ensemble"], row["subset"]): row
        for row in rows
    }
    lines = [
        "# Cached Ensemble Subset Evaluation",
        "",
        f"- cache: `{args.cache}`",
        f"- class_filename_overlaps: `{args.class_filename_overlaps}`",
        "",
        "## Subset Counts",
        "",
        "| Subset | Count | Ratio |",
        "|---|---:|---:|",
    ]
    for subset_name, indices in subsets.items():
        lines.append(f"| {subset_name} | {len(indices)} | {len(indices) / total if total else 0.0:.6f} |")

    lines.extend([
        "",
        "## Weighted Selected Metrics",
        "",
        "| Subset | Count | Top1 | Top3 | Macro-F1 |",
        "|---|---:|---:|---:|---:|",
    ])
    for subset_name in subsets:
        row = selected_rows[("weighted_selected", subset_name)]
        lines.append(
            f"| {subset_name} | {row['count']} | {float(row['top1']):.6f} | "
            f"{float(row['top3']):.6f} | {float(row['macro_f1']):.6f} |"
        )

    lines.extend([
        "",
        "## Ensemble Comparison On Key Subsets",
        "",
        "| Ensemble | Full Top1 | Old-Train-Overlap Top1 | Minus-Old-Train Top1 |",
        "|---|---:|---:|---:|",
    ])
    for ensemble_name in weight_sets:
        full = selected_rows[(ensemble_name, "full")]
        overlap = selected_rows[(ensemble_name, "old_train_filename_overlap_new_val")]
        clean = selected_rows[(ensemble_name, "minus_old_train_filename_overlap")]
        lines.append(
            f"| {ensemble_name} | {float(full['top1']):.6f} | "
            f"{float(overlap['top1']):.6f} | {float(clean['top1']):.6f} |"
        )

    lines.extend([
        "",
        "## Best Weight Sweep By Subset",
        "",
        "| Subset | Top1 | Top3 | Macro-F1 | Weights |",
        "|---|---:|---:|---:|---|",
    ])
    for subset_name in sorted({str(row["subset"]) for row in sweep_rows}):
        row = next(item for item in sweep_rows if item["subset"] == subset_name)
        weight_text = ", ".join(f"{name}={row[f'w_{name}']}" for name in names)
        lines.append(
            f"| {subset_name} | {float(row['top1']):.6f} | {float(row['top3']):.6f} | "
            f"{float(row['macro_f1']):.6f} | {weight_text} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `old_train_filename_overlap_new_val` is the highest-risk subset for models trained on the old train split.",
        "- `minus_old_train_filename_overlap` is the more conservative validation view for any ensemble containing the old B0 baseline.",
        "- If the overlap subset is much easier than the minus-overlap subset, current full-val numbers should be treated as optimistic.",
    ])
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
