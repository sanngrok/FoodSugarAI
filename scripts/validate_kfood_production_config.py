#!/usr/bin/env python3
"""Lightweight preflight validation for the production K-Food ensemble config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import BASE_DIR


def resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = BASE_DIR / resolved
    return resolved


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=BASE_DIR / "config" / "kfood_production_ensemble_config.json",
        help="Production ensemble config JSON.",
    )
    parser.add_argument(
        "--min-top1",
        type=float,
        # 7개 모델(0.9202)에서 가중치 합 약 1%인 3개를 뺀 4개 모델 구성이 0.9199이다.
        default=0.919,
        help="Minimum verified top1 required in config metadata.",
    )
    parser.add_argument(
        "--expected-classes",
        type=int,
        default=56,
        help="Expected number of K-Food classes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = resolve_path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")

    config = load_json(config_path)
    models = config.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("config.models must be a non-empty list")

    metrics = config.get("verified_metrics")
    if not isinstance(metrics, dict):
        raise ValueError("config.verified_metrics must be an object")
    top1 = float(metrics.get("top1", 0.0))
    if top1 < args.min_top1:
        raise ValueError(f"verified top1 is below target: {top1} < {args.min_top1}")

    tta = config.get("tta")
    if tta not in {"none", "hflip"}:
        raise ValueError(f"unsupported production tta: {tta}")

    total_weight = 0.0
    class_reference: list[str] | None = None
    checked_models: list[dict[str, Any]] = []
    for index, model in enumerate(models):
        if not isinstance(model, dict):
            raise ValueError(f"model entry #{index} must be an object")
        name = str(model.get("name", "")).strip()
        if not name:
            raise ValueError(f"model entry #{index} has no name")
        weight = float(model.get("weight", 0.0))
        if weight < 0:
            raise ValueError(f"negative weight: {name}={weight}")
        total_weight += weight

        paths = {
            key: resolve_path(model.get(key, ""))
            for key in ("checkpoint", "metadata", "classes")
        }
        for key, path in paths.items():
            if not path.exists():
                raise FileNotFoundError(f"{name}.{key} not found: {path}")

        classes = load_json(paths["classes"])
        if len(classes) != args.expected_classes:
            raise ValueError(f"{name} class count mismatch: {len(classes)}")
        if class_reference is None:
            class_reference = list(classes)
        elif class_reference != list(classes):
            raise ValueError(f"class order mismatch: {name}")

        metadata = load_json(paths["metadata"])
        checked_models.append({
            "name": name,
            "weight": weight,
            "checkpoint": str(paths["checkpoint"]),
            "model_name": metadata.get("model_name"),
            "model_type": metadata.get("model_type", "timm_classifier"),
            "image_size": metadata.get("image_size"),
        })

    if total_weight <= 0:
        raise ValueError("sum of weights must be positive")

    summary = {
        "status": "ok",
        "config": str(config_path),
        "name": config.get("name"),
        "tta": tta,
        "verified_top1": top1,
        "verified_correct": metrics.get("correct"),
        "verified_num_samples": metrics.get("num_samples"),
        "num_models": len(models),
        "num_classes": len(class_reference or []),
        "weight_sum": total_weight,
        "models": checked_models,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
