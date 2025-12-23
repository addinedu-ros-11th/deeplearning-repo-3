from __future__ import annotations
from typing import Any

class YoloSegModel:
    """YOLO Segmentation 로더(스켈레톤).
    - 실제 사용 시: ultralytics 또는 torchscript 모델로 교체하십시오.
    """
    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path

    def predict(self, image_bgr) -> list[dict[str, Any]]:
        # return list of {mask, bbox, confidence}
        return []
