#!/usr/bin/env python3
"""LeWM-style two-view self-supervised pretraining for K-Food images."""

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
import torch.nn.functional as F
from PIL import Image
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T

from src.classifier.food_lewm_model import FoodLeWMConfig, FoodLeWMEncoder, get_device
from src.classifier.lewm_sigreg import SIGRegLoss


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pretrain_food_lewm")


class ImageRootTwoViewDataset(Dataset):
    def __init__(self, image_root: Path, transform: T.Compose, max_samples: int = 0) -> None:
        self.image_root = image_root
        self.transform = transform
        self.paths = sorted(
            p for p in image_root.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        if max_samples > 0:
            self.paths = self.paths[:max_samples]
        if not self.paths:
            raise FileNotFoundError(f"No images found under {image_root}")

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        path = self.paths[index]
        with Image.open(path) as img:
            image = img.convert("RGB")
            return self.transform(image), self.transform(image)


def build_ssl_transform(image_size: int) -> T.Compose:
    return T.Compose([
        T.RandomResizedCrop(image_size, scale=(0.55, 1.0)),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomApply([T.ColorJitter(0.25, 0.25, 0.15, 0.03)], p=0.8),
        T.RandomGrayscale(p=0.05),
        T.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def write_readme(report_dir: Path, metrics: dict[str, object]) -> None:
    lines = ["# Food-LeWM Pretraining Report", ""]
    for key, value in metrics.items():
        lines.append(f"- {key}: `{value}`")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def jsonable_args(args: argparse.Namespace) -> dict[str, object]:
    values: dict[str, object] = {}
    for key, value in vars(args).items():
        values[key] = str(value) if isinstance(value, Path) else value
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--model-name", type=str, required=True)
    parser.add_argument("--image-size", type=int, required=True)
    parser.add_argument("--latent-dim", type=int, default=192)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--lambda-sigreg", type=float, default=0.1)
    parser.add_argument("--num-projections", type=int, default=256)
    parser.add_argument("--predictor-dropout", type=float, default=0.1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/food_lewm/pretrain"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-samples", type=int, default=0, help="Limit images for smoke tests")
    parser.add_argument("--log-every", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = get_device()
    logger.info("device=%s model=%s image_size=%d", device, args.model_name, args.image_size)

    dataset = ImageRootTwoViewDataset(args.image_root, build_ssl_transform(args.image_size), args.max_samples)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
        drop_last=True,
    )
    logger.info("pretrain images=%d batches=%d", len(dataset), len(loader))

    config = FoodLeWMConfig(
        model_name=args.model_name,
        image_size=args.image_size,
        latent_dim=args.latent_dim,
        predictor_dropout=args.predictor_dropout,
    )
    model = FoodLeWMEncoder(config, pretrained=True).to(device)
    sigreg = SIGRegLoss(args.latent_dim, args.num_projections).to(device)
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.report_dir / "train_log.csv"
    best_loss = float("inf")

    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["epoch", "loss", "prediction_loss", "sigreg_loss", "lr", "seconds"],
        )
        writer.writeheader()

        for epoch in range(1, args.epochs + 1):
            model.train()
            started = time.time()
            total_loss = total_pred = total_sig = 0.0
            optimizer.zero_grad(set_to_none=True)

            for batch_idx, (view_a, view_b) in enumerate(loader, start=1):
                view_a = view_a.to(device)
                view_b = view_b.to(device)
                z_a = model.encode(view_a)
                z_b = model.encode(view_b)
                pred_ab = model.predict_latent(z_a)
                pred_ba = model.predict_latent(z_b)
                prediction_loss = 0.5 * (
                    F.mse_loss(pred_ab, z_b) + F.mse_loss(pred_ba, z_a)
                )
                sigreg_loss = sigreg(z_a, z_b)
                loss = prediction_loss + args.lambda_sigreg * sigreg_loss
                (loss / args.grad_accum_steps).backward()

                if batch_idx % args.grad_accum_steps == 0 or batch_idx == len(loader):
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)

                total_loss += float(loss.detach().cpu())
                total_pred += float(prediction_loss.detach().cpu())
                total_sig += float(sigreg_loss.detach().cpu())

                if args.log_every > 0 and batch_idx % args.log_every == 0:
                    logger.info(
                        "epoch=%d batch=%d/%d loss=%.4f pred=%.4f sig=%.4f",
                        epoch, batch_idx, len(loader),
                        total_loss / batch_idx, total_pred / batch_idx, total_sig / batch_idx,
                    )

            scheduler.step()
            row = {
                "epoch": epoch,
                "loss": total_loss / len(loader),
                "prediction_loss": total_pred / len(loader),
                "sigreg_loss": total_sig / len(loader),
                "lr": scheduler.get_last_lr()[0],
                "seconds": round(time.time() - started, 2),
            }
            writer.writerow(row)
            f.flush()
            logger.info("epoch=%d summary=%s", epoch, row)

            if row["loss"] < best_loss:
                best_loss = float(row["loss"])
                torch.save(
                    {
                        "encoder_state_dict": model.state_dict(),
                        "config": config.__dict__,
                        "args": jsonable_args(args),
                        "epoch": epoch,
                        "best_loss": best_loss,
                    },
                    args.output,
                )
                logger.info("saved pretrain checkpoint: %s", args.output)

    metrics = {
        "model_name": args.model_name,
        "image_size": args.image_size,
        "latent_dim": args.latent_dim,
        "lambda_sigreg": args.lambda_sigreg,
        "num_projections": args.num_projections,
        "pretrain_epochs": args.epochs,
        "images": len(dataset),
        "best_loss": best_loss,
        "checkpoint": str(args.output),
    }
    (args.report_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(args.report_dir, metrics)


if __name__ == "__main__":
    main()
