#!/usr/bin/env python3
"""Check cached ensemble weight stability across calibration splits."""

from __future__ import annotations

import argparse
import csv
import json
import random
from itertools import product
from pathlib import Path

import torch
from sklearn.metrics import f1_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--weight-step", type=float, default=0.05)
    parser.add_argument("--calibration-ratio", type=float, default=0.5)
    parser.add_argument("--seed", type=int, action="append", required=True)
    parser.add_argument("--chunk-size", type=int, default=128)
    return parser.parse_args()


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


def normalized_weight_grid(num_models: int, step: float) -> torch.Tensor:
    units = round(1.0 / step)
    if abs(units * step - 1.0) > 1e-8:
        raise ValueError("--weight-step must divide 1.0 exactly")
    rows: list[tuple[float, ...]] = []
    for values in product(range(units + 1), repeat=num_models - 1):
        used = sum(values)
        if used > units:
            continue
        rows.append(tuple([*values, units - used][idx] / units for idx in range(num_models)))
    return torch.tensor(rows, dtype=torch.float32)


def metrics_for_weights(logits: torch.Tensor, labels: torch.Tensor, weights: torch.Tensor) -> dict[str, float]:
    blended = torch.einsum("mnc,m->nc", logits.float(), weights.float())
    probs = torch.softmax(blended, dim=1)
    preds = probs.argmax(dim=1)
    top3 = probs.topk(k=min(3, blended.shape[1]), dim=1).indices
    return {
        "top1": float(preds.eq(labels).float().mean().item()),
        "top3": float(top3.eq(labels[:, None]).any(dim=1).float().mean().item()),
        "macro_f1": float(f1_score(labels.tolist(), preds.tolist(), average="macro", zero_division=0)),
    }


def best_by_calibration_top1(
    weights: torch.Tensor,
    logits: torch.Tensor,
    labels: torch.Tensor,
    calibration_idx: torch.Tensor,
    evaluation_idx: torch.Tensor,
    chunk_size: int,
) -> tuple[int, float, float, float]:
    cal_logits = logits.index_select(1, calibration_idx).float()
    eval_logits = logits.index_select(1, evaluation_idx).float()
    cal_labels = labels.index_select(0, calibration_idx)
    eval_labels = labels.index_select(0, evaluation_idx)

    best_idx = 0
    best_cal_top1 = -1.0
    best_eval_top1 = -1.0
    best_full_top1 = -1.0
    for start in range(0, weights.shape[0], chunk_size):
        chunk = weights[start : start + chunk_size]
        cal_blended = torch.einsum("bm,mnc->bnc", chunk, cal_logits)
        cal_preds = cal_blended.argmax(dim=2)
        cal_top1 = cal_preds.eq(cal_labels.view(1, -1)).float().mean(dim=1)

        eval_blended = torch.einsum("bm,mnc->bnc", chunk, eval_logits)
        eval_preds = eval_blended.argmax(dim=2)
        eval_top1 = eval_preds.eq(eval_labels.view(1, -1)).float().mean(dim=1)

        full_top1 = (
            cal_top1 * (cal_labels.numel() / labels.numel())
            + eval_top1 * (eval_labels.numel() / labels.numel())
        )
        for offset in range(chunk.shape[0]):
            item = (
                float(cal_top1[offset].item()),
                float(eval_top1[offset].item()),
                float(full_top1[offset].item()),
            )
            current = (best_cal_top1, best_eval_top1, best_full_top1)
            if item > current:
                best_idx = start + offset
                best_cal_top1, best_eval_top1, best_full_top1 = item
    return best_idx, best_cal_top1, best_eval_top1, best_full_top1


def main() -> None:
    args = parse_args()
    cache = torch.load(args.cache, map_location="cpu")
    names = list(cache["names"])
    logits = cache["logits"].float()
    labels = cache["labels"].long()
    weights = normalized_weight_grid(len(names), args.weight_step)

    rows: list[dict[str, object]] = []
    selected_weights: list[list[float]] = []
    for seed in args.seed:
        calibration_idx, evaluation_idx = stratified_split(
            labels.tolist(),
            args.calibration_ratio,
            seed,
        )
        calibration_tensor = torch.tensor(calibration_idx, dtype=torch.long)
        evaluation_tensor = torch.tensor(evaluation_idx, dtype=torch.long)
        best_idx, fast_cal_top1, fast_eval_top1, fast_full_top1 = best_by_calibration_top1(
            weights,
            logits,
            labels,
            calibration_tensor,
            evaluation_tensor,
            args.chunk_size,
        )
        best_weights = weights[best_idx]
        selected_weights.append([float(value) for value in best_weights.tolist()])
        full = metrics_for_weights(logits, labels, best_weights)
        calibration = metrics_for_weights(
            logits.index_select(1, calibration_tensor),
            labels.index_select(0, calibration_tensor),
            best_weights,
        )
        evaluation = metrics_for_weights(
            logits.index_select(1, evaluation_tensor),
            labels.index_select(0, evaluation_tensor),
            best_weights,
        )
        row: dict[str, object] = {
            "seed": seed,
            "calibration_ratio": args.calibration_ratio,
            "fast_calibration_top1": fast_cal_top1,
            "fast_evaluation_top1": fast_eval_top1,
            "fast_full_top1": fast_full_top1,
            "calibration_top1": calibration["top1"],
            "calibration_top3": calibration["top3"],
            "calibration_macro_f1": calibration["macro_f1"],
            "evaluation_top1": evaluation["top1"],
            "evaluation_top3": evaluation["top3"],
            "evaluation_macro_f1": evaluation["macro_f1"],
            "full_top1": full["top1"],
            "full_top3": full["top3"],
            "full_macro_f1": full["macro_f1"],
        }
        row.update({f"w_{name}": float(weight) for name, weight in zip(names, best_weights.tolist())})
        rows.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "seed",
        "calibration_ratio",
        *[f"w_{name}" for name in names],
        "calibration_top1",
        "calibration_top3",
        "calibration_macro_f1",
        "evaluation_top1",
        "evaluation_top3",
        "evaluation_macro_f1",
        "full_top1",
        "full_top3",
        "full_macro_f1",
        "fast_calibration_top1",
        "fast_evaluation_top1",
        "fast_full_top1",
    ]
    with (args.output_dir / "stability_by_seed.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    weight_tensor = torch.tensor(selected_weights, dtype=torch.float32)
    weight_summary = {
        name: {
            "min": float(weight_tensor[:, idx].min().item()),
            "max": float(weight_tensor[:, idx].max().item()),
            "mean": float(weight_tensor[:, idx].mean().item()),
        }
        for idx, name in enumerate(names)
    }
    summary = {
        "cache": str(args.cache),
        "names": names,
        "weight_step": args.weight_step,
        "calibration_ratio": args.calibration_ratio,
        "seeds": args.seed,
        "num_weight_candidates": int(weights.shape[0]),
        "num_samples": int(labels.numel()),
        "weight_summary": weight_summary,
        "rows": rows,
    }
    (args.output_dir / "stability_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Cached Ensemble Weight Stability",
        "",
        f"- cache: `{args.cache}`",
        f"- weight_step: `{args.weight_step}`",
        f"- calibration_ratio: `{args.calibration_ratio}`",
        f"- seeds: `{', '.join(str(seed) for seed in args.seed)}`",
        "",
        "## Selected Weight Ranges",
        "",
        "| Model | Min | Mean | Max |",
        "|---|---:|---:|---:|",
    ]
    for name in names:
        item = weight_summary[name]
        lines.append(f"| {name} | {item['min']:.4f} | {item['mean']:.4f} | {item['max']:.4f} |")
    lines.extend([
        "",
        "## Per-Seed Metrics",
        "",
        "| Seed | Full Top1 | Eval Top1 | Full Macro-F1 |",
        "|---:|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['seed']} | {float(row['full_top1']):.6f} | "
            f"{float(row['evaluation_top1']):.6f} | {float(row['full_macro_f1']):.6f} |"
        )
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
