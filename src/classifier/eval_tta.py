"""TTA (Test-Time Augmentation) 정확도 측정"""
import os, ssl, sys, time, certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ssl._create_default_https_context = ssl.create_default_context

import torch, timm
import torchvision.transforms as T
from torchvision.datasets import Food101
from torch.utils.data import DataLoader

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
model = timm.create_model("efficientnet_b2", pretrained=False, num_classes=101)
state = torch.load("data/models/efficientnet_b2_food.pt", map_location=device, weights_only=True)
model.load_state_dict(state)
model = model.to(device).eval()
print("모델 로드 완료", flush=True)

# TTA augmentation 목록
tta_transforms = [
    T.Compose([T.Resize(292), T.CenterCrop(260), T.ToTensor(), T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])]),
    T.Compose([T.Resize(292), T.CenterCrop(260), T.RandomHorizontalFlip(p=1.0), T.ToTensor(), T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])]),
    T.Compose([T.Resize(300), T.CenterCrop(260), T.ToTensor(), T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])]),
    T.Compose([T.Resize(300), T.CenterCrop(260), T.RandomHorizontalFlip(p=1.0), T.ToTensor(), T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])]),
    T.Compose([T.Resize(320), T.CenterCrop(260), T.ToTensor(), T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])]),
]

val_ds_base = Food101("data/raw", split="test", transform=tta_transforms[0], download=False)
N = len(val_ds_base)

# 각 TTA transform마다 softmax 확률 누적
all_probs = None
t0 = time.time()

for i, tf in enumerate(tta_transforms):
    val_ds = Food101("data/raw", split="test", transform=tf, download=False)
    loader = DataLoader(val_ds, batch_size=64, num_workers=0, shuffle=False)
    probs_list = []
    with torch.inference_mode():
        for imgs, _ in loader:
            imgs = imgs.to(device)
            probs_list.append(torch.softmax(model(imgs), dim=1).cpu())
    probs = torch.cat(probs_list, dim=0)  # [N, 101]
    all_probs = probs if all_probs is None else all_probs + probs
    # 현재까지 누적 정확도
    labels_all = torch.tensor([val_ds_base[j][1] for j in range(N)])
    cur_acc = (all_probs.argmax(1) == labels_all).float().mean().item()
    elapsed = time.time() - t0
    name = ["기본", "반전", "큰crop", "큰crop+반전", "더큰crop"][i]
    print(f"TTA {i+1}개 ({name} 추가): acc={cur_acc:.4f} | {elapsed:.0f}초", flush=True)

labels_all = torch.tensor([val_ds_base[j][1] for j in range(N)])
final_acc = (all_probs.argmax(1) == labels_all).float().mean().item()
print(f"\n최종 TTA 정확도: {final_acc:.4f}", flush=True)
print(f"향상: +{(final_acc - 0.8726)*100:.2f}%p (87.26% → {final_acc*100:.2f}%)", flush=True)
