from __future__ import annotations
import numpy as np

class EmbedModel:
    """ResNet50 임베딩 모델(스켈레톤).
    - 실제 사용 시: torchvision.models.resnet50 + pooling 등으로 구현
    """
    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path

    def embed(self, image_rgb) -> np.ndarray:
        # (D,) float32
        return np.random.randn(512).astype(np.float32)
