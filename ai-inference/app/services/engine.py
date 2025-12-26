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
from app.services.central_client import CentralClient


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


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
        """
        기대 payload:
          - session_uuid: str
          - attempt_no: int (1..3)
          - store_code: str
          - device_code: str
          - frame_b64: str (dataURL 포함 가능)
        """
        # (schemas.py에서 required로 막지만, 안전망)
        session_uuid = str(payload.get("session_uuid") or "").strip()
        store_code = str(payload.get("store_code") or "").strip()
        device_code = str(payload.get("device_code") or "").strip()
        attempt_no = int(payload.get("attempt_no") or 1)

        if not session_uuid or not store_code or not device_code:
            raise ValueError("session_uuid/store_code/device_code are required")

        # 1) 프레임 decode (+ 원본 bytes 확보)
        frame_bytes, img = self._decode_frame(payload)

        # 2) 로컬 저장 (PC#2 관리자 디버깅/리뷰용)
        local_path = self._save_tray_frame(session_uuid, attempt_no, frame_bytes)

        # 3) MOCK 모드
        if self.mock:
            res = {
                "overlap_score": 0.12,
                "decision": "REVIEW",
                "result_json": {
                    "mode": "mock",
                    "local_frame_path": local_path,  # (선택) 중앙에 저장돼도 PC#2에서만 의미 있음
                    "instances": [
                        {
                            "instance_id": 1,
                            "confidence": 0.92,
                            "bbox": [120, 80, 260, 210],   # [x1,y1,x2,y2]
                            "label_text": "Plain Bagel",
                            "top_k": [
                                {"item_id": 101, "distance": 0.1423},
                                {"item_id": 109, "distance": 0.1504},
                            ],
                            "best_item_id": 101,
                            "match_distance": 0.1423,
                            "match_margin": 0.0081,
                            "state": "REVIEW",
                            "qty": 1,
                        }
                    ],
                    "items": [{"item_id": 101, "qty": 1}],
                },
            }

            # ✅ Central 업로드(실패해도 로컬 응답은 유지)
            self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # 4) prototype index 없으면 UNKNOWN
        if not self.prototype_index:
            res = {
                "overlap_score": None,
                "decision": "UNKNOWN",
                "result_json": {
                    "error": "prototype index not loaded (set PROTOTYPE_INDEX_PATH)",
                    "local_frame_path": local_path,
                },
            }
            self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # 5) TODO: 다음 단계에서 YOLO seg + crop -> embedding(q) 생성으로 교체
        # 지금은 skeleton 유지: 랜덤 임베딩으로 knn 흐름만 유지
        D = self.prototype_index.vectors.shape[1]
        q = np.random.randn(D).astype(np.float32)

        topk = self.prototype_index.knn(q, k=5)
        best_item, d1 = topk[0]
        d2 = topk[1][1] if len(topk) > 1 else (d1 + 1.0)
        margin = float(d2 - d1)

        state = "AUTO" if margin >= 0.03 else "REVIEW"
        decision = "AUTO" if state == "AUTO" else "REVIEW"

        # 옵션 A(좌표 오버레이): bbox 더미라도 포함 (YOLO 붙이면 실제 bbox/mask로 대체)
        h, w = int(img.shape[0]), int(img.shape[1])
        dummy_bbox = [int(w * 0.1), int(h * 0.1), int(w * 0.3), int(h * 0.3)]

        res = {
            "overlap_score": 0.0,
            "decision": decision,
            "result_json": {
                "mode": "real_skeleton",
                "local_frame_path": local_path,
                "input": {"shape": [h, w, int(img.shape[2])]},
                "instances": [
                    {
                        "instance_id": 1,
                        "confidence": 0.9,
                        "bbox": dummy_bbox,
                        "label_text": f"item-{int(best_item)}",
                        "top_k": [{"item_id": int(i), "distance": float(d)} for i, d in topk],
                        "best_item_id": int(best_item),
                        "match_distance": float(d1),
                        "match_margin": margin,
                        "state": state,
                        "qty": 1,
                    }
                ],
                "items": [{"item_id": int(best_item), "qty": 1}],
            },
        }

        # ✅ Central 업로드(실패해도 로컬 응답은 유지)
        self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
        return res

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

    # -----------------------------
    # helpers
    # -----------------------------
    def _decode_frame(self, payload: dict[str, Any]) -> tuple[bytes, np.ndarray]:
        frame_b64 = payload.get("frame_b64")
        if not frame_b64:
            raise ValueError("frame_b64 required")

        s = str(frame_b64).strip()

        # data URL prefix 제거
        if s.startswith("data:") and "," in s:
            s = s.split(",", 1)[1]

        raw = base64.b64decode(s)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return raw, np.array(img)

    def _save_tray_frame(self, session_uuid: str, attempt_no: int, frame_bytes: bytes) -> str:
        """
        로컬 저장:
          {CACHE_DIR}/tray/{session_uuid}/attempt_{attempt_no}.jpg
        """
        base_dir = os.path.join(settings.CACHE_DIR, "tray", session_uuid)
        _ensure_dir(base_dir)
        path = os.path.join(base_dir, f"attempt_{attempt_no}.jpg")
        with open(path, "wb") as f:
            f.write(frame_bytes)
        return path

    def _try_ingest_to_central(
        self,
        session_uuid: str,
        store_code: str,
        device_code: str,
        attempt_no: int,
        res: dict[str, Any],
    ) -> None:
        """
        정책: infer 발생하면 항상 Central 업로드 시도.
        단, Central 장애가 로컬 추론을 막으면 안 되므로 예외는 삼킴.
        """
        try:
            cc = CentralClient()
            cc.ingest_tray_result(
                session_uuid=session_uuid,
                payload={
                    "attempt_no": attempt_no,
                    "store_code": store_code,
                    "device_code": device_code,
                    "overlap_score": res.get("overlap_score"),
                    "decision": res.get("decision"),
                    "result_json": res.get("result_json", {}),
                },
                timeout_s=3.0,  # 데모: 짧게(로컬 UX 보호)
            )
        except Exception:
            pass
