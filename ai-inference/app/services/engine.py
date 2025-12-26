from __future__ import annotations

import base64
import io
import os
from datetime import datetime, timezone, timedelta
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import settings
from app.services.prototype_index import PrototypeIndex, load_index


def _ensure_cache_dir():
    os.makedirs(settings.CACHE_DIR, exist_ok=True)


class InferenceEngine:
    def __init__(self) -> None:
        self.mock = bool(settings.AI_MOCK_MODE)
        self.prototype_index: PrototypeIndex | None = None

    def startup_load(self) -> None:
        if self.mock:
            return

        # 이번 데모 정책: prototype은 로컬에서 관리 (Central/GCS에서 끌어오지 않음)
        if not settings.PROTOTYPE_INDEX_PATH:
            self.prototype_index = None
            return

        npy = settings.PROTOTYPE_INDEX_PATH
        meta = npy.replace(".npy", ".json")
        self.prototype_index = load_index(npy, meta)

    def infer_tray(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.mock:
            return {
                "overlap_score": 0.12,
                "decision": "REVIEW",
                "result_json": {
                    "mode": "mock",
                    "instances": [
                        {
                            "instance_id": 1,
                            "confidence": 0.92,
                            "top_k": [{"item_id": 101, "distance": 0.1423}, {"item_id": 109, "distance": 0.1504}],
                            "best_item_id": 101,
                            "match_distance": 0.1423,
                            "match_margin": 0.0081,
                            "state": "REVIEW",
                            "qty": 1
                        }
                    ]
                }
            }

        if not self.prototype_index:
            return {
                "overlap_score": None,
                "decision": "UNKNOWN",
                "result_json": {"error": "prototype index not loaded (set PROTOTYPE_INDEX_PATH)"},
            }

        img = self._load_rgb_image_from_payload(payload)

        # TODO(다음 단계): YOLO seg + crop -> embedding 생성으로 q를 만들기
        # 지금은 skeleton 유지: 랜덤 임베딩으로 knn 흐름만 유지
        D = self.prototype_index.vectors.shape[1]
        q = np.random.randn(D).astype(np.float32)

        topk = self.prototype_index.knn(q, k=5)
        best_item, d1 = topk[0]
        d2 = topk[1][1] if len(topk) > 1 else (d1 + 1.0)
        margin = float(d2 - d1)

        state = "AUTO" if margin >= 0.03 else "REVIEW"
        decision = "AUTO" if state == "AUTO" else "REVIEW"

        return {
            "overlap_score": 0.0,
            "decision": decision,
            "result_json": {
                "mode": "real_skeleton",
                "input": {"shape": [int(img.shape[0]), int(img.shape[1]), int(img.shape[2])]},
                "instances": [{
                    "instance_id": 1,
                    "confidence": 0.9,
                    "top_k": [{"item_id": int(i), "distance": float(d)} for i, d in topk],
                    "best_item_id": int(best_item),
                    "match_distance": float(d1),
                    "match_margin": margin,
                    "state": state,
                    "qty": 1
                }],
                "items": [{"item_id": int(best_item), "qty": 1}],
            }
        }

    def infer_cctv(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        if self.mock:
            return {
                "events": [
                    {
                        "event_type": "FALL",
                        "confidence": 0.88,
                        "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                        "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                        "meta_json": {"mode": "mock"},
                    }
                ]
            }
        return {"events": []}

    def _load_rgb_image_from_payload(self, payload: dict[str, Any]) -> np.ndarray:
        _ensure_cache_dir()

        frame_b64 = payload.get("frame_b64")
        if not frame_b64:
            raise ValueError("frame_b64 required")

        # data URL prefix 제거(브라우저/에이전트에서 붙이는 경우 많음)
        if "," in frame_b64 and frame_b64.strip().startswith("data:"):
            frame_b64 = frame_b64.split(",", 1)[1]

        raw = base64.b64decode(frame_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return np.array(img)  # (H,W,3) uint8
