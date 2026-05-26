"""
EfficientNet-B2 + RandAugment + MixUp Fine-tuning (Food-101)
목표: val_acc 88~90%
에포크당 약 20분 (MPS 기준)
"""

import logging
import os
import ssl
import sys
import time
from pathlib import Path

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

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
MODEL_NAME    = "efficientnet_b2"
IMG_SIZE      = 260
EPOCHS        = 15
BATCH         = 64
LR            = 3e-4
WEIGHT_DECAY  = 1e-4
WARMUP_EPOCHS = 2
MIXUP_ALPHA   = 0.4
LOG_INTERVAL  = 100
SAVE_PATH     = Path("data/models/efficientnet_b2_food.pt")

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 장치: {device} | 모델: {MODEL_NAME} | 배치: {BATCH} | 에포크: {EPOCHS}", flush=True)

# ── Augmentation ────────────────────────────────────────────────
TRAIN_TF = T.Compose([
    T.RandomResizedCrop(IMG_SIZE, scale=(0.6, 1.0)),
    T.RandomHorizontalFlip(),
    rand_augment_transform("rand-m9-n2-mstd0.5", {}),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
VAL_TF = T.Compose([
    T.Resize(IMG_SIZE + 32),
    T.CenterCrop(IMG_SIZE),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ── 데이터셋 ────────────────────────────────────────────────────
train_ds     = Food101("data/raw", split="train", transform=TRAIN_TF, download=False)
val_ds       = Food101("data/raw", split="test",  transform=VAL_TF,   download=False)
train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True,  num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False, num_workers=0)
print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 학습: {len(train_ds)}장 | 검증: {len(val_ds)}장", flush=True)

# ── 모델 ────────────────────────────────────────────────────────
model = timm.create_model(MODEL_NAME, pretrained=True, num_classes=101)
model = model.to(device)

START_EPOCH = 1
best_acc = 0.0
if SAVE_PATH.exists():
    state = torch.load(SAVE_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state)
    acc_file  = SAVE_PATH.with_suffix(".acc")
    epoch_file = SAVE_PATH.with_suffix(".epoch")
    best_acc   = float(acc_file.read_text().strip())  if acc_file.exists()  else 0.0
    START_EPOCH = int(epoch_file.read_text().strip()) if epoch_file.exists() else WARMUP_EPOCHS + 1
    print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 체크포인트 로드 (Epoch {START_EPOCH}부터, best_acc={best_acc:.4f})", flush=True)
else:
    print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO ImageNet pretrained 로드 완료", flush=True)

# ── MixUp ───────────────────────────────────────────────────────
def mixup_data(x, y, alpha=MIXUP_ALPHA):
    lam = np.random.beta(alpha, alpha) if alpha > 0 else 1.0
    idx = torch.randperm(x.size(0), device=x.device)
    return lam * x + (1 - lam) * x[idx], y, y[idx], lam

def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)

# ── 옵티마이저 ──────────────────────────────────────────────────
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
        print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 전체 파라미터 unfreeze (lr={LR/5:.2e})", flush=True)

    model.train()
    total_loss = 0.0
    epoch_start = time.time()
    for batch_idx, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)
        images, y_a, y_b, lam = mixup_data(images, labels)
        optimizer.zero_grad()
        loss = mixup_criterion(criterion, model(images), y_a, y_b, lam)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        if (batch_idx + 1) % LOG_INTERVAL == 0:
            elapsed = time.time() - epoch_start
            eta = elapsed / (batch_idx + 1) * (len(train_loader) - batch_idx - 1)
            print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO   "
                  f"Epoch {epoch:2d} | {batch_idx+1:4d}/{len(train_loader)} "
                  f"| loss={total_loss/(batch_idx+1):.4f} | ETA {eta/60:.1f}분", flush=True)
    scheduler.step()

    model.eval()
    correct = 0
    with torch.inference_mode():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            correct += (model(images).argmax(1) == labels).sum().item()
    val_acc = correct / len(val_ds)

    print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO "
          f"Epoch {epoch:2d}/{EPOCHS} | loss={total_loss/len(train_loader):.4f} | val_acc={val_acc:.4f}", flush=True)

    # 다음 재개를 위해 epoch 기록 (항상 업데이트)
    SAVE_PATH.with_suffix(".epoch").write_text(str(epoch + 1))
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), SAVE_PATH)
        SAVE_PATH.with_suffix(".acc").write_text(str(best_acc))
        print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO   -> 모델 저장 (acc={best_acc:.4f})", flush=True)

print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 학습 완료. 최고 정확도: {best_acc:.4f}", flush=True)
