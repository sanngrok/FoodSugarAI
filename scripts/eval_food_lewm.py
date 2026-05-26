#!/usr/bin/env python3
"""Evaluate one or more Food-LeWM classifiers with optional hflip TTA."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from torch.utils.data import DataLoader, Subset
from torchvision import datasets
import torchvision.transforms as T

from src.classifier.food_lewm_model import (
    FoodLeWMClassifier,
    FoodLeWMConfig,
    get_device,
    load_classifier_weights,
)


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("eval_food_lewm")


def build_transform(image_size: int) -> T.Compose:
    return T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_value(metadata: dict[str, object], key: str, default: object) -> object:
    if key in metadata:
        return metadata[key]
    config = metadata.get("config")
    if isinstance(config, dict) and key in config:
        return config[key]
    return default


def model_type_from_metadata(metadata: dict[str, object]) -> str:
    value = metadata.get("model_type")
    if isinstance(value, str):
        return value
    if "latent_dim" in metadata and "lewm_checkpoint" in metadata:
        return "food_lewm_classifier"
    return "food_lewm_classifier"


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


def write_readme(path: Path, metrics: dict[str, object]) -> None:
    lines = ["# Food-LeWM Evaluation Report", ""]
    for key, value in metrics.items():
        lines.append(f"- {key}: `{value}`")
    (path / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--metadata", type=Path, action="append", required=True)
    parser.add_argument("--classes", type=Path, action="append", required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--tta", choices=["none", "hflip"], default="none")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=0, help="Limit validation samples for smoke tests")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (len(args.checkpoint) == len(args.metadata) == len(args.classes)):
        raise ValueError("--checkpoint, --metadata, and --classes counts must match")

    device = get_device()
    class_lists = [load_json(path) for path in args.classes]
    if not all(class_lists[0] == item for item in class_lists):
        raise ValueError("class lists differ across checkpoints")
    classes = list(class_lists[0])
    num_classes = len(classes)

    metadatas = [load_json(path) for path in args.metadata]
    if not all(isinstance(item, dict) for item in metadatas):
        raise ValueError("metadata files must contain JSON objects")

    models: list[FoodLeWMClassifier] = []
    image_sizes: list[int] = []
    for checkpoint, metadata in zip(args.checkpoint, metadatas):
        meta = metadata if isinstance(metadata, dict) else {}
        model_name = str(metadata_value(meta, "model_name", "efficientnet_b0"))
        image_size = int(metadata_value(meta, "image_size", 224))
        latent_dim = int(metadata_value(meta, "latent_dim", 192))
        image_sizes.append(image_size)
        config = FoodLeWMConfig(
            model_name=model_name,
            image_size=image_size,
            latent_dim=latent_dim,
            num_classes=num_classes,
        )
        model = FoodLeWMClassifier(config, pretrained=False).to(device)
        load_classifier_weights(model, checkpoint, device)
        model.eval()
        models.append(model)
        logger.info("loaded %s model=%s image_size=%d", checkpoint, model_name, image_size)

    if len(set(image_sizes)) != 1:
        logger.warning("mixed image sizes in ensemble: %s; using max image_size for dataset transform", image_sizes)
    image_size = max(image_sizes)
    val_ds = datasets.ImageFolder(args.data_dir / "val", transform=build_transform(image_size))
    if val_ds.classes != classes:
        raise ValueError("validation class order differs from checkpoint classes")
    val_data = Subset(val_ds, range(min(args.max_samples, len(val_ds)))) if args.max_samples > 0 else val_ds
    loader = DataLoader(
        val_data,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    y_true: list[int] = []
    y_pred: list[int] = []
    top3_correct = 0
    total = 0
    with torch.inference_mode():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits_sum = None
            for model in models:
                logits = model(images)
                if args.tta == "hflip":
                    logits = 0.5 * (logits + model(torch.flip(images, dims=[3])))
                logits_sum = logits if logits_sum is None else logits_sum + logits
            logits_avg = logits_sum / len(models)
            preds = logits_avg.argmax(dim=1)
            topk = logits_avg.topk(k=min(3, num_classes), dim=1).indices
            top3_correct += topk.eq(labels[:, None]).any(dim=1).sum().item()
            total += labels.numel()
            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())

    top1 = sum(int(a == b) for a, b in zip(y_true, y_pred)) / max(len(y_true), 1)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    metrics = {
        "checkpoints": [str(path) for path in args.checkpoint],
        "data_dir": str(args.data_dir),
        "num_models": len(models),
        "tta": args.tta,
        "val_top1": top1,
        "val_top3": top3_correct / max(total, 1),
        "macro_f1": macro_f1,
        "num_classes": num_classes,
        "num_samples": len(y_true),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_per_class(args.output_dir / "per_class_metrics.csv", classes, y_true, y_pred)
    write_confusion(args.output_dir / "confusion_matrix.csv", classes, y_true, y_pred)
    write_readme(args.output_dir, metrics)
    logger.info("metrics=%s", metrics)


if __name__ == "__main__":
    main()
