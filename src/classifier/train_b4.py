"""
EfficientNet-B4 + RandAugment + MixUp Fine-tuning (Food-101)
목표: val_acc 90% 근접
"""

import logging
import os
import ssl
import sys
from pathlib import Path

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

# ── 로깅: timm import 전에 root logger 직접 설정 ──────────────────
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)   # stdout으로 (stderr 아님)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
root_logger.addHandler(_handler)
logger = logging.getLogger(__name__)

import torch
import torch.nn as nn
import numpy as np
import timm
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.utils.data import DataLoader
from torchvision.datasets import Food101
import torchvision.transforms as T
from timm.data.auto_augment import rand_augment_transform

# ── 하이퍼파라미터 ──────────────────────────────────────────────
MODEL_NAME   = "efficientnet_b4"
IMG_SIZE     = 320
EPOCHS       = 15
BATCH        = 64
LR           = 3e-4
WEIGHT_DECAY = 1e-4
WARMUP_EPOCHS = 2
MIXUP_ALPHA  = 0.4
LOG_INTERVAL = 50       # 50배치마다 출력 (더 자주)
SAVE_PATH    = Path("data/models/efficientnet_b4_food.pt")

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
logger.info("장치: %s | 모델: %s | 배치: %d | 에포크: %d", device, MODEL_NAME, BATCH, EPOCHS)
sys.stdout.flush()

# ── Augmentation ────────────────────────────────────────────────
ra_config = "rand-m9-n2-mstd0.5"

TRAIN_TF = T.Compose([
    T.RandomResizedCrop(IMG_SIZE, scale=(0.6, 1.0)),
    T.RandomHorizontalFlip(),
    rand_augment_transform(ra_config, {}),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

VAL_TF = T.Compose([
    T.Resize(IMG_SIZE + 32),
    T.CenterCrop(IMG_SIZE),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ── 데이터셋 — num_workers=2로 병렬 로딩 ────────────────────────
train_ds     = Food101("data/raw", split="train", transform=TRAIN_TF, download=False)
val_ds       = Food101("data/raw", split="test",  transform=VAL_TF,   download=False)
train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True,  num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False, num_workers=0)
logger.info("학습: %d장 | 검증: %d장", len(train_ds), len(val_ds))
sys.stdout.flush()

# ── 모델 ────────────────────────────────────────────────────────
model = timm.create_model(MODEL_NAME, pretrained=True, num_classes=101)
model = model.to(device)

# Epoch 2 체크포인트 로드 후 이어서 학습
START_EPOCH = 1
best_acc = 0.0
if SAVE_PATH.exists():
    state = torch.load(SAVE_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state)
    START_EPOCH = WARMUP_EPOCHS + 1
    best_acc = 0.5755
    logger.info("체크포인트 로드 완료 (Epoch %d부터 재개, best_acc=%.4f)", START_EPOCH, best_acc)
else:
    logger.info("ImageNet pretrained 로드 완료")
sys.stdout.flush()

# ── MixUp 유틸 ──────────────────────────────────────────────────
def mixup_data(x, y, alpha=MIXUP_ALPHA):
    lam = np.random.beta(alpha, alpha) if alpha > 0 else 1.0
    idx = torch.randperm(x.size(0), device=x.device)
    return lam * x + (1 - lam) * x[idx], y, y[idx], lam

def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)

# ── 옵티마이저 & 스케줄러 ───────────────────────────────────────
for p in model.parameters():
    p.requires_grad = False
for p in model.get_classifier().parameters():
    p.requires_grad = True

optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=LR)
scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=max(EPOCHS - WARMUP_EPOCHS, 1), eta_min=1e-6)
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

# ── 학습 루프 ───────────────────────────────────────────────────
SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

for epoch in range(START_EPOCH, EPOCHS + 1):
    if epoch == WARMUP_EPOCHS + 1:
        for p in model.parameters():
            p.requires_grad = True
        optimizer = AdamW(model.parameters(), lr=LR / 5, weight_decay=WEIGHT_DECAY)
        scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=EPOCHS - WARMUP_EPOCHS, eta_min=1e-6)
        logger.info("전체 파라미터 unfreeze (lr=%.2e)", LR / 5)
        sys.stdout.flush()

    model.train()
    total_loss = 0.0
    for batch_idx, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)
        images, y_a, y_b, lam = mixup_data(images, labels)
        optimizer.zero_grad()
        loss = mixup_criterion(criterion, model(images), y_a, y_b, lam)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        if (batch_idx + 1) % LOG_INTERVAL == 0:
            print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO   "
                  f"Epoch {epoch:2d} | batch {batch_idx+1:4d}/{len(train_loader)} "
                  f"| avg_loss={total_loss/(batch_idx+1):.4f}", flush=True)
    scheduler.step()

    model.eval()
    correct = 0
    with torch.inference_mode():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            correct += (model(images).argmax(1) == labels).sum().item()
    val_acc = correct / len(val_ds)

    print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO "
          f"Epoch {epoch:2d}/{EPOCHS} | loss={total_loss/len(train_loader):.4f} | val_acc={val_acc:.4f}",
          flush=True)

    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), SAVE_PATH)
        print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO   "
              f"-> 모델 저장 (acc={best_acc:.4f})", flush=True)

print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO "
      f"학습 완료. 최고 정확도: {best_acc:.4f}", flush=True)
