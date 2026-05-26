"""
EfficientNet-B0 Fine-tuning 스크립트 (Food-101)

사용법:
    python -m src.classifier.train_classifier \
        --data-dir /path/to/food101 \
        --epochs 10 \
        --batch-size 64 \
        --lr 1e-4
"""

import argparse
import logging
import os
import ssl
from pathlib import Path

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision.datasets import Food101
import torchvision.transforms as T

from config.settings import settings
from src.classifier.food_classifier import build_model, TRANSFORM

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TRAIN_TRANSFORM = T.Compose([
    T.RandomResizedCrop(settings.image_size, scale=(0.7, 1.0)),
    T.RandomHorizontalFlip(),
    T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def train(
    data_dir: str,
    epochs: int = 10,
    batch_size: int = 64,
    lr: float = 1e-4,
    num_workers: int = 4,
) -> None:
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    logger.info("학습 장치: %s", device)

    # MPS는 pin_memory 미지원
    pin_memory = device.type == "cuda"

    # 데이터셋
    train_ds = Food101(data_dir, split="train", transform=TRAIN_TRANSFORM, download=True)
    val_ds = Food101(data_dir, split="test", transform=TRANSFORM, download=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=num_workers, pin_memory=pin_memory)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=num_workers, pin_memory=pin_memory)

    model = build_model(num_classes=101, pretrained=True).to(device)

    # 헤드만 먼저 워밍업 (feature freeze)
    for p in model.parameters():
        p.requires_grad = False
    for p in model.get_classifier().parameters():
        p.requires_grad = True

    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    best_acc = 0.0
    save_path = settings.classifier_model_path
    save_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        # 3 에포크 이후 전체 파라미터 unfreeze
        if epoch == 3:
            for p in model.parameters():
                p.requires_grad = True
            optimizer = AdamW(model.parameters(), lr=lr / 10)
            scheduler = CosineAnnealingLR(optimizer, T_max=epochs - 2)
            logger.info("전체 파라미터 unfreeze")

        model.train()
        total_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # 검증
        model.eval()
        correct = 0
        with torch.inference_mode():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                preds = model(images).argmax(dim=1)
                correct += (preds == labels).sum().item()

        acc = correct / len(val_ds)
        scheduler.step()
        logger.info("Epoch %d/%d | loss=%.4f | val_acc=%.4f",
                    epoch, epochs, total_loss / len(train_loader), acc)

        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), save_path)
            logger.info("  -> 모델 저장: %s (acc=%.4f)", save_path, best_acc)

    logger.info("학습 완료. 최고 정확도: %.4f", best_acc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EfficientNet-B0 Food-101 Fine-tuning")
    parser.add_argument("--data-dir", type=str, default="./data/raw")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=4)
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.batch_size, args.lr, args.num_workers)
