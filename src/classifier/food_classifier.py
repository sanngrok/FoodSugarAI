"""
EfficientNet 기반 음식 이미지 분류기
timm 라이브러리를 사용해 pretrained 가중치 로드 후 fine-tuning 구조 지원.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as T
    _TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    nn = None     # type: ignore
    T = None      # type: ignore
    _TORCH_AVAILABLE = False

try:
    import timm
except ImportError:
    timm = None  # 런타임에 안내 메시지 출력

from config.settings import settings

try:
    from src.classifier.food_lewm_model import FoodLeWMClassifier, FoodLeWMConfig
except ImportError:
    FoodLeWMClassifier = None  # type: ignore
    FoodLeWMConfig = None  # type: ignore

logger = logging.getLogger(__name__)

KOREAN_MODEL_PATH   = Path("data/models/efficientnet_korean.pt")
KOREAN_CLASSES_PATH = Path("data/models/korean_food_classes.json")
KOREAN_METADATA_PATH = Path("data/models/korean_food_model_meta.json")

LEWM_MODEL_TYPE = "food_lewm_classifier"


@dataclass
class ClassificationResult:
    food_key: str           # DB 키 (e.g. "pizza")
    food_name_ko: str       # 한국어명
    confidence: float       # top-1 확률
    top5: list[tuple[str, float]]  # [(food_key, prob), ...]


# Food-101 클래스 순서 (alphabetical) — timm Food-101 pretrained 모델 기준
FOOD101_CLASSES = [
    "apple_pie", "baby_back_ribs", "baklava", "beef_carpaccio", "beef_tartare",
    "beet_salad", "beignets", "bibimbap", "bread_pudding", "breakfast_burrito",
    "bruschetta", "caesar_salad", "cannoli", "caprese_salad", "carrot_cake",
    "ceviche", "cheesecake", "cheese_plate", "chicken_curry", "chicken_quesadilla",
    "chicken_wings", "chocolate_cake", "chocolate_mousse", "churros", "clam_chowder",
    "club_sandwich", "crab_cakes", "creme_brulee", "croque_madame", "cup_cakes",
    "deviled_eggs", "donuts", "dumplings", "edamame", "eggs_benedict",
    "escargots", "falafel", "filet_mignon", "fish_and_chips", "foie_gras",
    "french_fries", "french_onion_soup", "french_toast", "fried_calamari", "fried_rice",
    "frozen_yogurt", "garlic_bread", "gnocchi", "greek_salad", "grilled_cheese_sandwich",
    "grilled_salmon", "guacamole", "gyoza", "hamburger", "hot_and_sour_soup",
    "hot_dog", "huevos_rancheros", "hummus", "ice_cream", "lasagna",
    "lobster_bisque", "lobster_roll_sandwich", "macaroni_and_cheese", "macarons", "miso_soup",
    "mussels", "nachos", "omelette", "onion_rings", "oysters",
    "pad_thai", "paella", "pancakes", "panna_cotta", "peking_duck",
    "pho", "pizza", "pork_chop", "poutine", "prime_rib",
    "pulled_pork_sandwich", "ramen", "ravioli", "red_velvet_cake", "risotto",
    "samosa", "sashimi", "scallops", "seaweed_salad", "shrimp_and_grits",
    "spaghetti_bolognese", "spaghetti_carbonara", "spring_rolls", "steak", "strawberry_shortcake",
    "sushi", "tacos", "takoyaki", "tiramisu", "tuna_tartare", "waffles",
]

# 전처리 파이프라인 (ImageNet 통계 사용) — torch 설치 시에만 구성
def _build_transform(image_size: int | None = None):
    if not _TORCH_AVAILABLE:
        return None
    size = image_size or settings.image_size
    return T.Compose([
        T.Resize(size + 32),
        T.CenterCrop(size),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]),
    ])

TRANSFORM = _build_transform()


def build_model(num_classes: int = 101, pretrained: bool = True, model_name: str = "efficientnet_b0"):
    """timm 모델 빌드"""
    if not _TORCH_AVAILABLE:
        raise ImportError("torch/torchvision 패키지가 설치되어 있지 않습니다: pip install torch torchvision")
    if timm is None:
        raise ImportError("timm 패키지가 설치되어 있지 않습니다: pip install timm")
    model = timm.create_model(
        model_name,
        pretrained=pretrained,
        num_classes=num_classes,
    )
    return model


def _torch_load(path: Path, device: torch.device) -> Any:
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)
    except Exception:
        # Local training checkpoints may include small metadata objects that
        # PyTorch's weights_only mode rejects. Only use this for local paths.
        return torch.load(path, map_location=device, weights_only=False)


def _candidate_companion_paths(model_path: Path) -> tuple[Path | None, Path | None]:
    stem = model_path.stem
    candidates: list[tuple[Path, Path]] = []
    if stem.startswith("efficientnet_korean_"):
        suffix = stem[len("efficientnet_korean_") :]
        candidates.append((
            model_path.with_name(f"korean_food_classes_{suffix}.json"),
            model_path.with_name(f"korean_food_model_meta_{suffix}.json"),
        ))
    if stem.endswith("_classifier"):
        prefix = stem[: -len("_classifier")]
        candidates.append((
            model_path.with_name(f"{prefix}_classes.json"),
            model_path.with_name(f"{prefix}_meta.json"),
        ))
    if "_classifier_" in stem:
        prefix, suffix = stem.split("_classifier_", 1)
        candidates.append((
            model_path.with_name(f"{prefix}_classes_{suffix}.json"),
            model_path.with_name(f"{prefix}_meta_{suffix}.json"),
        ))
    candidates.extend([
        (model_path.with_suffix(".classes.json"), model_path.with_suffix(".meta.json")),
        (KOREAN_CLASSES_PATH, KOREAN_METADATA_PATH),
    ])

    for classes_path, metadata_path in candidates:
        if classes_path.exists() and metadata_path.exists():
            return classes_path, metadata_path
    for classes_path, metadata_path in candidates:
        if classes_path.exists():
            return classes_path, metadata_path if metadata_path.exists() else None
    return None, None


def _is_lewm_checkpoint(checkpoint: Any, metadata: dict[str, Any]) -> bool:
    if metadata.get("model_type") == LEWM_MODEL_TYPE:
        return True
    if "latent_dim" in metadata and "lewm_checkpoint" in metadata:
        return True
    if isinstance(checkpoint, dict):
        state = checkpoint.get("model_state_dict")
        config = checkpoint.get("config")
        if isinstance(config, dict) and "latent_dim" in config:
            return True
        if isinstance(state, dict) and any(key.startswith("encoder.") for key in state):
            return True
    return False


class FoodClassifier:
    """추론 전용 래퍼 — 모델 로드 및 predict 인터페이스 제공

    우선순위:
      1. 한국 음식 모델 (efficientnet_korean.pt + korean_food_classes.json)
      2. Food-101 모델 (efficientnet_food.pt)
      3. ImageNet pretrained fallback
    """

    def __init__(self, model_path: Path | None = None):
        if not _TORCH_AVAILABLE:
            raise ImportError("torch가 설치되어 있지 않습니다: pip install torch torchvision timm")
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        self.model: nn.Module | None = None
        self.classes = FOOD101_CLASSES  # 기본값
        self.model_name = "efficientnet_b0"
        self.image_size = settings.image_size
        self.transform = TRANSFORM
        self.model_type = "timm_classifier"

        if model_path is not None:
            model_path = Path(model_path)
            classes_path, metadata_path = _candidate_companion_paths(model_path)
            if classes_path and classes_path.exists():
                with open(classes_path, encoding="utf-8") as f:
                    self.classes = json.load(f)
            metadata: dict[str, Any] = {}
            if metadata_path and metadata_path.exists():
                with open(metadata_path, encoding="utf-8") as f:
                    metadata = json.load(f)
                self.model_name = metadata.get("model_name", self.model_name)
                self.image_size = int(metadata.get("image_size", self.image_size))
                self.transform = _build_transform(self.image_size)
            self._load(model_path, num_classes=len(self.classes), metadata=metadata)
            logger.info(
                "지정 음식 분류기 로드: %s, type=%s, %d클래스, image_size=%d",
                model_path, self.model_type, len(self.classes), self.image_size,
            )
            return

        # 한국 음식 모델 우선 로드
        if KOREAN_MODEL_PATH.exists() and KOREAN_CLASSES_PATH.exists():
            with open(KOREAN_CLASSES_PATH, encoding="utf-8") as f:
                self.classes = json.load(f)
            if KOREAN_METADATA_PATH.exists():
                with open(KOREAN_METADATA_PATH, encoding="utf-8") as f:
                    metadata = json.load(f)
                self.model_name = metadata.get("model_name", self.model_name)
                self.image_size = int(metadata.get("image_size", self.image_size))
                self.transform = _build_transform(self.image_size)
            self._load(KOREAN_MODEL_PATH, num_classes=len(self.classes), metadata=metadata if KOREAN_METADATA_PATH.exists() else {})
            logger.info(
                "한국 음식 분류기 로드: %s, %d클래스, image_size=%d",
                self.model_name, len(self.classes), self.image_size,
            )
            return

        # Food-101 모델
        food101_path = model_path or settings.classifier_model_path
        if food101_path.exists():
            self._load(food101_path, num_classes=len(self.classes), metadata={})
        else:
            logger.warning(
                "학습된 모델 파일이 없습니다. pretrained ImageNet 가중치로 초기화합니다 (정확도 낮음)."
            )
            self.model = build_model(
                num_classes=len(self.classes),
                pretrained=True,
                model_name=self.model_name,
            )
            self.model.eval().to(self.device)

    def _load(self, path: Path, num_classes: int | None = None, metadata: dict[str, Any] | None = None) -> None:
        nc = num_classes or len(self.classes)
        metadata = metadata or {}
        checkpoint = _torch_load(path, self.device)
        if _is_lewm_checkpoint(checkpoint, metadata):
            if FoodLeWMClassifier is None or FoodLeWMConfig is None:
                raise ImportError("Food-LeWM 모델 로더를 사용할 수 없습니다.")
            config_data = checkpoint.get("config", {}) if isinstance(checkpoint, dict) else {}
            self.model_name = str(metadata.get("model_name", config_data.get("model_name", self.model_name)))
            self.image_size = int(metadata.get("image_size", config_data.get("image_size", self.image_size)))
            latent_dim = int(metadata.get("latent_dim", config_data.get("latent_dim", 192)))
            config = FoodLeWMConfig(
                model_name=self.model_name,
                image_size=self.image_size,
                latent_dim=latent_dim,
                num_classes=nc,
            )
            self.model = FoodLeWMClassifier(config, pretrained=False)
            if isinstance(checkpoint, dict) and isinstance(checkpoint.get("model_state_dict"), dict):
                state = checkpoint["model_state_dict"]
            elif isinstance(checkpoint, dict) and checkpoint and all(torch.is_tensor(v) for v in checkpoint.values()):
                state = checkpoint
            else:
                raise ValueError(f"지원하지 않는 Food-LeWM checkpoint 형식: {path}")
            self.model.load_state_dict(state)
            self.model_type = LEWM_MODEL_TYPE
            self.transform = _build_transform(self.image_size)
        else:
            self.model = build_model(num_classes=nc, pretrained=False, model_name=self.model_name)
            if isinstance(checkpoint, dict):
                if isinstance(checkpoint.get("model_state_dict"), dict):
                    state = checkpoint["model_state_dict"]
                elif isinstance(checkpoint.get("state_dict"), dict):
                    state = checkpoint["state_dict"]
                else:
                    state = checkpoint
            else:
                state = checkpoint
            self.model.load_state_dict(state)
            self.model_type = "timm_classifier"
        self.model.eval().to(self.device)
        logger.info("분류기 모델 로드 완료: %s (%s, %s)", path, self.model_name, self.model_type)

    def predict(self, image: Image.Image, top_k: int = 5) -> ClassificationResult:
        """PIL Image → ClassificationResult"""
        with torch.inference_mode():
            tensor = self.transform(image).unsqueeze(0).to(self.device)
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

            top_probs, top_indices = torch.topk(probs, k=top_k)
            top5 = [(self.classes[i], float(top_probs[j]))
                    for j, i in enumerate(top_indices.tolist())]

        food_key = top5[0][0]
        confidence = top5[0][1]

        # 한국어 이름 조회
        # 한국 음식 모델: food_key 자체가 한국어 (e.g. "비빔밥")
        # Food-101 모델: food_key가 영어 → nutrition_db에서 한국어명 조회
        from src.nutrition.nutrition_db import get_nutrition
        info = get_nutrition(food_key)
        if info:
            food_name_ko = info.food_name
        elif KOREAN_CLASSES_PATH.exists():
            # 한국 음식 모델인 경우 food_key 자체가 한국어
            food_name_ko = food_key
        else:
            food_name_ko = food_key.replace("_", " ").title()

        return ClassificationResult(
            food_key=food_key,
            food_name_ko=food_name_ko,
            confidence=confidence,
            top5=top5,
        )
