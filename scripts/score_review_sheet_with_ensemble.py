#!/usr/bin/env python3
"""Score a review sheet with a weighted K-Food ensemble."""

from __future__ import annotations

import argparse
import csv
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
logger = logging.getLogger("score_review_sheet_with_ensemble")


class ReviewDataset(Dataset):
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[int, str]:
        return index, self.rows[index]["image_path"]


def collate(batch: list[tuple[int, str]]) -> tuple[list[int], list[str]]:
    indices, paths = zip(*batch)
    return list(indices), list(paths)


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
    parser.add_argument("--review-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--suspects-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--metadata", type=Path, action="append", required=True)
    parser.add_argument("--classes", type=Path, action="append", required=True)
    parser.add_argument("--name", type=str, action="append", required=True)
    parser.add_argument("--weights-json", type=Path, required=True)
    parser.add_argument("--tta", choices=["none", "hflip"], default="hflip")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--suspect-threshold", type=float, default=0.80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (len(args.checkpoint) == len(args.metadata) == len(args.classes) == len(args.name)):
        raise ValueError("--checkpoint/--metadata/--classes/--name counts must match")

    with args.review_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        input_fieldnames = list(rows[0].keys()) if rows else []

    class_lists = [load_json(path) for path in args.classes]
    if not all(class_lists[0] == item for item in class_lists):
        raise ValueError("class lists differ across models")
    classes = class_lists[0]
    class_to_idx = {name: idx for idx, name in enumerate(classes)}
    weights_data = load_json(args.weights_json)
    weight_map = weights_data.get("best_weights", {})
    weights = [float(weight_map.get(name, 0.0)) for name in args.name]
    if sum(weights) <= 0:
        raise ValueError("ensemble weights sum to zero")
    weights = [weight / sum(weights) for weight in weights]

    device = get_device()
    models: list[nn.Module] = []
    image_sizes: list[int] = []
    model_infos: list[dict[str, object]] = []
    for checkpoint, metadata_path, name in zip(args.checkpoint, args.metadata, args.name):
        metadata = load_json(metadata_path)
        classifier = FoodClassifier(model_path=checkpoint)
        if classifier.classes != classes:
            raise ValueError(f"class list mismatch: {checkpoint}")
        model = classifier.model
        if not isinstance(model, nn.Module):
            raise RuntimeError(f"failed to load model: {checkpoint}")
        image_size = int(metadata.get("image_size", classifier.image_size))
        models.append(model.to(device).eval())
        image_sizes.append(image_size)
        model_infos.append({
            "name": name,
            "checkpoint": str(checkpoint),
            "metadata": str(metadata_path),
            "weight": weights[len(model_infos)],
            "image_size": image_size,
        })
        logger.info("loaded %s weight=%.4f image_size=%s", name, weights[len(model_infos) - 1], image_size)

    transforms = {image_size: build_transform(image_size) for image_size in sorted(set(image_sizes))}
    loader = DataLoader(
        ReviewDataset(rows),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate,
    )

    with torch.inference_mode():
        for batch_idx, (indices, paths) in enumerate(loader, start=1):
            logits_sum = None
            for model, image_size, weight in zip(models, image_sizes, weights):
                images = load_images(paths, transforms[image_size], device)
                if args.tta == "hflip":
                    both = torch.cat([images, torch.flip(images, dims=[3])], dim=0)
                    both_logits = model(both)
                    logits = 0.5 * (both_logits[: images.shape[0]] + both_logits[images.shape[0] :])
                else:
                    logits = model(images)
                weighted = logits * weight
                logits_sum = weighted if logits_sum is None else logits_sum + weighted
            probs = torch.softmax(logits_sum, dim=1)
            confs, preds = probs.max(dim=1)
            topk = probs.topk(k=min(3, len(classes)), dim=1)
            for offset, row_index in enumerate(indices):
                pred_idx = int(preds[offset].item())
                pred_label = classes[pred_idx]
                true_label = rows[row_index]["true_label"]
                true_idx = class_to_idx.get(true_label, -1)
                true_prob = float(probs[offset, true_idx].item()) if true_idx >= 0 else 0.0
                top3 = [
                    [classes[int(idx)], float(value)]
                    for idx, value in zip(topk.indices[offset].tolist(), topk.values[offset].tolist())
                ]
                rows[row_index]["ensemble_pred_label"] = pred_label
                rows[row_index]["ensemble_confidence"] = f"{float(confs[offset].item()):.6f}"
                rows[row_index]["ensemble_true_prob"] = f"{true_prob:.6f}"
                rows[row_index]["ensemble_top3"] = json.dumps(top3, ensure_ascii=False)
                rows[row_index]["ensemble_agrees_true"] = str(pred_label == true_label)
                rows[row_index]["ensemble_agrees_candidate"] = str(pred_label == rows[row_index].get("pred_label", ""))
                if not rows[row_index].get("review_status") and pred_label != true_label and float(confs[offset].item()) >= args.suspect_threshold:
                    rows[row_index]["review_status"] = "model_suspect"
                    rows[row_index]["corrected_label"] = pred_label
                    rows[row_index]["review_note"] = (
                        f"ensemble_suspect: top prediction `{pred_label}` "
                        f"conf={float(confs[offset].item()):.3f}; human confirmation required."
                    )
                    rows[row_index]["action"] = "needs_human_review"
            if batch_idx == 1 or batch_idx % 5 == 0 or batch_idx == len(loader):
                logger.info("scored batch %s/%s", batch_idx, len(loader))

    output_fieldnames = [
        *input_fieldnames,
        "ensemble_pred_label",
        "ensemble_confidence",
        "ensemble_true_prob",
        "ensemble_top3",
        "ensemble_agrees_true",
        "ensemble_agrees_candidate",
    ]
    # Preserve order while removing accidental duplicates.
    output_fieldnames = list(dict.fromkeys(output_fieldnames))
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    suspects = [
        row for row in rows
        if row.get("ensemble_agrees_true") == "False"
        and float(row.get("ensemble_confidence", "0") or 0) >= args.suspect_threshold
    ]
    suspects.sort(key=lambda row: float(row["ensemble_confidence"]), reverse=True)
    args.suspects_output.parent.mkdir(parents=True, exist_ok=True)
    with args.suspects_output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(suspects)

    prefilled = sum(1 for row in rows if row.get("review_source") == "existing_ai_patch_train_affected")
    summary = {
        "review_csv": str(args.review_csv),
        "output_csv": str(args.output_csv),
        "suspects_output": str(args.suspects_output),
        "weights_json": str(args.weights_json),
        "tta": args.tta,
        "suspect_threshold": args.suspect_threshold,
        "num_rows": len(rows),
        "num_suspects": len(suspects),
        "prefilled_existing_ai_patch_rows": prefilled,
        "models": model_infos,
    }
    lines = [
        "# Train Review Ensemble Scoring",
        "",
        f"- review_csv: `{args.review_csv}`",
        f"- output_csv: `{args.output_csv}`",
        f"- suspects_output: `{args.suspects_output}`",
        f"- tta: `{args.tta}`",
        f"- suspect_threshold: `{args.suspect_threshold}`",
        f"- num_rows: `{len(rows)}`",
        f"- num_suspects: `{len(suspects)}`",
        "",
        "## Important",
        "",
        "`model_suspect` rows are not confirmed label errors. They require visual/human review before relabel/remove patching.",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
    ]
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_csv)


if __name__ == "__main__":
    main()
