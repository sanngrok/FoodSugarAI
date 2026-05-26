#!/usr/bin/env python3
"""Sweep ensemble weights from a cached logits tensor."""

from __future__ import annotations

import argparse
import csv
import json
import random
from itertools import product
from pathlib import Path

import torch
from sklearn.metrics import f1_score


def stratified_split(labels: list[int], ratio: float, seed: int) -> tuple[list[int], list[int]]:
    by_class: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        by_class.setdefault(label, []).append(idx)
    rng = random.Random(seed)
    calibration: list[int] = []
    evaluation: list[int] = []
    for indices in by_class.values():
        shuffled = list(indices)
        rng.shuffle(shuffled)
        cut = max(1, min(len(shuffled) - 1, round(len(shuffled) * ratio)))
        calibration.extend(shuffled[:cut])
        evaluation.extend(shuffled[cut:])
    return sorted(calibration), sorted(evaluation)


def normalized_weight_grid(num_models: int, step: float) -> list[tuple[float, ...]]:
    units = round(1.0 / step)
    if abs(units * step - 1.0) > 1e-8:
        raise ValueError("--weight-step must divide 1.0 exactly")
    weights: list[tuple[float, ...]] = []
    for values in product(range(units + 1), repeat=num_models - 1):
        used = sum(values)
        if used > units:
            continue
        weights.append(tuple([*values, units - used][idx] / units for idx in range(num_models)))
    return weights


def weighted_logits(logits: torch.Tensor, weights: tuple[float, ...]) -> torch.Tensor:
    return (logits * torch.tensor(weights, dtype=logits.dtype).view(-1, 1, 1)).sum(dim=0)


def metrics_for_logits(logits: torch.Tensor, labels: torch.Tensor) -> dict[str, float]:
    probs = torch.softmax(logits, dim=1)
    preds = probs.argmax(dim=1)
    top3 = probs.topk(k=min(3, logits.shape[1]), dim=1).indices
    return {
        "top1": float(preds.eq(labels).float().mean().item()),
        "top3": float(top3.eq(labels[:, None]).any(dim=1).float().mean().item()),
        "macro_f1": float(f1_score(labels.tolist(), preds.tolist(), average="macro", zero_division=0)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--weight-step", type=float, default=0.05)
    parser.add_argument("--calibration-ratio", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cache = torch.load(args.cache, map_location="cpu")
    names = list(cache["names"])
    logits = cache["logits"].float()
    labels = cache["labels"].long()
    calibration_idx, evaluation_idx = stratified_split(labels.tolist(), args.calibration_ratio, args.seed)
    calibration_tensor = torch.tensor(calibration_idx, dtype=torch.long)
    evaluation_tensor = torch.tensor(evaluation_idx, dtype=torch.long)

    rows: list[dict[str, object]] = []
    for weights in normalized_weight_grid(len(names), args.weight_step):
        full_logits = weighted_logits(logits, weights)
        calibration_metrics = metrics_for_logits(
            full_logits.index_select(0, calibration_tensor),
            labels.index_select(0, calibration_tensor),
        )
        evaluation_metrics = metrics_for_logits(
            full_logits.index_select(0, evaluation_tensor),
            labels.index_select(0, evaluation_tensor),
        )
        full_metrics = metrics_for_logits(full_logits, labels)
        row: dict[str, object] = {f"w_{name}": weight for name, weight in zip(names, weights)}
        row.update({
            "calibration_top1": calibration_metrics["top1"],
            "calibration_top3": calibration_metrics["top3"],
            "calibration_macro_f1": calibration_metrics["macro_f1"],
            "evaluation_top1": evaluation_metrics["top1"],
            "evaluation_top3": evaluation_metrics["top3"],
            "evaluation_macro_f1": evaluation_metrics["macro_f1"],
            "full_top1": full_metrics["top1"],
            "full_top3": full_metrics["top3"],
            "full_macro_f1": full_metrics["macro_f1"],
        })
        rows.append(row)

    rows.sort(
        key=lambda row: (
            float(row["calibration_top1"]),
            float(row["calibration_macro_f1"]),
            float(row["evaluation_top1"]),
        ),
        reverse=True,
    )
    best = rows[0]
    diagnostic_full_best = max(
        rows,
        key=lambda row: (
            float(row["full_top1"]),
            float(row["full_macro_f1"]),
            float(row["full_top3"]),
        ),
    )
    simple_weights = tuple(1.0 / len(names) for _ in names)
    simple_logits = weighted_logits(logits, simple_weights)
    simple_metrics = {
        "full": metrics_for_logits(simple_logits, labels),
        "calibration": metrics_for_logits(
            simple_logits.index_select(0, calibration_tensor),
            labels.index_select(0, calibration_tensor),
        ),
        "evaluation": metrics_for_logits(
            simple_logits.index_select(0, evaluation_tensor),
            labels.index_select(0, evaluation_tensor),
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [f"w_{name}" for name in names] + [
        "calibration_top1",
        "calibration_top3",
        "calibration_macro_f1",
        "evaluation_top1",
        "evaluation_top3",
        "evaluation_macro_f1",
        "full_top1",
        "full_top3",
        "full_macro_f1",
    ]
    with (args.output_dir / "sweep_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metrics = {
        "cache": str(args.cache),
        "names": names,
        "data_dir": cache.get("data_dir"),
        "tta": cache.get("tta"),
        "weight_step": args.weight_step,
        "calibration_ratio": args.calibration_ratio,
        "seed": args.seed,
        "num_samples": int(labels.numel()),
        "num_calibration": len(calibration_idx),
        "num_evaluation": len(evaluation_idx),
        "best_weights": {name: float(best[f"w_{name}"]) for name in names},
        "best_metrics": {
            "calibration": {
                "top1": float(best["calibration_top1"]),
                "top3": float(best["calibration_top3"]),
                "macro_f1": float(best["calibration_macro_f1"]),
            },
            "evaluation": {
                "top1": float(best["evaluation_top1"]),
                "top3": float(best["evaluation_top3"]),
                "macro_f1": float(best["evaluation_macro_f1"]),
            },
            "full": {
                "top1": float(best["full_top1"]),
                "top3": float(best["full_top3"]),
                "macro_f1": float(best["full_macro_f1"]),
            },
        },
        "diagnostic_full_best_weights": {
            name: float(diagnostic_full_best[f"w_{name}"]) for name in names
        },
        "diagnostic_full_best_metrics": {
            "top1": float(diagnostic_full_best["full_top1"]),
            "top3": float(diagnostic_full_best["full_top3"]),
            "macro_f1": float(diagnostic_full_best["full_macro_f1"]),
        },
        "simple_average_metrics": simple_metrics,
        "models": cache["models"],
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Cached Weighted Ensemble Sweep",
        "",
        f"- cache: `{args.cache}`",
        f"- data_dir: `{cache.get('data_dir')}`",
        f"- tta: `{cache.get('tta')}`",
        "",
        "## Best Weights",
        "",
    ]
    for name in names:
        lines.append(f"- {name}: `{best[f'w_{name}']}`")
    lines.extend([
        "",
        "## Metrics",
        "",
        "| Ensemble | Split | Top1 | Top3 | Macro-F1 |",
        "|---|---|---:|---:|---:|",
    ])
    for split in ("calibration", "evaluation", "full"):
        item = metrics["best_metrics"][split]
        lines.append(f"| best | {split} | {item['top1']} | {item['top3']} | {item['macro_f1']} |")
    for split in ("calibration", "evaluation", "full"):
        item = simple_metrics[split]
        lines.append(f"| simple_avg | {split} | {item['top1']} | {item['top3']} | {item['macro_f1']} |")
    item = metrics["diagnostic_full_best_metrics"]
    lines.append(f"| diagnostic_full_best | full | {item['top1']} | {item['top3']} | {item['macro_f1']} |")
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
