"""Model components for LeWM-style K-Food experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
import timm


@dataclass(frozen=True)
class FoodLeWMConfig:
    model_name: str
    image_size: int
    latent_dim: int = 192
    predictor_dropout: float = 0.1
    num_classes: int | None = None


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def extract_state_dict(checkpoint: Any) -> dict[str, torch.Tensor]:
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "encoder_state_dict", "classifier_state_dict"):
            value = checkpoint.get(key)
            if isinstance(value, dict):
                return value
        if checkpoint and all(torch.is_tensor(v) for v in checkpoint.values()):
            return checkpoint
    raise ValueError("Unsupported checkpoint format")


def load_torch_checkpoint(path: str | Path, device: torch.device) -> Any:
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)
    except Exception:
        return torch.load(path, map_location=device, weights_only=False)


class FoodLeWMEncoder(nn.Module):
    def __init__(self, config: FoodLeWMConfig, pretrained: bool = True) -> None:
        super().__init__()
        self.config = config
        self.backbone = timm.create_model(
            config.model_name,
            pretrained=pretrained,
            num_classes=0,
            global_pool="avg",
        )
        feature_dim = int(self.backbone.num_features)
        self.projector = nn.Sequential(
            nn.Linear(feature_dim, feature_dim),
            nn.GELU(),
            nn.LayerNorm(feature_dim),
            nn.Linear(feature_dim, config.latent_dim),
        )
        self.predictor = nn.Sequential(
            nn.Linear(config.latent_dim, config.latent_dim * 2),
            nn.GELU(),
            nn.Dropout(config.predictor_dropout),
            nn.Linear(config.latent_dim * 2, config.latent_dim),
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        return self.projector(features)

    def predict_latent(self, z: torch.Tensor) -> torch.Tensor:
        return self.predictor(z)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encode(x)


class FoodLeWMClassifier(nn.Module):
    def __init__(self, config: FoodLeWMConfig, pretrained: bool = True) -> None:
        super().__init__()
        if config.num_classes is None:
            raise ValueError("num_classes is required for FoodLeWMClassifier")
        self.config = config
        self.encoder = FoodLeWMEncoder(config, pretrained=pretrained)
        self.classifier = nn.Linear(config.latent_dim, config.num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.encoder.encode(x))


def load_lewm_encoder_weights(
    encoder: FoodLeWMEncoder,
    checkpoint_path: str | Path,
    device: torch.device,
    strict: bool = False,
) -> None:
    checkpoint = load_torch_checkpoint(checkpoint_path, device)
    if isinstance(checkpoint, dict) and isinstance(checkpoint.get("encoder_state_dict"), dict):
        state = checkpoint["encoder_state_dict"]
    else:
        state = extract_state_dict(checkpoint)
    encoder.load_state_dict(state, strict=strict)


def load_classifier_weights(
    model: FoodLeWMClassifier,
    checkpoint_path: str | Path,
    device: torch.device,
) -> None:
    checkpoint = load_torch_checkpoint(checkpoint_path, device)
    if isinstance(checkpoint, dict) and isinstance(checkpoint.get("model_state_dict"), dict):
        state = checkpoint["model_state_dict"]
    else:
        state = extract_state_dict(checkpoint)
    model.load_state_dict(state)
