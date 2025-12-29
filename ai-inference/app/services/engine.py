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

import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights
from ultralytics import YOLO

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


class InferenceEngine:
    def __init__(self) -> None:
        self.mock = str(getattr(settings, "AI_MOCK_MODE", "0")).strip().lower() in ("1", "true", "yes", "y", "on")
        self.prototype_index: PrototypeIndex | None = None

        self.yolo = None
        self.embed_model = None
        self.embed_tf = None
        self.device = "cpu"

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

        self._load_models()

        D = int(self.prototype_index.vectors.shape[1])
        if D != 2048:
            raise ValueError(f"prototype dim mismatch: {D} (expected 2048)")

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
                            "mask_area": 12345,
                            "top_k": [{"item_id": 1, "distance": 0.1423}, {"item_id": 2, "distance": 0.1504}],
                            "best_item_id": 1,
                            "match_distance": 0.1423,
                            "match_margin": 0.0081,
                            "state": "REVIEW",
                            "qty": 1
                        },
                        {
                            "instance_id": 2,
                            "confidence": 0.95,
                            "mask_area": 11002,
                            "top_k": [{"item_id": 3, "distance": 0.0901}, {"item_id": 4, "distance": 0.1312}],
                            "best_item_id": 3,
                            "match_distance": 0.0901,
                            "match_margin": 0.0411,
                            "state": "AUTO",
                            "qty": 1
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

        # 5) YOLO seg -> crop -> embedding -> kNN -> gating
        instances = self._infer_instances(img)

        if not instances:
            res = {
                "overlap_score": None,
                "decision": "UNKNOWN",
                "result_json": {
                    "mode": "real",
                    "local_frame_path": local_path,
                    "instances": [],
                    "items": [],
                    "error": "no detections",
                },
            }
            self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # decision 정책(권장):
        # - 하나라도 REVIEW/UNKNOWN 있으면 REVIEW
        # - 전부 AUTO면 AUTO
        # - 전부 UNKNOWN이면 UNKNOWN
        states = [it["state"] for it in instances]
        if all(s == "UNKNOWN" for s in states):
            decision = "UNKNOWN"
        elif any(s != "AUTO" for s in states):
            decision = "REVIEW"
        else:
            decision = "AUTO"

        # items 집계(UNKNOWN 제외)
        item_map = {}
        for it in instances:
            if it["state"] == "UNKNOWN":
                continue
            iid = int(it["best_item_id"])
            item_map[iid] = item_map.get(iid, 0) + int(it.get("qty", 1))
        items = [{"item_id": k, "qty": v} for k, v in item_map.items()]

        h, w = int(img.shape[0]), int(img.shape[1])
        res = {
            "overlap_score": 0.0,
            "decision": decision,
            "result_json": {
                "mode": "real",
                "local_frame_path": local_path,
                "input": {"shape": [h, w, int(img.shape[2])]},
                "instances": instances,
                "items": items,
            },
        }
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

    def _load_models(self) -> None:
        # device
        self.device = getattr(settings, "AI_DEVICE", "cpu")  # 없으면 cpu

        # YOLO seg
        yolo_path = getattr(settings, "YOLO_SEG_MODEL_PATH", None)
        if not yolo_path:
            raise ValueError("YOLO_SEG_MODEL_PATH is required for real inference")
        self.yolo = YOLO(yolo_path)

        # ResNet50 embedder
        w = ResNet50_Weights.IMAGENET1K_V2
        m = models.resnet50(weights=w)
        m.fc = nn.Identity()
        m.eval()
        m.to(self.device)
        self.embed_model = m

        self.embed_tf = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406),
                                std=(0.229, 0.224, 0.225)),
        ])

    def _l2norm(self, v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
        n = np.linalg.norm(v) + eps
        return (v / n).astype(np.float32)

    @torch.no_grad()
    def _embed_rgb(self, crop_rgb: np.ndarray) -> np.ndarray:
        # crop_rgb: (H,W,3) RGB
        pil = Image.fromarray(crop_rgb).convert("RGB")
        x = self.embed_tf(pil).unsqueeze(0).to(self.device)  # (1,3,224,224)
        y = self.embed_model(x)  # (1,2048)
        v = y.squeeze(0).detach().cpu().numpy().astype(np.float32)
        return self._l2norm(v)

    def _masked_crop_rgb(self, img_rgb: np.ndarray, mask: np.ndarray, box: np.ndarray) -> np.ndarray:
        h, w = img_rgb.shape[:2]

        x1, y1, x2, y2 = box.astype(int).tolist()
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        if x2 <= x1: x2 = min(w, x1 + 1)
        if y2 <= y1: y2 = min(h, y1 + 1)

        # mask shape 맞추기
        if mask.shape[0] != h or mask.shape[1] != w:
            mask = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)

        crop = img_rgb[y1:y2, x1:x2].copy()
        m = mask[y1:y2, x1:x2]

        if m.max() > 1:
            m = (m > 127).astype(np.uint8)
        else:
            m = (m > 0).astype(np.uint8)

        bg = np.full_like(crop, 255, dtype=np.uint8)
        m3 = np.repeat(m[:, :, None], 3, axis=2)
        out = np.where(m3 == 1, crop, bg)
        return out
    
    def _gate(self, d1: float, d2: float) -> tuple[str, float]:
        unknown_th = float(getattr(settings, "UNKNOWN_DIST_TH", 0.35))
        margin_th = float(getattr(settings, "MARGIN_TH", 0.03))
        margin = float(d2 - d1)

        if d1 > unknown_th:
            return "UNKNOWN", margin
        if margin < margin_th:
            return "REVIEW", margin
        return "AUTO", margin

    def _infer_instances(self, img_rgb: np.ndarray) -> list[dict[str, Any]]:
        if not self.yolo or not self.embed_model or not self.prototype_index:
            return []

        # Ultralytics는 numpy 입력이 BGR 기준인 케이스가 있어 안전하게 변환
        img_bgr = img_rgb[:, :, ::-1].copy()

        # YOLO seg
        res = self.yolo.predict(
            source=img_bgr,
            imgsz=int(getattr(settings, "YOLO_IMGSZ", 640)),
            conf=float(getattr(settings, "YOLO_CONF", 0.25)),
            iou=float(getattr(settings, "YOLO_IOU", 0.7)),
            device=self.device,
            verbose=False,
        )[0]

        if res.masks is None or res.boxes is None or len(res.boxes) == 0:
            return []

        masks = res.masks.data.detach().cpu().numpy()  # (n,H,W)
        boxes = res.boxes.xyxy.detach().cpu().numpy()  # (n,4)
        confs = res.boxes.conf.detach().cpu().numpy()  # (n,)

        instances: list[dict[str, Any]] = []
        k = int(getattr(settings, "KNN_TOPK", 5))

        for i in range(len(confs)):
            crop_rgb = self._masked_crop_rgb(img_rgb, masks[i], boxes[i])
            q = self._embed_rgb(crop_rgb)

            topk = self.prototype_index.knn(q, k=k)  # [(item_id, dist), ...]
            if not topk:
                continue

            best_item, d1 = topk[0]
            d2 = topk[1][1] if len(topk) > 1 else (d1 + 1.0)

            state, margin = self._gate(float(d1), float(d2))

            # label_text는 “다른 서비스가 DB 조인”이므로 의미 없게 두는 게 안전합니다.
            # 기존 클라이언트가 필드를 기대하면 빈 문자열 정도로 유지하세요.
            instances.append({
                "instance_id": len(instances) + 1,
                "confidence": float(confs[i]),
                "bbox": [int(x) for x in boxes[i].tolist()],
                "label_text": "",  # 또는 f"item-{int(best_item)}"
                "top_k": [{"item_id": int(it), "distance": float(d)} for it, d in topk],
                "best_item_id": int(best_item),
                "match_distance": float(d1),
                "match_margin": float(margin),
                "state": state,
                "qty": 1,
            })

        return instances
