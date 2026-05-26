"""
EfficientNet-B2 추가 파인튜닝 (낮은 lr로 수렴)
현재 87.26% → 89~90% 목표
lr=1e-5, 10 에포크
"""
import os, ssl, sys, time, certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

import torch
import torch.nn as nn
import numpy as np
import timm
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision.datasets import Food101
import torchvision.transforms as T
from timm.data.auto_augment import rand_augment_transform
from pathlib import Path

# ── 하이퍼파라미터 ──────────────────────────────────────────────
EPOCHS       = 10
BATCH        = 64
LR           = 1e-5        # 낮은 lr로 세밀하게 수렴
WEIGHT_DECAY = 1e-4
MIXUP_ALPHA  = 0.4
LOG_INTERVAL = 100
IMG_SIZE     = 260
BASE_PATH    = Path("data/models/efficientnet_b2_food.pt")   # 기존 체크포인트
SAVE_PATH    = Path("data/models/efficientnet_b2_ft.pt")     # 파인튜닝 저장

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 장치: {device} | lr={LR} | 에포크: {EPOCHS}", flush=True)

# ── Augmentation ────────────────────────────────────────────────
TRAIN_TF = T.Compose([
    T.RandomResizedCrop(IMG_SIZE, scale=(0.7, 1.0)),
    T.RandomHorizontalFlip(),
    rand_augment_transform("rand-m7-n2-mstd0.5", {}),  # 강도 약간 낮춤
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

# ── 모델 — 기존 체크포인트 로드 ─────────────────────────────────
model = timm.create_model("efficientnet_b2", pretrained=False, num_classes=101)
state = torch.load(BASE_PATH, map_location=device, weights_only=True)
model.load_state_dict(state)
model = model.to(device)

# 파인튜닝 체크포인트가 있으면 이어서
best_acc = 0.8726
START_EPOCH = 1
if SAVE_PATH.exists():
    acc_file   = SAVE_PATH.with_suffix(".acc")
    epoch_file = SAVE_PATH.with_suffix(".epoch")
    ft_state   = torch.load(SAVE_PATH, map_location=device, weights_only=True)
    model.load_state_dict(ft_state)
    best_acc    = float(acc_file.read_text().strip())  if acc_file.exists()  else best_acc
    START_EPOCH = int(epoch_file.read_text().strip())  if epoch_file.exists() else 1
    print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 파인튜닝 체크포인트 로드 (Epoch {START_EPOCH}부터, best_acc={best_acc:.4f})", flush=True)
else:
    print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 기존 체크포인트(87.26%) 로드 완료, Epoch 1부터 파인튜닝 시작", flush=True)

# ── MixUp ───────────────────────────────────────────────────────
def mixup_data(x, y, alpha=MIXUP_ALPHA):
    lam = np.random.beta(alpha, alpha) if alpha > 0 else 1.0
    idx = torch.randperm(x.size(0), device=x.device)
    return lam * x + (1 - lam) * x[idx], y, y[idx], lam

def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)

# ── 옵티마이저 — 전체 파라미터, 낮은 lr ─────────────────────────
optimizer = AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-7)
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

# ── 학습 루프 ───────────────────────────────────────────────────
SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

for epoch in range(START_EPOCH, EPOCHS + 1):
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

    SAVE_PATH.with_suffix(".epoch").write_text(str(epoch + 1))
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), SAVE_PATH)
        SAVE_PATH.with_suffix(".acc").write_text(str(best_acc))
        print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO   -> 모델 저장 (acc={best_acc:.4f})", flush=True)

print(f"{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S} INFO 파인튜닝 완료. 최고 정확도: {best_acc:.4f}", flush=True)
