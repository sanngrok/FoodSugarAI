#!/usr/bin/env python3
"""Evaluate plain timm and Food-LeWM K-Food classifiers on ImageFolder val sets."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
import torchvision.transforms as T

from src.classifier.food_classifier import FoodClassifier


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("eval_kfood_any_model")


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


def write_per_class(path: Path, classes: list[str], y_true: list[int], y_pred: list[int]) -> None:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(len(classes))),
        zero_division=0,
    )
    correct = [0 for _ in classes]
    total = [0 for _ in classes]
    for target, pred in zip(y_true, y_pred):
        total[target] += 1
        if target == pred:
            correct[target] += 1
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["class_index", "class_name", "precision", "recall", "f1", "accuracy", "support"],
        )
        writer.writeheader()
        for idx, name in enumerate(classes):
            writer.writerow({
                "class_index": idx,
                "class_name": name,
                "precision": float(precision[idx]),
                "recall": float(recall[idx]),
                "f1": float(f1[idx]),
                "accuracy": correct[idx] / total[idx] if total[idx] else 0.0,
                "support": int(support[idx]),
            })


def write_confusion(path: Path, classes: list[str], y_true: list[int], y_pred: list[int]) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(classes))))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true\\pred", *classes])
        for idx, row in enumerate(matrix):
            writer.writerow([classes[idx], *row.tolist()])


def write_high_confidence_errors(
    path: Path,
    classes: list[str],
    records: list[dict[str, object]],
    limit: int = 1000,
) -> None:
    rows = sorted(
        (row for row in records if not row["correct"]),
        key=lambda row: float(row["confidence"]),
        reverse=True,
    )[:limit]
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "image_path",
            "true_index",
            "true_class",
            "pred_index",
            "pred_class",
            "confidence",
            "top3",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def write_readme(path: Path, metrics: dict[str, object]) -> None:
    lines = ["# K-Food Model Evaluation", ""]
    for key, value in metrics.items():
        lines.append(f"- {key}: `{value}`")
    path.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--classes", type=Path, required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--tta", choices=["none", "hflip"], default="none")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = get_device()
    classes = load_json(args.classes)
    metadata = load_json(args.metadata)
    if not isinstance(classes, list):
        raise ValueError("classes JSON must be a list")
    if not isinstance(metadata, dict):
        raise ValueError("metadata JSON must be an object")

    classifier = FoodClassifier(model_path=args.checkpoint)
    model = classifier.model
    if not isinstance(model, nn.Module):
        raise RuntimeError("FoodClassifier did not load a torch module")
    model = model.to(device).eval()
    if classifier.classes != classes:
        raise ValueError("checkpoint classes differ from provided classes file")

    image_size = int(metadata.get("image_size", classifier.image_size))
    val_ds = datasets.ImageFolder(args.data_dir / args.val_subdir, transform=build_transform(image_size))
    if val_ds.classes != classes:
        raise ValueError("validation class order differs from classes file")
    loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    y_true: list[int] = []
    y_pred: list[int] = []
    top3_correct = 0
    records: list[dict[str, object]] = []
    sample_offset = 0
    num_classes = len(classes)

    with torch.inference_mode():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            if args.tta == "hflip":
                logits = 0.5 * (logits + model(torch.flip(images, dims=[3])))
            probs = torch.softmax(logits, dim=1)
            confs, preds = probs.max(dim=1)
            topk = probs.topk(k=min(3, num_classes), dim=1)
            top3_correct += topk.indices.eq(labels[:, None]).any(dim=1).sum().item()
            batch_true = labels.cpu().tolist()
            batch_pred = preds.cpu().tolist()
            batch_conf = confs.cpu().tolist()
            batch_top_indices = topk.indices.cpu().tolist()
            batch_top_values = topk.values.cpu().tolist()
            y_true.extend(batch_true)
            y_pred.extend(batch_pred)

            for i, (target, pred, conf) in enumerate(zip(batch_true, batch_pred, batch_conf)):
                sample_path = val_ds.samples[sample_offset + i][0]
                top3 = [
                    [classes[idx], float(value)]
                    for idx, value in zip(batch_top_indices[i], batch_top_values[i])
                ]
                records.append({
                    "image_path": sample_path,
                    "true_index": target,
                    "true_class": classes[target],
                    "pred_index": pred,
                    "pred_class": classes[pred],
                    "confidence": float(conf),
                    "top3": json.dumps(top3, ensure_ascii=False),
                    "correct": target == pred,
                })
            sample_offset += len(batch_true)

    top1 = sum(int(a == b) for a, b in zip(y_true, y_pred)) / max(len(y_true), 1)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    metrics = {
        "name": args.name,
        "checkpoint": str(args.checkpoint),
        "metadata": str(args.metadata),
        "classes": str(args.classes),
        "data_dir": str(args.data_dir),
        "val_subdir": args.val_subdir,
        "model_type": classifier.model_type,
        "model_name": classifier.model_name,
        "image_size": image_size,
        "tta": args.tta,
        "val_top1": top1,
        "val_top3": top3_correct / max(len(y_true), 1),
        "macro_f1": macro_f1,
        "num_classes": num_classes,
        "num_samples": len(y_true),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.joinpath("metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_per_class(args.output_dir / "per_class_metrics.csv", classes, y_true, y_pred)
    write_confusion(args.output_dir / "confusion_matrix.csv", classes, y_true, y_pred)
    write_high_confidence_errors(args.output_dir / "high_confidence_errors.csv", classes, records)
    write_readme(args.output_dir, metrics)
    logger.info("metrics=%s", metrics)


if __name__ == "__main__":
    main()
