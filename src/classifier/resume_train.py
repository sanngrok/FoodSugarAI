"""체크포인트에서 이어서 학습 (추가 10 에포크)"""
import logging, os, ssl
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

import torch, torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision.datasets import Food101
import torchvision.transforms as T
import timm
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SAVE_PATH = Path("data/models/efficientnet_food.pt")
EPOCHS    = 10
LR        = 5e-5
BATCH     = 64

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
logger.info("장치: %s", device)

TRAIN_TF = T.Compose([
    T.RandomResizedCrop(224, scale=(0.7, 1.0)),
    T.RandomHorizontalFlip(),
    T.ColorJitter(0.3, 0.3, 0.2),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
VAL_TF = T.Compose([
    T.Resize(256), T.CenterCrop(224), T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

train_ds     = Food101("data/raw", split="train", transform=TRAIN_TF, download=False)
val_ds       = Food101("data/raw", split="test",  transform=VAL_TF,   download=False)
train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True,  num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False, num_workers=0)

model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=101)
state = torch.load(SAVE_PATH, map_location=device, weights_only=True)
model.load_state_dict(state)
model = model.to(device)
logger.info("체크포인트 로드 완료 (base acc=0.7249): %s", SAVE_PATH)

optimizer = AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS)
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

best_acc = 0.8301
for epoch in range(1, EPOCHS + 1):
    model.train()
    total_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        loss = criterion(model(images), labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    model.eval()
    correct = 0
    with torch.inference_mode():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            correct += (model(images).argmax(1) == labels).sum().item()
    val_acc = correct / len(val_ds)
    scheduler.step()

    logger.info("Epoch %2d/%d | loss=%.4f | val_acc=%.4f",
                epoch, EPOCHS, total_loss / len(train_loader), val_acc)
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), SAVE_PATH)
        logger.info("  -> 모델 저장 (acc=%.4f)", best_acc)

logger.info("추가 학습 완료. 최고 정확도: %.4f", best_acc)
