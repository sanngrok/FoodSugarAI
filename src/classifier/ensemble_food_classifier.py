"""Config-driven weighted ensemble classifier for K-Food inference."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from config.settings import BASE_DIR
from src.classifier.food_classifier import ClassificationResult, FoodClassifier, _build_transform
from src.nutrition.nutrition_db import get_nutrition

try:
    import torch
except ImportError:
    torch = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnsembleMember:
    name: str
    weight: float
    classifier: FoodClassifier


def _resolve_path(path: str | Path, *, base_dir: Path = BASE_DIR) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = base_dir / resolved
    return resolved


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _hflip_tensor(tensor):
    return torch.flip(tensor, dims=[3])


class EnsembleFoodClassifier:
    """Weighted ensemble that keeps the same predict API as FoodClassifier.

    The ensemble expects a JSON config with a ``models`` list. Each model entry
    must include ``name``, ``weight``, ``checkpoint``, ``metadata``, and
    ``classes``. The class order must be identical across every member.
    """

    def __init__(self, config_path: str | Path):
        if torch is None:
            raise ImportError("torch가 설치되어 있지 않습니다: pip install torch torchvision timm")

        self.config_path = _resolve_path(config_path)
        self.config = _load_json(self.config_path)
        self.name = str(self.config.get("name", self.config_path.stem))
        self.tta = str(self.config.get("tta", "hflip"))
        if self.tta not in {"none", "hflip"}:
            raise ValueError(f"운영 ensemble은 none/hflip TTA만 지원합니다: {self.tta}")

        self.device = self._get_device()
        self.members = self._load_members()
        self.classes = self.members[0].classifier.classes
        self.model_type = "weighted_ensemble"
        self.model_name = self.name
        self.image_size = max(member.classifier.image_size for member in self.members)

        logger.info(
            "운영 ensemble 로드 완료: %s, members=%d, tta=%s",
            self.config_path,
            len(self.members),
            self.tta,
        )

    @staticmethod
    def _get_device():
        if torch.backends.mps.is_available():
            return torch.device("mps")
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def _load_members(self) -> list[EnsembleMember]:
        raw_models = self.config.get("models")
        if not isinstance(raw_models, list) or not raw_models:
            raise ValueError(f"ensemble config에 models 목록이 없습니다: {self.config_path}")

        members: list[EnsembleMember] = []
        class_reference: list[str] | None = None
        total_weight = 0.0

        for raw in raw_models:
            if not isinstance(raw, dict):
                raise ValueError(f"잘못된 model entry: {raw!r}")
            name = str(raw.get("name", "")).strip()
            checkpoint = _resolve_path(raw.get("checkpoint", ""))
            classes_path = _resolve_path(raw.get("classes", ""))
            metadata_path = _resolve_path(raw.get("metadata", ""))
            weight = float(raw.get("weight", 0.0))
            if not name:
                raise ValueError(f"model name이 비어 있습니다: {raw!r}")
            if weight < 0:
                raise ValueError(f"model weight는 음수일 수 없습니다: {name}={weight}")
            for required in (checkpoint, classes_path, metadata_path):
                if not required.exists():
                    raise FileNotFoundError(f"운영 ensemble 파일이 없습니다: {required}")

            classes = _load_json(classes_path)
            if class_reference is None:
                class_reference = list(classes)
            elif class_reference != list(classes):
                raise ValueError(f"class order mismatch: {name}")

            classifier = FoodClassifier(model_path=checkpoint)
            if classifier.classes != class_reference:
                raise ValueError(f"loaded classifier class order mismatch: {name}")
            members.append(EnsembleMember(name=name, weight=weight, classifier=classifier))
            total_weight += weight

        if total_weight <= 0:
            raise ValueError("ensemble weight 합이 0입니다.")

        return [
            EnsembleMember(
                name=member.name,
                weight=member.weight / total_weight,
                classifier=member.classifier,
            )
            for member in members
            if member.weight > 0
        ]

    def _member_logits(self, member: EnsembleMember, image: Image.Image):
        classifier = member.classifier
        transform = classifier.transform or _build_transform(classifier.image_size)
        tensor = transform(image).unsqueeze(0).to(classifier.device)
        logits = classifier.model(tensor)
        if self.tta == "hflip":
            logits = (logits + classifier.model(_hflip_tensor(tensor))) / 2
        return logits.to(self.device)

    def predict(self, image: Image.Image, top_k: int = 5) -> ClassificationResult:
        """PIL Image -> weighted ensemble ClassificationResult."""
        with torch.inference_mode():
            weighted_logits = None
            for member in self.members:
                logits = self._member_logits(member, image)
                weighted = logits * member.weight
                weighted_logits = weighted if weighted_logits is None else weighted_logits + weighted
            probs = torch.softmax(weighted_logits, dim=1)[0]
            top_probs, top_indices = torch.topk(probs, k=min(top_k, len(self.classes)))
            top5 = [
                (self.classes[index], float(top_probs[position]))
                for position, index in enumerate(top_indices.tolist())
            ]

        food_key = top5[0][0]
        info = get_nutrition(food_key)
        food_name_ko = info.food_name if info else food_key

        return ClassificationResult(
            food_key=food_key,
            food_name_ko=food_name_ko,
            confidence=top5[0][1],
            top5=top5,
        )
