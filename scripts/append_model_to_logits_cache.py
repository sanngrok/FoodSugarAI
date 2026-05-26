#!/usr/bin/env python3
"""Append one model's logits to an existing K-Food weighted-ensemble cache."""

from __future__ import annotations

import argparse
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
from torch import nn
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T

from src.classifier.food_classifier import FoodClassifier


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("append_model_to_logits_cache")


class PathOnlyDataset(Dataset):
    def __init__(self, paths: list[str]) -> None:
        self.paths = paths

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> str:
        return self.paths[index]


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
    images = []
    for path in paths:
        with Image.open(path) as img:
            images.append(transform(img.convert("RGB")))
    return torch.stack(images).to(device)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-cache", type=Path, required=True)
    parser.add_argument("--output-cache", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--classes", type=Path, required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--tta", choices=["none", "hflip"], default="hflip")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--num-workers", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cache = torch.load(args.input_cache, map_location="cpu")
    if args.name in cache["names"]:
        raise ValueError(f"name already exists in cache: {args.name}")
    if args.tta != cache.get("tta"):
        raise ValueError(f"cache tta={cache.get('tta')} but requested tta={args.tta}")

    classes = load_json(args.classes)
    metadata = load_json(args.metadata)
    if classes != cache["classes"]:
        raise ValueError("class list differs from cache")

    classifier = FoodClassifier(model_path=args.checkpoint)
    if classifier.classes != classes:
        raise ValueError("checkpoint classes differ from provided classes")
    model = classifier.model
    if not isinstance(model, nn.Module):
        raise RuntimeError("FoodClassifier did not load a torch module")

    device = get_device()
    model = model.to(device).eval()
    image_size = int(metadata.get("image_size", classifier.image_size))
    transform = build_transform(image_size)
    paths = list(cache["paths"])
    loader = DataLoader(
        PathOnlyDataset(paths),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=lambda batch: list(batch),
    )

    chunks: list[torch.Tensor] = []
    with torch.inference_mode():
        for batch_idx, batch_paths in enumerate(loader, start=1):
            images = load_images(batch_paths, transform, device)
            if args.tta == "hflip":
                both = torch.cat([images, torch.flip(images, dims=[3])], dim=0)
                both_logits = model(both)
                logits = 0.5 * (both_logits[: images.shape[0]] + both_logits[images.shape[0] :])
            else:
                logits = model(images)
            chunks.append(logits.cpu())
            if batch_idx == 1 or batch_idx % 5 == 0 or batch_idx == len(loader):
                logger.info("cached %s batch %s/%s", args.name, batch_idx, len(loader))

    appended_logits = torch.cat(chunks, dim=0)
    if appended_logits.shape[0] != cache["logits"].shape[1]:
        raise RuntimeError("sample count mismatch")
    cache["names"] = [*cache["names"], args.name]
    cache["models"] = [
        *cache["models"],
        {
            "name": args.name,
            "checkpoint": str(args.checkpoint),
            "metadata": str(args.metadata),
            "model_type": classifier.model_type,
            "model_name": classifier.model_name,
            "image_size": image_size,
        },
    ]
    cache["logits"] = torch.cat([cache["logits"], appended_logits.unsqueeze(0)], dim=0)
    args.output_cache.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.output_cache)
    print(args.output_cache)


if __name__ == "__main__":
    main()
