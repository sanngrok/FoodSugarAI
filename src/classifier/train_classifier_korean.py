"""
EfficientNet 한국 음식 파인튜닝 스크립트.

ImageFolder 형식의 K-Food train/val split을 학습하고, timm classifier
checkpoint 및 리포트를 저장한다.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import ssl
import time
from pathlib import Path

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

import torch
import torch.nn as nn
from sklearn.metrics import f1_score, precision_recall_fscore_support
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision import datasets
import torchvision.transforms as T

try:
    import timm
except ImportError:
    raise ImportError("pip install timm 을 먼저 실행하세요.")

from config.settings import settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_SAVE_PATH = Path("data/models/efficientnet_korean.pt")
CLASSES_SAVE_PATH = Path("data/models/korean_food_classes.json")
METADATA_SAVE_PATH = Path("data/models/korean_food_model_meta.json")

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_transforms(
    image_size: int,
    randaugment_n: int,
    randaugment_m: int,
    random_erasing_p: float,
) -> tuple[T.Compose, T.Compose]:
    train_steps: list[object] = [
        T.RandomResizedCrop(image_size, scale=(0.65, 1.0)),
        T.RandomHorizontalFlip(),
    ]
    if randaugment_n > 0:
        train_steps.append(T.RandAugment(num_ops=randaugment_n, magnitude=randaugment_m))
    else:
        train_steps.extend([
            T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            T.RandomRotation(15),
        ])
    train_steps.extend([
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    if random_erasing_p > 0:
        train_steps.append(T.RandomErasing(p=random_erasing_p, scale=(0.02, 0.12), ratio=(0.3, 3.3)))

    train_transform = T.Compose(train_steps)
    val_transform = T.Compose([
        T.Resize(int(image_size * 1.14)),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    return train_transform, val_transform


def load_datasets(
    data_dir: Path,
    image_size: int,
    randaugment_n: int,
    randaugment_m: int,
    random_erasing_p: float,
    train_subdir: str = "train",
    val_subdir: str = "val",
) -> tuple[datasets.ImageFolder, datasets.ImageFolder]:
    train_dir = data_dir / train_subdir
    val_dir = data_dir / val_subdir
    if not train_dir.exists():
        raise FileNotFoundError(f"{train_dir} 없음.")
    if not val_dir.exists():
        raise FileNotFoundError(f"{val_dir} 없음.")

    train_transform, val_transform = build_transforms(
        image_size=image_size,
        randaugment_n=randaugment_n,
        randaugment_m=randaugment_m,
        random_erasing_p=random_erasing_p,
    )
    train_ds = datasets.ImageFolder(train_dir, transform=train_transform)
    val_ds = datasets.ImageFolder(val_dir, transform=val_transform)
    if train_ds.classes != val_ds.classes:
        raise ValueError("train/val class order mismatch")
    return train_ds, val_ds


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, num_classes: int) -> dict[str, object]:
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    top3_correct = 0
    total = 0
    with torch.inference_mode():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            preds = logits.argmax(dim=1)
            topk = logits.topk(k=min(3, num_classes), dim=1).indices
            top3_correct += topk.eq(labels[:, None]).any(dim=1).sum().item()
            total += labels.numel()
            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())

    top1 = sum(int(a == b) for a, b in zip(y_true, y_pred)) / max(len(y_true), 1)
    return {
        "top1": top1,
        "top3": top3_correct / max(total, 1),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
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

    path.parent.mkdir(parents=True, exist_ok=True)
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


def jsonable_args(args: argparse.Namespace | dict[str, object]) -> dict[str, object]:
    raw = vars(args) if isinstance(args, argparse.Namespace) else args
    values: dict[str, object] = {}
    for key, value in raw.items():
        values[key] = str(value) if isinstance(value, Path) else value
    return values


def write_readme(report_dir: Path, metrics: dict[str, object]) -> None:
    lines = ["# Korean Food Classifier Training", ""]
    for key, value in metrics.items():
        lines.append(f"- {key}: `{value}`")
    (report_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_state_dict(path: Path, device: torch.device):
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(path, map_location=device)
    except Exception:
        checkpoint = torch.load(path, map_location=device, weights_only=False)
    if isinstance(checkpoint, dict):
        if isinstance(checkpoint.get("model_state_dict"), dict):
            return checkpoint["model_state_dict"]
        if isinstance(checkpoint.get("state_dict"), dict):
            return checkpoint["state_dict"]
    return checkpoint


def train(
    data_dir: str | Path,
    epochs: int = 15,
    batch_size: int = 32,
    lr: float = 1e-4,
    num_workers: int = 4,
    warmup_epochs: int = 3,
    model_save_path: str | Path = MODEL_SAVE_PATH,
    classes_save_path: str | Path = CLASSES_SAVE_PATH,
    metadata_save_path: str | Path = METADATA_SAVE_PATH,
    model_name: str = "efficientnet_b0",
    image_size: int = settings.image_size,
    log_every: int = 100,
    resume_from: str | Path | None = None,
    initial_best_acc: float = 0.0,
    label_smoothing: float = 0.1,
    weight_decay: float = 0.01,
    randaugment_n: int = 0,
    randaugment_m: int = 9,
    random_erasing_p: float = 0.0,
    drop_rate: float = 0.0,
    drop_path_rate: float = 0.0,
    grad_accum_steps: int = 1,
    report_dir: str | Path | None = None,
    seed: int = 42,
    train_subdir: str = "train",
    val_subdir: str = "val",
    head_lr: float | None = None,
    args_dict: dict[str, object] | None = None,
) -> None:
    data_dir = Path(data_dir)
    model_save_path = Path(model_save_path)
    classes_save_path = Path(classes_save_path)
    metadata_save_path = Path(metadata_save_path)
    report_path = Path(report_dir) if report_dir else metadata_save_path.with_suffix("")
    grad_accum_steps = max(1, grad_accum_steps)

    random.seed(seed)
    torch.manual_seed(seed)
    device = get_device()
    logger.info("학습 장치: %s", device)
    logger.info("모델: %s / image_size=%d", model_name, image_size)

    train_ds, val_ds = load_datasets(
        data_dir=data_dir,
        image_size=image_size,
        randaugment_n=randaugment_n,
        randaugment_m=randaugment_m,
        random_erasing_p=random_erasing_p,
        train_subdir=train_subdir,
        val_subdir=val_subdir,
    )
    num_classes = len(train_ds.classes)
    logger.info("클래스 수: %d개", num_classes)
    logger.info("학습 이미지: %d장 / 검증 이미지: %d장", len(train_ds), len(val_ds))

    classes_save_path.parent.mkdir(parents=True, exist_ok=True)
    classes_save_path.write_text(
        json.dumps(train_ds.classes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.info("클래스 목록 저장: %s", classes_save_path)

    metadata_save_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.mkdir(parents=True, exist_ok=True)

    pin_memory = device.type == "cuda"
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    resume_path = Path(resume_from) if resume_from else None
    use_pretrained = not (resume_path and resume_path.exists())
    model = timm.create_model(
        model_name,
        pretrained=use_pretrained,
        num_classes=num_classes,
        drop_rate=drop_rate,
        drop_path_rate=drop_path_rate,
    )
    if resume_path and resume_path.exists():
        model.load_state_dict(_load_state_dict(resume_path, device))
        logger.info("기존 checkpoint 로드: %s", resume_path)
    model = model.to(device)

    if warmup_epochs > 0:
        for param in model.parameters():
            param.requires_grad = False
        for param in model.get_classifier().parameters():
            param.requires_grad = True
        optimizer = AdamW(model.get_classifier().parameters(), lr=head_lr or lr, weight_decay=weight_decay)
        logger.info("Warmup 시작: classifier head만 학습 (%d epoch)", warmup_epochs)
    else:
        for param in model.parameters():
            param.requires_grad = True
        optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        logger.info("Warmup 생략: 전체 파라미터 학습")

    scheduler = CosineAnnealingLR(optimizer, T_max=max(epochs, 1))
    criterion = nn.CrossEntropyLoss(label_smoothing=label_smoothing)

    best_acc = initial_best_acc
    best_metrics: dict[str, object] = {}
    model_save_path.parent.mkdir(parents=True, exist_ok=True)
    if best_acc > 0:
        logger.info("초기 best 검증 정확도: %.4f", best_acc)

    train_log_path = report_path / "train_log.csv"
    with train_log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["epoch", "loss", "train_acc", "val_top1", "val_top3", "macro_f1", "lr", "seconds"],
        )
        writer.writeheader()

        for epoch in range(1, epochs + 1):
            if warmup_epochs > 0 and epoch == warmup_epochs + 1:
                for param in model.parameters():
                    param.requires_grad = True
                optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
                scheduler = CosineAnnealingLR(optimizer, T_max=max(epochs - warmup_epochs, 1))
                logger.info("Epoch %d: 전체 파라미터 unfreeze (lr=%.2e)", epoch, lr)

            model.train()
            started = time.time()
            total_loss = 0.0
            total_correct = 0
            total = 0
            optimizer.zero_grad(set_to_none=True)

            for batch_idx, (images, labels) in enumerate(train_loader, start=1):
                images, labels = images.to(device), labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                (loss / grad_accum_steps).backward()
                if batch_idx % grad_accum_steps == 0 or batch_idx == len(train_loader):
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)

                total_loss += float(loss.detach().cpu())
                total_correct += (logits.argmax(1) == labels).sum().item()
                total += labels.numel()
                if log_every > 0 and batch_idx % log_every == 0:
                    logger.info(
                        "Epoch %2d/%d | batch %4d/%d | loss=%.4f | train_acc=%.4f",
                        epoch,
                        epochs,
                        batch_idx,
                        len(train_loader),
                        total_loss / batch_idx,
                        total_correct / max(total, 1),
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

            if float(metrics["top1"]) > best_acc:
                best_acc = float(metrics["top1"])
                best_metrics = {
                    **row,
                    "model_type": "timm_classifier",
                    "model_name": model_name,
                    "image_size": image_size,
                    "num_classes": num_classes,
                    "checkpoint": str(model_save_path),
                    "data_dir": str(data_dir),
                    "train_subdir": train_subdir,
                    "val_subdir": val_subdir,
                    "best_val_acc": best_acc,
                    "best_macro_f1": metrics["macro_f1"],
                    "args": args_dict or {
                        "label_smoothing": label_smoothing,
                        "weight_decay": weight_decay,
                        "randaugment_n": randaugment_n,
                        "randaugment_m": randaugment_m,
                        "random_erasing_p": random_erasing_p,
                        "drop_rate": drop_rate,
                        "drop_path_rate": drop_path_rate,
                        "grad_accum_steps": grad_accum_steps,
                        "seed": seed,
                        "head_lr": head_lr,
                    },
                }
                torch.save(model.state_dict(), model_save_path)
                write_per_class(report_path / "per_class_metrics.csv", train_ds.classes, metrics["y_true"], metrics["y_pred"])
                logger.info("  -> 모델 저장 (val_acc=%.4f): %s", best_acc, model_save_path)

    metadata_save_path.write_text(json.dumps(best_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (report_path / "metrics.json").write_text(json.dumps(best_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(report_path, best_metrics)
    logger.info("학습 완료. 최고 검증 정확도: %.4f", best_acc)
    logger.info("모델: %s", model_save_path)
    logger.info("클래스: %s", classes_save_path)
    logger.info("리포트: %s", report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EfficientNet 한국 음식 파인튜닝")
    parser.add_argument("--data-dir", type=str, default="data/raw/korean_food")
    parser.add_argument("--train-subdir", type=str, default="train")
    parser.add_argument("--val-subdir", type=str, default="val")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--head-lr", type=float, default=None)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--warmup-epochs", type=int, default=3)
    parser.add_argument("--model-save-path", type=str, default=str(MODEL_SAVE_PATH))
    parser.add_argument("--classes-save-path", type=str, default=str(CLASSES_SAVE_PATH))
    parser.add_argument("--metadata-save-path", type=str, default=str(METADATA_SAVE_PATH))
    parser.add_argument("--model-name", type=str, default="efficientnet_b0")
    parser.add_argument("--image-size", type=int, default=settings.image_size)
    parser.add_argument("--log-every", type=int, default=100)
    parser.add_argument("--resume-from", type=str, default=None)
    parser.add_argument("--initial-best-acc", type=float, default=0.0)
    parser.add_argument("--label-smoothing", type=float, default=0.1)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--randaugment-n", type=int, default=0)
    parser.add_argument("--randaugment-m", type=int, default=9)
    parser.add_argument("--random-erasing-p", type=float, default=0.0)
    parser.add_argument("--drop-rate", type=float, default=0.0)
    parser.add_argument("--drop-path-rate", type=float, default=0.0)
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--report-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(
        data_dir=args.data_dir,
        train_subdir=args.train_subdir,
        val_subdir=args.val_subdir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        head_lr=args.head_lr,
        num_workers=args.num_workers,
        warmup_epochs=args.warmup_epochs,
        model_save_path=args.model_save_path,
        classes_save_path=args.classes_save_path,
        metadata_save_path=args.metadata_save_path,
        model_name=args.model_name,
        image_size=args.image_size,
        log_every=args.log_every,
        resume_from=args.resume_from,
        initial_best_acc=args.initial_best_acc,
        label_smoothing=args.label_smoothing,
        weight_decay=args.weight_decay,
        randaugment_n=args.randaugment_n,
        randaugment_m=args.randaugment_m,
        random_erasing_p=args.random_erasing_p,
        drop_rate=args.drop_rate,
        drop_path_rate=args.drop_path_rate,
        grad_accum_steps=args.grad_accum_steps,
        report_dir=args.report_dir,
        seed=args.seed,
        args_dict=jsonable_args(args),
    )
