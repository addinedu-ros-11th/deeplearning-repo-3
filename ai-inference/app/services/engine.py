from __future__ import annotations

import base64
import io
from PIL import Image

import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Any
from app.core.config import settings
from app.services.gcs_utils import download_to
from app.services.prototype_index import PrototypeIndex, load_index
from app.services.central_client import CentralClient, CentralClientError

class InferenceEngine:
    def __init__(self) -> None:
        self.mock = bool(settings.AI_MOCK_MODE)
        self.prototype_index: PrototypeIndex | None = None

    def startup_load(self) -> None:
        if self.mock:
            return

        # Priority 1: local index
        if settings.PROTOTYPE_INDEX_PATH:
            npy = settings.PROTOTYPE_INDEX_PATH
            meta = npy.replace(".npy", ".json")
            self.prototype_index = load_index(npy, meta)
            return

        # Priority 2: GCS index
        if settings.PROTOTYPE_INDEX_GCS_URI:
            cache = settings.CACHE_DIR
            npy_local = f"{cache}/prototype_index.npy"
            json_local = f"{cache}/prototype_index.json"
            download_to(settings.PROTOTYPE_INDEX_GCS_URI, npy_local)
            download_to(settings.PROTOTYPE_INDEX_GCS_URI.replace(".npy", ".json"), json_local)
            self.prototype_index = load_index(npy_local, json_local)
            return

        # Priority 3: Central active prototypes (embedding .npy 다운로드)
        try:
            cc = CentralClient()
            rows = cc.fetch_active_prototypes()
            vecs = []
            item_ids = []
            for idx, r in enumerate(rows):
                item_id = int(r["item_id"])
                uri = r["embedding_gcs_uri"]
                local = f"{settings.CACHE_DIR}/emb_{item_id}_{idx}.npy"
                download_to(uri, local)
                v = np.load(local).astype(np.float32).reshape(-1)
                vecs.append(v)
                item_ids.append(item_id)
            if vecs:
                V = np.stack(vecs, axis=0)
                self.prototype_index = PrototypeIndex(
                    item_ids=np.array(item_ids, dtype=np.int32),
                    vectors=V,
                    meta={"source": "central_active_prototypes", "item_ids": item_ids},
                )
        except CentralClientError:
            self.prototype_index = None

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
                            "mask_area": 12345,
                            "top_k": [{"item_id": 101, "distance": 0.1423}, {"item_id": 109, "distance": 0.1504}],
                            "best_item_id": 101,
                            "match_distance": 0.1423,
                            "match_margin": 0.0081,
                            "state": "REVIEW",
                            "qty": 1
                        },
                        {
                            "instance_id": 2,
                            "confidence": 0.95,
                            "mask_area": 11002,
                            "top_k": [{"item_id": 205, "distance": 0.0901}, {"item_id": 207, "distance": 0.1312}],
                            "best_item_id": 205,
                            "match_distance": 0.0901,
                            "match_margin": 0.0411,
                            "state": "AUTO",
                            "qty": 1
                        }
                    ],
                    "notes": "AI_MOCK_MODE=0이면 prototype index 및 실제 추론 구현을 연결하십시오."
                }
            }

        if not self.prototype_index:
            return {"overlap_score": None, "decision": "UNKNOWN", "result_json": {"error": "prototype index not loaded"}}

        img = self._load_rgb_image_from_payload(payload)    

        # REAL 스켈레톤: 랜덤 임베딩으로 kNN 흐름만 시연
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
                "input": {"shape": list(img.shape)},
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
                        "meta_json": {"mode": "mock"}
                    }
                ]
            }
        return {"events": []}

    def _load_rgb_image_from_payload(self, payload: dict[str, Any]) -> np.ndarray:
    frame_b64 = payload.get("frame_b64")
    frame_gcs_uri = payload.get("frame_gcs_uri")

    if frame_b64:
        raw = base64.b64decode(frame_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return np.array(img)  # (H,W,3) uint8

    if frame_gcs_uri:
        local = f"{settings.CACHE_DIR}/tray_{datetime.now(timezone.utc).timestamp()}.jpg"
        download_to(frame_gcs_uri, local)
        img = Image.open(local).convert("RGB")
        return np.array(img)

    raise ValueError("frame_b64 or frame_gcs_uri required")

