#!/usr/bin/env python3
"""Evaluate a fixed-weight K-Food ensemble with optional fivefold TTA."""

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

from PIL import Image
import torch
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from torch import nn
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T

from src.classifier.food_classifier import FoodClassifier


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("eval_fixed_weight_ensemble")


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


def normalize_weights(weights: list[float]) -> list[float]:
    total = sum(weights)
    if total <= 0:
        raise ValueError("sum of weights must be positive")
    return [weight / total for weight in weights]


def base_transform(image_size: int) -> T.Compose:
    return T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def zoom_center_transform(image_size: int, scale: float) -> T.Compose:
    crop_size = max(1, round(image_size * scale))
    return T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(crop_size),
        T.Resize(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def larger_resize_transform(image_size: int) -> T.Compose:
    return T.Compose([
        T.Resize(int(image_size * 1.25)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_tta_transforms(image_size: int, tta: str) -> list[tuple[str, T.Compose, bool]]:
    base = base_transform(image_size)
    if tta == "none":
        return [("original", base, False)]
    if tta == "hflip":
        return [("original", base, False), ("hflip", base, True)]
    if tta == "fivefold":
        return [
            ("original", base, False),
            ("hflip", base, True),
            ("center_crop_scale_090", zoom_center_transform(image_size, 0.90), False),
            ("center_crop_scale_095", zoom_center_transform(image_size, 0.95), False),
            ("larger_resize_center_crop", larger_resize_transform(image_size), False),
        ]
    raise ValueError(f"unsupported tta: {tta}")


def load_images(paths: list[str], transform: T.Compose, device: torch.device, hflip: bool = False) -> torch.Tensor:
    tensors = []
    for path in paths:
        with Image.open(path) as img:
            tensor = transform(img.convert("RGB"))
            if hflip:
                tensor = torch.flip(tensor, dims=[2])
            tensors.append(tensor)
    return torch.stack(tensors).to(device)


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
    fieldnames = [
        "image_path",
        "true_index",
        "true_class",
        "pred_index",
        "pred_class",
        "confidence",
        "top3",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--metadata", type=Path, action="append", required=True)
    parser.add_argument("--classes", type=Path, action="append", required=True)
    parser.add_argument("--name", type=str, action="append", required=True)
    parser.add_argument("--weight", type=float, action="append", required=True)
    parser.add_argument("--tta", choices=["none", "hflip", "fivefold"], default="hflip")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (len(args.checkpoint) == len(args.metadata) == len(args.classes) == len(args.name) == len(args.weight)):
        raise ValueError("--checkpoint/--metadata/--classes/--name/--weight counts must match")

    class_lists = [load_json(path) for path in args.classes]
    if not all(class_lists[0] == class_list for class_list in class_lists):
        raise ValueError("class lists differ across models")
    classes = list(class_lists[0])
    num_classes = len(classes)
    weights = normalize_weights(args.weight)
    device = get_device()

    models: list[nn.Module] = []
    tta_transforms: list[list[tuple[str, T.Compose, bool]]] = []
    model_infos: list[dict[str, object]] = []
    for checkpoint, metadata_path, name, weight in zip(args.checkpoint, args.metadata, args.name, weights):
        metadata = load_json(metadata_path)
        if not isinstance(metadata, dict):
            raise ValueError(f"metadata must be an object: {metadata_path}")
        classifier = FoodClassifier(model_path=checkpoint)
        if classifier.classes != classes:
            raise ValueError(f"class list mismatch for {checkpoint}")
        model = classifier.model
        if not isinstance(model, nn.Module):
            raise RuntimeError(f"failed to load model: {checkpoint}")
        image_size = int(metadata.get("image_size", classifier.image_size))
        models.append(model.to(device).eval())
        tta_transforms.append(build_tta_transforms(image_size, args.tta))
        model_infos.append({
            "name": name,
            "checkpoint": str(checkpoint),
            "metadata": str(metadata_path),
            "model_type": classifier.model_type,
            "model_name": classifier.model_name,
            "image_size": image_size,
            "weight": weight,
        })
        logger.info("loaded %s image_size=%d weight=%.6f", name, image_size, weight)

    image_folder = __import__("torchvision").datasets.ImageFolder(args.data_dir / args.val_subdir)
    if image_folder.classes != classes:
        raise ValueError("validation class order differs from model classes")
    loader = DataLoader(
        PathImageDataset(image_folder.samples),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_paths,
        pin_memory=device.type == "cuda",
    )

    y_true: list[int] = []
    y_pred: list[int] = []
    top3_correct = 0
    records: list[dict[str, object]] = []
    with torch.inference_mode():
        for batch_idx, (paths, labels) in enumerate(loader, start=1):
            labels = labels.to(device)
            weighted_sum = None
            for model, transforms, weight in zip(models, tta_transforms, weights):
                model_logits = None
                for _, transform, hflip in transforms:
                    images = load_images(paths, transform, device, hflip=hflip)
                    logits = model(images)
                    model_logits = logits if model_logits is None else model_logits + logits
                model_logits = model_logits / len(transforms)
                weighted = model_logits * weight
                weighted_sum = weighted if weighted_sum is None else weighted_sum + weighted

            probs = torch.softmax(weighted_sum, dim=1)
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
            for path, target, pred, conf, top_indices, top_values in zip(
                paths,
                batch_true,
                batch_pred,
                batch_conf,
                batch_top_indices,
                batch_top_values,
            ):
                top3 = [
                    [classes[idx], float(value)]
                    for idx, value in zip(top_indices, top_values)
                ]
                records.append({
                    "image_path": path,
                    "true_index": target,
                    "true_class": classes[target],
                    "pred_index": pred,
                    "pred_class": classes[pred],
                    "confidence": float(conf),
                    "top3": json.dumps(top3, ensure_ascii=False),
                    "correct": target == pred,
                })
            if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == len(loader):
                logger.info("evaluated batch %s/%s", batch_idx, len(loader))

    top1 = sum(int(a == b) for a, b in zip(y_true, y_pred)) / max(len(y_true), 1)
    metrics = {
        "names": args.name,
        "models": model_infos,
        "weights": {name: weight for name, weight in zip(args.name, weights)},
        "data_dir": str(args.data_dir),
        "val_subdir": args.val_subdir,
        "tta": args.tta,
        "top1": top1,
        "top3": top3_correct / max(len(y_true), 1),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
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
    lines = [
        "# Fixed-Weight K-Food Ensemble Evaluation",
        "",
        f"- data_dir: `{args.data_dir}`",
        f"- val_subdir: `{args.val_subdir}`",
        f"- tta: `{args.tta}`",
        f"- top1: `{metrics['top1']}`",
        f"- top3: `{metrics['top3']}`",
        f"- macro_f1: `{metrics['macro_f1']}`",
        "",
        "## Weights",
        "",
    ]
    for name, weight in metrics["weights"].items():
        lines.append(f"- {name}: `{weight}`")
    args.output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("metrics=%s", metrics)


if __name__ == "__main__":
    main()
