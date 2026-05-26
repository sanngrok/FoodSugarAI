#!/usr/bin/env python3
"""Evaluate logits-average ensembles for K-Food models."""

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
logger = logging.getLogger("eval_kfood_ensemble")


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


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_transform(image_size: int) -> T.Compose:
    return T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def load_images(paths: list[str], transform: T.Compose, device: torch.device) -> torch.Tensor:
    tensors = []
    for path in paths:
        with Image.open(path) as img:
            tensors.append(transform(img.convert("RGB")))
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
    parser.add_argument("--tta", choices=["none", "hflip"], default="none")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (len(args.checkpoint) == len(args.metadata) == len(args.classes) == len(args.name)):
        raise ValueError("--checkpoint/--metadata/--classes/--name counts must match")

    class_lists = [load_json(path) for path in args.classes]
    if not all(class_lists[0] == item for item in class_lists):
        raise ValueError("class lists differ across models")
    classes = list(class_lists[0])
    num_classes = len(classes)
    device = get_device()

    models: list[nn.Module] = []
    transforms: list[T.Compose] = []
    model_infos: list[dict[str, object]] = []
    for checkpoint, metadata_path, name in zip(args.checkpoint, args.metadata, args.name):
        metadata = load_json(metadata_path)
        classifier = FoodClassifier(model_path=checkpoint)
        model = classifier.model
        if not isinstance(model, nn.Module):
            raise RuntimeError(f"failed to load model: {checkpoint}")
        image_size = int(metadata.get("image_size", classifier.image_size))
        models.append(model.to(device).eval())
        transforms.append(build_transform(image_size))
        model_infos.append({
            "name": name,
            "checkpoint": str(checkpoint),
            "model_type": classifier.model_type,
            "model_name": classifier.model_name,
            "image_size": image_size,
        })
        logger.info("loaded %s: %s", name, model_infos[-1])

    # Use an ImageFolder only to get class order and samples. Per-model transforms
    # are applied manually because ensemble members may have different image sizes.
    image_folder = __import__("torchvision").datasets.ImageFolder(args.data_dir / args.val_subdir)
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

    y_true: list[int] = []
    y_pred: list[int] = []
    records: list[dict[str, object]] = []
    single_true: dict[str, list[int]] = {name: [] for name in args.name}
    single_pred: dict[str, list[int]] = {name: [] for name in args.name}
    top3_correct = 0
    with torch.inference_mode():
        for paths, labels in loader:
            labels = labels.to(device)
            logits_sum = None
            for name, model, transform in zip(args.name, models, transforms):
                images = load_images(paths, transform, device)
                logits = model(images)
                if args.tta == "hflip":
                    logits = 0.5 * (logits + model(torch.flip(images, dims=[3])))
                preds = logits.argmax(dim=1)
                single_true[name].extend(labels.cpu().tolist())
                single_pred[name].extend(preds.cpu().tolist())
                logits_sum = logits if logits_sum is None else logits_sum + logits
            logits_avg = logits_sum / len(models)
            probs = torch.softmax(logits_avg, dim=1)
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

    metrics = {
        "names": args.name,
        "models": model_infos,
        "data_dir": str(args.data_dir),
        "val_subdir": args.val_subdir,
        "tta": args.tta,
        "ensemble_top1": sum(int(a == b) for a, b in zip(y_true, y_pred)) / max(len(y_true), 1),
        "ensemble_top3": top3_correct / max(len(y_true), 1),
        "ensemble_macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "num_classes": num_classes,
        "num_samples": len(y_true),
        "single_models": {},
    }
    for name in args.name:
        st = single_true[name]
        sp = single_pred[name]
        metrics["single_models"][name] = {
            "top1": sum(int(a == b) for a, b in zip(st, sp)) / max(len(st), 1),
            "macro_f1": f1_score(st, sp, average="macro", zero_division=0),
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.joinpath("metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_per_class(args.output_dir / "per_class_metrics.csv", classes, y_true, y_pred)
    write_confusion(args.output_dir / "confusion_matrix.csv", classes, y_true, y_pred)
    write_high_confidence_errors(args.output_dir / "high_confidence_errors.csv", classes, records)
    lines = ["# K-Food Ensemble Evaluation", "", f"- tta: `{args.tta}`"]
    lines.append(f"- ensemble_top1: `{metrics['ensemble_top1']}`")
    lines.append(f"- ensemble_top3: `{metrics['ensemble_top3']}`")
    lines.append(f"- ensemble_macro_f1: `{metrics['ensemble_macro_f1']}`")
    lines.append("")
    lines.append("## Single Models")
    for name, item in metrics["single_models"].items():
        lines.append(f"- {name}: top1=`{item['top1']}`, macro_f1=`{item['macro_f1']}`")
    args.output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("metrics=%s", metrics)


if __name__ == "__main__":
    main()
