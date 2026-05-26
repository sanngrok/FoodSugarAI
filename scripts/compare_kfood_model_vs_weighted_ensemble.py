#!/usr/bin/env python3
"""Compare one K-Food model against a weighted ensemble on an ImageFolder split."""

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
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T

from src.classifier.food_classifier import FoodClassifier


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("compare_kfood_model_vs_weighted_ensemble")


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
    tensors = []
    for path in paths:
        with Image.open(path) as img:
            tensors.append(transform(img.convert("RGB")))
    return torch.stack(tensors).to(device)


def load_model(checkpoint: Path, metadata_path: Path, device: torch.device) -> tuple[nn.Module, T.Compose, dict[str, Any]]:
    metadata = load_json(metadata_path)
    if not isinstance(metadata, dict):
        raise ValueError(f"metadata must be an object: {metadata_path}")
    classifier = FoodClassifier(model_path=checkpoint)
    model = classifier.model
    if not isinstance(model, nn.Module):
        raise RuntimeError(f"failed to load torch module: {checkpoint}")
    image_size = int(metadata.get("image_size", classifier.image_size))
    info = {
        "checkpoint": str(checkpoint),
        "metadata": str(metadata_path),
        "model_type": classifier.model_type,
        "model_name": classifier.model_name,
        "image_size": image_size,
    }
    return model.to(device).eval(), build_transform(image_size), info


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "image_path",
        "true_class",
        "target_pred",
        "target_confidence",
        "ensemble_pred",
        "ensemble_confidence",
        "target_top3",
        "ensemble_top3",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})


def write_per_class_delta(
    path: Path,
    classes: list[str],
    y_true: list[int],
    target_pred: list[int],
    ensemble_pred: list[int],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_index",
                "class_name",
                "support",
                "target_correct",
                "ensemble_correct",
                "target_accuracy",
                "ensemble_accuracy",
                "delta_accuracy",
            ],
        )
        writer.writeheader()
        for idx, class_name in enumerate(classes):
            indices = [i for i, target in enumerate(y_true) if target == idx]
            support = len(indices)
            target_correct = sum(1 for i in indices if target_pred[i] == y_true[i])
            ensemble_correct = sum(1 for i in indices if ensemble_pred[i] == y_true[i])
            target_acc = target_correct / support if support else 0.0
            ensemble_acc = ensemble_correct / support if support else 0.0
            writer.writerow({
                "class_index": idx,
                "class_name": class_name,
                "support": support,
                "target_correct": target_correct,
                "ensemble_correct": ensemble_correct,
                "target_accuracy": target_acc,
                "ensemble_accuracy": ensemble_acc,
                "delta_accuracy": target_acc - ensemble_acc,
            })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--target-checkpoint", type=Path, required=True)
    parser.add_argument("--target-metadata", type=Path, required=True)
    parser.add_argument("--target-classes", type=Path, required=True)
    parser.add_argument("--target-name", type=str, required=True)
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--metadata", type=Path, action="append", required=True)
    parser.add_argument("--classes", type=Path, action="append", required=True)
    parser.add_argument("--name", type=str, action="append", required=True)
    parser.add_argument("--weight", type=float, action="append", required=True)
    parser.add_argument("--tta", choices=["none", "hflip"], default="hflip")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def top3_json(classes: list[str], probs: torch.Tensor, row_idx: int) -> str:
    topk = probs[row_idx].topk(k=min(3, len(classes)))
    rows = [[classes[idx], float(value)] for idx, value in zip(topk.indices.cpu().tolist(), topk.values.cpu().tolist())]
    return json.dumps(rows, ensure_ascii=False)


def main() -> None:
    args = parse_args()
    if not (len(args.checkpoint) == len(args.metadata) == len(args.classes) == len(args.name) == len(args.weight)):
        raise ValueError("--checkpoint/--metadata/--classes/--name/--weight counts must match")

    target_classes = load_json(args.target_classes)
    class_lists = [load_json(path) for path in args.classes]
    if not isinstance(target_classes, list):
        raise ValueError("target classes JSON must be a list")
    if not all(target_classes == item for item in class_lists):
        raise ValueError("class lists differ across target/ensemble models")
    classes = list(target_classes)
    num_classes = len(classes)

    weight_sum = sum(args.weight)
    if weight_sum <= 0:
        raise ValueError("sum of weights must be positive")
    weights = [weight / weight_sum for weight in args.weight]

    device = get_device()
    target_model, target_transform, target_info = load_model(args.target_checkpoint, args.target_metadata, device)
    ensemble_models: list[nn.Module] = []
    ensemble_transforms: list[T.Compose] = []
    ensemble_infos: list[dict[str, object]] = []
    for checkpoint, metadata_path, name, weight in zip(args.checkpoint, args.metadata, args.name, weights):
        model, transform, info = load_model(checkpoint, metadata_path, device)
        info.update({"name": name, "weight": weight})
        ensemble_models.append(model)
        ensemble_transforms.append(transform)
        ensemble_infos.append(info)
        logger.info("loaded ensemble member %s: %s", name, info)
    logger.info("loaded target %s: %s", args.target_name, target_info)

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
    target_pred: list[int] = []
    ensemble_pred: list[int] = []
    b3_correct_current_wrong: list[dict[str, object]] = []
    current_correct_b3_wrong: list[dict[str, object]] = []
    both_wrong: list[dict[str, object]] = []

    with torch.inference_mode():
        for paths, labels in loader:
            labels = labels.to(device)
            target_images = load_images(paths, target_transform, device)
            target_logits = target_model(target_images)
            if args.tta == "hflip":
                target_logits = 0.5 * (target_logits + target_model(torch.flip(target_images, dims=[3])))
            target_probs = torch.softmax(target_logits, dim=1)
            target_confs, target_batch_pred = target_probs.max(dim=1)

            ensemble_logits = None
            for model, transform, weight in zip(ensemble_models, ensemble_transforms, weights):
                images = load_images(paths, transform, device)
                logits = model(images)
                if args.tta == "hflip":
                    logits = 0.5 * (logits + model(torch.flip(images, dims=[3])))
                weighted = logits * weight
                ensemble_logits = weighted if ensemble_logits is None else ensemble_logits + weighted
            ensemble_probs = torch.softmax(ensemble_logits, dim=1)
            ensemble_confs, ensemble_batch_pred = ensemble_probs.max(dim=1)

            batch_true = labels.cpu().tolist()
            batch_target_pred = target_batch_pred.cpu().tolist()
            batch_ensemble_pred = ensemble_batch_pred.cpu().tolist()
            batch_target_conf = target_confs.cpu().tolist()
            batch_ensemble_conf = ensemble_confs.cpu().tolist()

            y_true.extend(batch_true)
            target_pred.extend(batch_target_pred)
            ensemble_pred.extend(batch_ensemble_pred)

            for i, (path, true_idx, tp, ep, tc, ec) in enumerate(
                zip(paths, batch_true, batch_target_pred, batch_ensemble_pred, batch_target_conf, batch_ensemble_conf)
            ):
                target_correct = tp == true_idx
                ensemble_correct = ep == true_idx
                row = {
                    "image_path": path,
                    "true_class": classes[true_idx],
                    "target_pred": classes[tp],
                    "target_confidence": float(tc),
                    "ensemble_pred": classes[ep],
                    "ensemble_confidence": float(ec),
                    "target_top3": top3_json(classes, target_probs, i),
                    "ensemble_top3": top3_json(classes, ensemble_probs, i),
                }
                if target_correct and not ensemble_correct:
                    b3_correct_current_wrong.append(row)
                elif ensemble_correct and not target_correct:
                    current_correct_b3_wrong.append(row)
                elif not target_correct and not ensemble_correct:
                    both_wrong.append(row)

    target_top1 = sum(int(a == b) for a, b in zip(y_true, target_pred)) / max(len(y_true), 1)
    ensemble_top1 = sum(int(a == b) for a, b in zip(y_true, ensemble_pred)) / max(len(y_true), 1)
    metrics = {
        "target_name": args.target_name,
        "target": target_info,
        "ensemble_models": ensemble_infos,
        "data_dir": str(args.data_dir),
        "val_subdir": args.val_subdir,
        "tta": args.tta,
        "num_classes": num_classes,
        "num_samples": len(y_true),
        "target_top1": target_top1,
        "target_macro_f1": f1_score(y_true, target_pred, average="macro", zero_division=0),
        "ensemble_top1": ensemble_top1,
        "ensemble_macro_f1": f1_score(y_true, ensemble_pred, average="macro", zero_division=0),
        "target_correct_ensemble_wrong": len(b3_correct_current_wrong),
        "ensemble_correct_target_wrong": len(current_correct_b3_wrong),
        "both_wrong": len(both_wrong),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.joinpath("metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_rows(args.output_dir / "b3_correct_current_wrong.csv", b3_correct_current_wrong)
    write_rows(args.output_dir / "current_correct_b3_wrong.csv", current_correct_b3_wrong)
    write_rows(args.output_dir / "both_wrong.csv", both_wrong)
    write_per_class_delta(args.output_dir / "per_class_delta.csv", classes, y_true, target_pred, ensemble_pred)

    lines = [
        "# B3 vs Current Weighted Ensemble",
        "",
        f"- target_name: `{args.target_name}`",
        f"- data_dir: `{args.data_dir}`",
        f"- val_subdir: `{args.val_subdir}`",
        f"- tta: `{args.tta}`",
        f"- target_top1: `{target_top1}`",
        f"- ensemble_top1: `{ensemble_top1}`",
        f"- target_correct_ensemble_wrong: `{len(b3_correct_current_wrong)}`",
        f"- ensemble_correct_target_wrong: `{len(current_correct_b3_wrong)}`",
        f"- both_wrong: `{len(both_wrong)}`",
        "",
        "## Files",
        "",
        "- `b3_correct_current_wrong.csv`",
        "- `current_correct_b3_wrong.csv`",
        "- `both_wrong.csv`",
        "- `per_class_delta.csv`",
    ]
    args.output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("metrics=%s", metrics)


if __name__ == "__main__":
    main()
