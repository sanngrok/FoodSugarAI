#!/usr/bin/env python3
"""Cache logits and sweep weighted K-Food ensembles."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import sys
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image
import torch
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets
import torchvision.transforms as T

from src.classifier.food_classifier import FoodClassifier


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("eval_weighted_ensemble_sweep")


class PathImageDataset(Dataset):
    def __init__(self, samples: list[tuple[str, int]]) -> None:
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[str, int]:
        return self.samples[index]


def collate_paths(batch: list[tuple[str, int]]) -> tuple[list[str], torch.Tensor]:
    paths, labels = zip(*batch)
    return list(paths), torch.tensor(labels, dtype=torch.long)


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_transform(image_size: int) -> T.Compose:
    return T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def load_images(paths: list[str], transform: T.Compose, device: torch.device) -> torch.Tensor:
    images = []
    for path in paths:
        with Image.open(path) as img:
            images.append(transform(img.convert("RGB")))
    return torch.stack(images).to(device)


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
    if num_models < 1:
        raise ValueError("num_models must be >= 1")
    units = round(1.0 / step)
    if abs(units * step - 1.0) > 1e-8:
        raise ValueError("--weight-step must divide 1.0 exactly, e.g. 0.1 or 0.05")

    weights: list[tuple[float, ...]] = []
    for values in product(range(units + 1), repeat=num_models - 1):
        used = sum(values)
        if used > units:
            continue
        full = (*values, units - used)
        weights.append(tuple(value / units for value in full))
    return weights


def metrics_for_logits(logits: torch.Tensor, labels: torch.Tensor) -> dict[str, float]:
    if logits.numel() == 0:
        return {"top1": 0.0, "top3": 0.0, "macro_f1": 0.0}
    probs = torch.softmax(logits, dim=1)
    preds = probs.argmax(dim=1)
    top3 = probs.topk(k=min(3, logits.shape[1]), dim=1).indices
    labels_cpu = labels.cpu()
    preds_cpu = preds.cpu()
    return {
        "top1": float(preds_cpu.eq(labels_cpu).float().mean().item()),
        "top3": float(top3.cpu().eq(labels_cpu[:, None]).any(dim=1).float().mean().item()),
        "macro_f1": float(f1_score(labels_cpu.tolist(), preds_cpu.tolist(), average="macro", zero_division=0)),
    }


def weighted_logits(logits: torch.Tensor, weights: tuple[float, ...]) -> torch.Tensor:
    weight_tensor = torch.tensor(weights, dtype=logits.dtype).view(-1, 1, 1)
    return (logits * weight_tensor).sum(dim=0)


def compute_logits(args: argparse.Namespace, classes: list[str]) -> dict[str, object]:
    device = get_device()
    models: list[nn.Module] = []
    image_sizes: list[int] = []
    model_infos: list[dict[str, object]] = []

    for checkpoint, metadata_path, name in zip(args.checkpoint, args.metadata, args.name):
        metadata = load_json(metadata_path)
        classifier = FoodClassifier(model_path=checkpoint)
        if classifier.classes != classes:
            raise ValueError(f"class list mismatch for {checkpoint}")
        model = classifier.model
        if not isinstance(model, nn.Module):
            raise RuntimeError(f"failed to load model: {checkpoint}")
        image_size = int(metadata.get("image_size", classifier.image_size))
        models.append(model.to(device).eval())
        image_sizes.append(image_size)
        model_infos.append({
            "name": name,
            "checkpoint": str(checkpoint),
            "metadata": str(metadata_path),
            "model_type": classifier.model_type,
            "model_name": classifier.model_name,
            "image_size": image_size,
        })
        logger.info("loaded %s image_size=%s", name, image_size)

    image_folder = datasets.ImageFolder(args.data_dir / args.val_subdir)
    if image_folder.classes != classes:
        raise ValueError("validation class order differs from model classes")
    dataset = PathImageDataset(image_folder.samples)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_paths,
        pin_memory=device.type == "cuda",
    )

    all_labels: list[int] = []
    all_paths: list[str] = []
    per_model_logits = [[] for _ in models]
    transforms = {image_size: build_transform(image_size) for image_size in sorted(set(image_sizes))}
    with torch.inference_mode():
        for batch_idx, (paths, labels) in enumerate(loader, start=1):
            all_paths.extend(paths)
            all_labels.extend(labels.tolist())
            batch_images = {
                image_size: load_images(paths, transform, device)
                for image_size, transform in transforms.items()
            }
            for model_idx, (model, image_size) in enumerate(zip(models, image_sizes)):
                images = batch_images[image_size]
                if args.tta == "hflip":
                    both = torch.cat([images, torch.flip(images, dims=[3])], dim=0)
                    both_logits = model(both)
                    logits = 0.5 * (both_logits[: images.shape[0]] + both_logits[images.shape[0] :])
                else:
                    logits = model(images)
                per_model_logits[model_idx].append(logits.cpu())
            if batch_idx == 1 or batch_idx % 5 == 0 or batch_idx == len(loader):
                logger.info("cached logits batch %s/%s", batch_idx, len(loader))

    stacked = torch.stack([torch.cat(chunks, dim=0) for chunks in per_model_logits], dim=0)
    return {
        "names": args.name,
        "models": model_infos,
        "classes": classes,
        "paths": all_paths,
        "labels": torch.tensor(all_labels, dtype=torch.long),
        "logits": stacked,
        "data_dir": str(args.data_dir),
        "val_subdir": args.val_subdir,
        "tta": args.tta,
    }


def write_sweep(path: Path, rows: list[dict[str, object]], names: list[str]) -> None:
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
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--metadata", type=Path, action="append", required=True)
    parser.add_argument("--classes", type=Path, action="append", required=True)
    parser.add_argument("--name", type=str, action="append", required=True)
    parser.add_argument("--tta", choices=["none", "hflip"], default="none")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--weight-step", type=float, default=0.05)
    parser.add_argument("--calibration-ratio", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force-recompute", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (len(args.checkpoint) == len(args.metadata) == len(args.classes) == len(args.name)):
        raise ValueError("--checkpoint/--metadata/--classes/--name counts must match")
    if not 0.0 < args.calibration_ratio < 1.0:
        raise ValueError("--calibration-ratio must be between 0 and 1")

    class_lists = [load_json(path) for path in args.classes]
    if not all(class_lists[0] == class_list for class_list in class_lists):
        raise ValueError("class lists differ across models")
    classes = list(class_lists[0])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = args.output_dir / "logits_cache.pt"
    if cache_path.exists() and not args.force_recompute:
        logger.info("loading logits cache: %s", cache_path)
        cache = torch.load(cache_path, map_location="cpu")
    else:
        cache = compute_logits(args, classes)
        torch.save(cache, cache_path)

    logits = cache["logits"].float()
    labels = cache["labels"].long()
    names = list(cache["names"])
    calibration_idx, evaluation_idx = stratified_split(labels.tolist(), args.calibration_ratio, args.seed)
    calibration_tensor = torch.tensor(calibration_idx, dtype=torch.long)
    evaluation_tensor = torch.tensor(evaluation_idx, dtype=torch.long)

    rows: list[dict[str, object]] = []
    for weights in normalized_weight_grid(len(names), args.weight_step):
        full_logits = weighted_logits(logits, weights)
        calibration_metrics = metrics_for_logits(full_logits.index_select(0, calibration_tensor), labels.index_select(0, calibration_tensor))
        evaluation_metrics = metrics_for_logits(full_logits.index_select(0, evaluation_tensor), labels.index_select(0, evaluation_tensor))
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
        "calibration": metrics_for_logits(
            simple_logits.index_select(0, calibration_tensor),
            labels.index_select(0, calibration_tensor),
        ),
        "evaluation": metrics_for_logits(
            simple_logits.index_select(0, evaluation_tensor),
            labels.index_select(0, evaluation_tensor),
        ),
        "full": metrics_for_logits(simple_logits, labels),
    }
    best_weights = tuple(float(best[f"w_{name}"]) for name in names)
    best_logits = weighted_logits(logits, best_weights)
    best_metrics = {
        "calibration": {
            "top1": best["calibration_top1"],
            "top3": best["calibration_top3"],
            "macro_f1": best["calibration_macro_f1"],
        },
        "evaluation": {
            "top1": best["evaluation_top1"],
            "top3": best["evaluation_top3"],
            "macro_f1": best["evaluation_macro_f1"],
        },
        "full": metrics_for_logits(best_logits, labels),
    }

    write_sweep(args.output_dir / "sweep_results.csv", rows, names)
    metrics = {
        "names": names,
        "data_dir": str(args.data_dir),
        "val_subdir": cache.get("val_subdir", args.val_subdir),
        "tta": args.tta,
        "weight_step": args.weight_step,
        "calibration_ratio": args.calibration_ratio,
        "seed": args.seed,
        "num_samples": int(labels.numel()),
        "num_calibration": len(calibration_idx),
        "num_evaluation": len(evaluation_idx),
        "best_weights": {name: weight for name, weight in zip(names, best_weights)},
        "best_metrics": best_metrics,
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
        "# K-Food Weighted Ensemble Sweep",
        "",
        f"- data_dir: `{args.data_dir}`",
        f"- val_subdir: `{cache.get('val_subdir', args.val_subdir)}`",
        f"- tta: `{args.tta}`",
        f"- weight_step: `{args.weight_step}`",
        f"- num_samples: `{labels.numel()}`",
        "",
        "## Best Weights",
        "",
    ]
    for name, weight in zip(names, best_weights):
        lines.append(f"- {name}: `{weight}`")
    lines.extend([
        "",
        "## Diagnostic Full-Best Weights",
        "",
    ])
    for name in names:
        lines.append(f"- {name}: `{diagnostic_full_best[f'w_{name}']}`")
    lines.extend([
        "",
        "## Metrics",
        "",
        "| Ensemble | Split | Top1 | Top3 | Macro-F1 |",
        "|---|---|---:|---:|---:|",
    ])
    for label, metric_group in (("best", best_metrics), ("simple_avg", simple_metrics)):
        for split_name in ("calibration", "evaluation", "full"):
            item = metric_group[split_name]
            lines.append(
                f"| {label} | {split_name} | {item['top1']} | {item['top3']} | {item['macro_f1']} |"
            )
    lines.append(
        f"| diagnostic_full_best | full | {diagnostic_full_best['full_top1']} | "
        f"{diagnostic_full_best['full_top3']} | {diagnostic_full_best['full_macro_f1']} |"
    )
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("best_weights=%s best_full=%s", best_weights, best_metrics["full"])


if __name__ == "__main__":
    main()
