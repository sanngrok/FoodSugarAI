"""SIGReg-style anti-collapse regularization for Food-LeWM experiments."""

from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


def off_diagonal(x: torch.Tensor) -> torch.Tensor:
    n, m = x.shape
    if n != m:
        raise ValueError("off_diagonal expects a square matrix")
    return x.flatten()[:-1].view(n - 1, n + 1)[:, 1:].flatten()


class SIGRegLoss(nn.Module):
    """Small, practical SIGReg-inspired regularizer.

    The original LeWM setup uses SIGReg to avoid representation collapse. This
    implementation keeps the same purpose for two-view image training by
    combining variance preservation and projected covariance decorrelation.
    """

    def __init__(
        self,
        latent_dim: int,
        num_projections: int = 256,
        eps: float = 1e-4,
        std_target: float = 1.0,
    ) -> None:
        super().__init__()
        self.eps = eps
        self.std_target = std_target
        projection = torch.randn(latent_dim, num_projections)
        projection = F.normalize(projection, dim=0)
        self.register_buffer("projection", projection)

    def forward(self, z_a: torch.Tensor, z_b: torch.Tensor) -> torch.Tensor:
        return 0.5 * (self._single_view(z_a) + self._single_view(z_b))

    def _single_view(self, z: torch.Tensor) -> torch.Tensor:
        z = z.float()
        z = z - z.mean(dim=0, keepdim=True)

        std = torch.sqrt(z.var(dim=0, unbiased=False) + self.eps)
        variance_loss = torch.mean(F.relu(self.std_target - std))

        projected = z @ self.projection.to(device=z.device, dtype=z.dtype)
        projected = projected - projected.mean(dim=0, keepdim=True)
        projected_std = torch.sqrt(projected.var(dim=0, unbiased=False) + self.eps)
        projected = projected / projected_std.clamp_min(self.eps)

        batch_size = max(projected.shape[0] - 1, 1)
        cov = (projected.T @ projected) / batch_size
        covariance_loss = off_diagonal(cov).pow(2).mean()

        return variance_loss + covariance_loss

