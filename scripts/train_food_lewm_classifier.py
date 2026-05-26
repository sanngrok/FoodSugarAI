#!/usr/bin/env python3
"""Fine-tune a Food-LeWM pretrained encoder for 56-class K-Food classification."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from sklearn.metrics import f1_score, precision_recall_fscore_support
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Subset
from torchvision import datasets
import torchvision.transforms as T

from src.classifier.food_lewm_model import (
    FoodLeWMClassifier,
    FoodLeWMConfig,
    get_device,
    load_lewm_encoder_weights,
)


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("train_food_lewm_classifier")


def build_transforms(image_size: int, random_erasing_p: float) -> tuple[T.Compose, T.Compose]:
    train_steps: list[object] = [
        T.RandomResizedCrop(image_size, scale=(0.65, 1.0)),
        T.RandomHorizontalFlip(p=0.5),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.12, hue=0.02),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
    if random_erasing_p > 0:
        train_steps.append(T.RandomErasing(p=random_erasing_p, scale=(0.02, 0.12), ratio=(0.3, 3.3)))
    train_tf = T.Compose(train_steps)
    val_tf = T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    return train_tf, val_tf


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    num_classes: int,
) -> dict[str, object]:
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    top3_correct = 0
    total = 0
    with torch.inference_mode():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            preds = logits.argmax(dim=1)
            topk = logits.topk(k=min(3, num_classes), dim=1).indices
            top3_correct += topk.eq(labels[:, None]).any(dim=1).sum().item()
            total += labels.numel()
            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())

    top1 = sum(int(a == b) for a, b in zip(y_true, y_pred)) / max(len(y_true), 1)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    return {
        "top1": top1,
        "top3": top3_correct / max(total, 1),
        "macro_f1": macro_f1,
        "y_true": y_true,
        "y_pred": y_pred,
    }


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


def write_readme(report_dir: Path, metrics: dict[str, object]) -> None:
    lines = ["# Food-LeWM Classifier Report", ""]
    for key, value in metrics.items():
        lines.append(f"- {key}: `{value}`")
    (report_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def jsonable_args(args: argparse.Namespace) -> dict[str, object]:
    values: dict[str, object] = {}
    for key, value in vars(args).items():
        values[key] = str(value) if isinstance(value, Path) else value
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--train-subdir", type=str, default="train")
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--model-name", type=str, required=True)
    parser.add_argument("--image-size", type=int, required=True)
    parser.add_argument("--latent-dim", type=int, default=192)
    parser.add_argument("--lewm-checkpoint", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--lr", type=float, default=7e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--label-smoothing", type=float, default=0.05)
    parser.add_argument("--warmup-epochs", type=int, default=2)
    parser.add_argument("--random-erasing-p", type=float, default=0.1)
    parser.add_argument("--predictor-dropout", type=float, default=0.1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--classes-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-train-samples", type=int, default=0, help="Limit training samples for smoke tests")
    parser.add_argument("--max-val-samples", type=int, default=0, help="Limit validation samples for smoke tests")
    parser.add_argument("--log-every", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = get_device()

    train_tf, val_tf = build_transforms(args.image_size, args.random_erasing_p)
    train_ds = datasets.ImageFolder(args.data_dir / args.train_subdir, transform=train_tf)
    val_ds = datasets.ImageFolder(args.data_dir / args.val_subdir, transform=val_tf)
    if train_ds.classes != val_ds.classes:
        raise ValueError("train/val class order mismatch")

    classes = train_ds.classes
    num_classes = len(classes)
    train_data = Subset(train_ds, range(min(args.max_train_samples, len(train_ds)))) if args.max_train_samples > 0 else train_ds
    val_data = Subset(val_ds, range(min(args.max_val_samples, len(val_ds)))) if args.max_val_samples > 0 else val_ds
    logger.info("device=%s classes=%d train=%d val=%d", device, num_classes, len(train_data), len(val_data))

    train_loader = DataLoader(
        train_data,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )
    val_loader = DataLoader(
        val_data,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    config = FoodLeWMConfig(
        model_name=args.model_name,
        image_size=args.image_size,
        latent_dim=args.latent_dim,
        predictor_dropout=args.predictor_dropout,
        num_classes=num_classes,
    )
    use_lewm_checkpoint = (
        args.lewm_checkpoint is not None
        and str(args.lewm_checkpoint).strip().lower() not in {"", "none", "null"}
    )
    model = FoodLeWMClassifier(config, pretrained=not use_lewm_checkpoint)
    if use_lewm_checkpoint:
        load_lewm_encoder_weights(model.encoder, args.lewm_checkpoint, device=device, strict=False)
        logger.info("loaded LeWM checkpoint: %s", args.lewm_checkpoint)
    else:
        logger.info("no LeWM checkpoint provided; using ImageNet pretrained encoder")
    model = model.to(device)

    if args.warmup_epochs > 0:
        for param in model.encoder.parameters():
            param.requires_grad = False
        optimizer = AdamW(model.classifier.parameters(), lr=args.lr, weight_decay=args.weight_decay)
        logger.info("warmup: classifier head only for %d epochs", args.warmup_epochs)
    else:
        optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))
    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.classes_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.classes_output.write_text(json.dumps(classes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    log_path = args.report_dir / "train_log.csv"
    best_top1 = 0.0
    best_metrics: dict[str, object] = {}
    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["epoch", "loss", "train_acc", "val_top1", "val_top3", "macro_f1", "lr", "seconds"],
        )
        writer.writeheader()

        for epoch in range(1, args.epochs + 1):
            if args.warmup_epochs > 0 and epoch == args.warmup_epochs + 1:
                for param in model.encoder.parameters():
                    param.requires_grad = True
                optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
                scheduler = CosineAnnealingLR(optimizer, T_max=max(args.epochs - args.warmup_epochs, 1))
                logger.info("epoch=%d unfreeze encoder", epoch)

            model.train()
            started = time.time()
            total_loss = 0.0
            total_correct = 0
            total = 0
            optimizer.zero_grad(set_to_none=True)

            for batch_idx, (images, labels) in enumerate(train_loader, start=1):
                images = images.to(device)
                labels = labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                (loss / args.grad_accum_steps).backward()
                if batch_idx % args.grad_accum_steps == 0 or batch_idx == len(train_loader):
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)

                total_loss += float(loss.detach().cpu())
                total_correct += (logits.argmax(1) == labels).sum().item()
                total += labels.numel()
                if args.log_every > 0 and batch_idx % args.log_every == 0:
                    logger.info(
                        "epoch=%d batch=%d/%d loss=%.4f train_acc=%.4f",
                        epoch, batch_idx, len(train_loader),
                        total_loss / batch_idx, total_correct / max(total, 1),
                    )

            metrics = evaluate(model, val_loader, device, num_classes)
            scheduler.step()
            row = {
                "epoch": epoch,
                "loss": total_loss / len(train_loader),
                "train_acc": total_correct / max(total, 1),
                "val_top1": metrics["top1"],
                "val_top3": metrics["top3"],
                "macro_f1": metrics["macro_f1"],
                "lr": scheduler.get_last_lr()[0],
                "seconds": round(time.time() - started, 2),
            }
            writer.writerow(row)
            f.flush()
            logger.info("epoch=%d summary=%s", epoch, row)

            if float(metrics["top1"]) > best_top1:
                best_top1 = float(metrics["top1"])
                best_metrics = row | {
                    "model_type": "food_lewm_classifier",
                    "model_name": args.model_name,
                    "image_size": args.image_size,
                    "latent_dim": args.latent_dim,
                    "num_classes": num_classes,
                    "lewm_checkpoint": str(args.lewm_checkpoint) if use_lewm_checkpoint else None,
                    "pretrain": "lewm" if use_lewm_checkpoint else "imagenet_supervised_only",
                    "checkpoint": str(args.output),
                    "data_dir": str(args.data_dir),
                    "train_subdir": args.train_subdir,
                    "val_subdir": args.val_subdir,
                }
                torch.save(
                    {
                        "model_state_dict": model.state_dict(),
                        "config": config.__dict__,
                        "classes": classes,
                        "args": jsonable_args(args),
                        "best_metrics": best_metrics,
                    },
                    args.output,
                )
                write_per_class(args.report_dir / "per_class_metrics.csv", classes, metrics["y_true"], metrics["y_pred"])
                logger.info("saved classifier checkpoint: %s", args.output)

    args.metadata_output.write_text(json.dumps(best_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.report_dir / "metrics.json").write_text(json.dumps(best_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(args.report_dir, best_metrics)


if __name__ == "__main__":
    main()
