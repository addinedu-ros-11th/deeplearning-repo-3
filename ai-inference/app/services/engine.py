from __future__ import annotations

import base64
import io
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import settings
from app.services.prototype_index import PrototypeIndex, load_index
from app.services.central_client import CentralClient
from app.util.gcs_utils import upload_to_gcs
from dotenv import load_dotenv
import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights
from ultralytics import YOLO

from app.util.preprocessing.violence_classification import ViolenceClassification
from app.util.preprocessing.fall_down_detection import FallDownDetection
from app.util.preprocessing.auxiliary_tools import AuxiliaryTools

import sys
from YOLOwrapper import FallDownDetection as FallDownDetectionWrapper, YOLOWrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

sys.modules['__main__'].FallDownDetection = FallDownDetectionWrapper
sys.modules['__main__'].YOLOWrapper = YOLOWrapper

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

load_dotenv()

class InferenceEngine:
    def __init__(self) -> None:
        self.mock = bool(settings.AI_MOCK_MODE)
        self.prototype_index: PrototypeIndex | None = None

        self.yolo = None
        self.embed_model = None
        self.embed_tf = None
        self.device = "gpu"

        self.violence_classifier: ViolenceClassification | None = None
        self.fall_detector: FallDownDetection | None = None
        self.auxiliary_detector: AuxiliaryTools | None = None

    def startup_load(self) -> None:
        if self.mock:
            return

        # CCTV 폭력 감지 모델 로드 (GCS에서)
        try:
            self.violence_classifier = ViolenceClassification()
        except Exception as e:
            logging.warning(f"ViolenceClassification 로드 실패: {e}")
            self.violence_classifier = None

        # CCTV 낙상 감지 모델 로드 (GCS에서)
        try:
            self.fall_detector = FallDownDetection()
        except Exception as e:
            logging.warning(f"FallDownDetection 로드 실패: {e}")
            self.fall_detector = None

        # CCTV Auxiliary 감지 모델 로드 (GCS에서)
        try:
            self.auxiliary_detector = AuxiliaryTools()
        except Exception as e:
            logging.warning(f"AuxiliaryTools 로드 실패: {e}")
            self.auxiliary_detector = None

        # 이번 데모 정책: prototype은 로컬에서 관리 (Central/GCS에서 끌어오지 않음)
        if not settings.PROTOTYPE_INDEX_PATH:
            self.prototype_index = None
            return

        npy = settings.PROTOTYPE_INDEX_PATH
        meta = npy.replace(".npy", ".json")
        self.prototype_index = load_index(npy, meta)

        self._load_models()

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
        """CCTV 폭력/낙상 감지 추론"""
        now = datetime.now(timezone.utc)

        if self.mock:
            return {
                "events": [
                    {
                        "event_type": "VIOLENCE",
                        "confidence": 0.88,
                        "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                        "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                        "meta_json": {"mode": "mock"},
                    },
                    {
                        "event_type": "FALL",
                        "confidence": 0.92,
                        "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                        "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                        "meta_json": {"mode": "mock"},
                    },
                    {
                        "event_type": "AUXILIARY",
                        "confidence": 0.90,
                        "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                        "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                        "meta_json": {"mode": "mock"},
                    }
                ]
            }

        # 공통 변수
        store_code = payload.get("store_code", "")
        device_code = payload.get("device_code", "")
        clip_local_path = payload.get("clip_local_path")
        frames_b64 = payload.get("frames_b64")
        GCS_BUCKET_CCTV = os.getenv("GCS_BUCKET_CCTV")

        if clip_local_path:
            frames, fps, width, height = self._decode_video(clip_local_path)
        elif frames_b64:
            frames = self._decode_b64_frames(frames_b64)
            fps = 15
            if frames:
                height, width = frames[0].shape[:2]
            else:
                height, width = 0, 0
        else:
            frames, fps, width, height = [], 30, 0, 0

        if not frames:
            return {"events": []}

        events = []
        tasks = []

        if self.violence_classifier:
            tasks.append(("VIOLENCE", self._run_violence_inference_frames))

        if self.fall_detector:
            tasks.append(("FALL", self._run_fall_inference_frames))

        if self.auxiliary_detector:
            tasks.append(("WHEELCHAIR", self._run_auxiliary_inference_frames))

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_type = {
                executor.submit(func, frames, fps, width, height, now): event_type
                for event_type, func in tasks
            }

            for future in as_completed(future_to_type):
                event_type = future_to_type[future]
                try:
                    result = future.result()

                    if event_type == "VIOLENCE" and result["is_violence"]:
                        detected = True
                    elif event_type == "FALL" and result["is_fall"]:
                        detected = True
                    elif event_type == "WHEELCHAIR" and result["detected"]:
                        detected = True
                    else:
                        detected = False
                    
                    if detected:
                        event = self._process_cctv_event(
                                event_type=event_type,
                                inference_result=result,
                                now=now,
                                store_code=store_code,
                                device_code=device_code,
                                gcs_bucket=GCS_BUCKET_CCTV,
                            )
                        if event:
                            events.append(event)
                except Exception as e:
                    logging.warning(f"{event_type} 추론 실패: {e}")

        return {"events": events}

    def _process_cctv_event(
        self,
        event_type: str,
        inference_result: dict[str, Any],
        now: datetime,
        store_code: str,
        device_code: str,
        gcs_bucket: str,
    ) -> dict[str, Any] | None:
        """CCTV 이벤트 처리 (GCS 업로드 + Central API 저장)"""
        local_clip_path = inference_result.get("local_clip_path")
        confidence = inference_result.get("confidence", 0.0)
        extra_meta = inference_result.get("extra_meta", {})

        gcs_uri = None

        # GCS 업로드
        if local_clip_path and os.path.exists(local_clip_path):
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            # FALL -> fall_down 으로 변환 (일관성 유지)
            event_name = "fall_down" if event_type == "FALL" else event_type.lower()
            blob_name = f"cctv_{event_name}_{timestamp}.mp4"
            try:
                gcs_uri = upload_to_gcs(local_clip_path, gcs_bucket, blob_name)
            except Exception as e:
                logging.warning(f"GCS 업로드 실패 ({event_type}): {e}")

        # 이벤트 데이터 생성
        event_data = {
            "event_type": event_type,
            "confidence": confidence,
            "started_at": now.replace(tzinfo=None).isoformat(sep=" "),
            "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
            "meta_json": {
                "mode": "real",
                "clip_path": local_clip_path,
                "gcs_uri": gcs_uri,
                **extra_meta,
            },
        }

        # Central API에 이벤트 저장
        if gcs_uri and store_code and device_code:
            self._try_ingest_cctv_event(
                store_code=store_code,
                device_code=device_code,
                event_data=event_data,
                gcs_uri=gcs_uri,
            )

        return event_data

    def _run_violence_inference_frames(
        self,
        frames: list[np.ndarray],
        fps: int,
        width: int,
        height: int,
        now: datetime,
    ) -> dict[str, Any]:
        """공유 프레임으로 폭력 감지 추론"""
        self.violence_classifier._reset()

        probabilities = []
        violence_detected = False
        violence_frame = None
        frame_interval = 3

        for i, frame in enumerate(frames):
            if i % frame_interval != 0:
                continue

            result = self.violence_classifier.process_frame(frame)
            if result.get("ready"):
                prob = result.get("probability", 0.0)
                probabilities.append(prob)
                if prob >= self.violence_classifier.threshold and not violence_detected:
                    violence_detected = True
                    violence_frame = i

        if not probabilities:
            return {"is_violence": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

        if violence_detected:
            # 클립 저장 (감지 시점 ±5초)
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            local_clip_dir = os.path.join(settings.CACHE_DIR, "violence_clips")
            _ensure_dir(local_clip_dir)
            local_clip_path = os.path.join(local_clip_dir, f"cctv_violence_{timestamp}.mp4")

            clip_seconds = 5
            start_frame = max(0, violence_frame - clip_seconds * fps)
            end_frame = min(len(frames), violence_frame + clip_seconds * fps)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(local_clip_path, fourcc, fps, (width, height))
            for f in frames[start_frame:end_frame]:
                out.write(f)
            out.release()

            violence_count = sum(1 for p in probabilities if p >= self.violence_classifier.threshold)
            return {
                "is_violence": True,
                "confidence": float(max(probabilities)),
                "local_clip_path": local_clip_path,
                "extra_meta": {
                    "source": "shared_frames",
                    "avg_probability": float(np.mean(probabilities)),
                    "violence_ratio": float(violence_count / len(probabilities)),
                },
            }

        return {"is_violence": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

    def _run_fall_inference_frames(
        self,
        frames: list[np.ndarray],
        fps: int,
        width: int,
        height: int,
        now: datetime,
    ) -> dict[str, Any]:
        """공유 프레임으로 낙상 감지 추론"""
        fall_detected = False
        fall_frame = None
        skip_frames = 0

        for i, frame in enumerate(frames):
            if skip_frames > 0:
                skip_frames -= 1
                continue

            result = self.fall_detector.process_frame(frame)

            if result.get("is_fall") and not fall_detected:
                fall_detected = True
                fall_frame = i
                skip_frames = fps * 10

        if fall_detected:
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            local_clip_dir = os.path.join(settings.CACHE_DIR, "fall_clips")
            _ensure_dir(local_clip_dir)
            local_clip_path = os.path.join(local_clip_dir, f"cctv_fall_down_{timestamp}.mp4")

            clip_seconds = 5
            start_frame = max(0, fall_frame - clip_seconds * fps)
            end_frame = min(len(frames), fall_frame + clip_seconds * fps)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(local_clip_path, fourcc, fps, (width, height))
            for f in frames[start_frame:end_frame]:
                out.write(f)
            out.release()

            return {
                "is_fall": True,
                "confidence": 1.0,
                "local_clip_path": local_clip_path,
                "extra_meta": {"source": "shared_frames"},
            }

        return {"is_fall": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

    def _run_auxiliary_inference_frames(
        self,
        frames: list[np.ndarray],
        fps: int,
        width: int,
        height: int,
        now: datetime,
    ) -> dict[str, Any]:
        """공유 프레임으로 Auxiliary 감지 추론"""
        detected = False
        detected_frame = None
        skip_frames = 0

        for i, frame in enumerate(frames):
            if skip_frames > 0:
                skip_frames -= 1
                continue

            result = self.auxiliary_detector.process_frame(frame)

            if result.get("detected") and not detected:
                detected = True
                detected_frame = i
                skip_frames = fps * 10

        if detected:
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            local_clip_dir = os.path.join(settings.CACHE_DIR, "auxiliary_clips")
            _ensure_dir(local_clip_dir)
            local_clip_path = os.path.join(local_clip_dir, f"cctv_auxiliary_{timestamp}.mp4")

            clip_seconds = 5
            start_frame = max(0, detected_frame - clip_seconds * fps)
            end_frame = min(len(frames), detected_frame + clip_seconds * fps)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(local_clip_path, fourcc, fps, (width, height))
            for f in frames[start_frame:end_frame]:
                out.write(f)
            out.release()

            return {
                "detected": True,
                "confidence": 1.0,
                "local_clip_path": local_clip_path,
                "extra_meta": {"source": "shared_frames"},
            }

        return {"detected": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

    # -----------------------------
    # helpers
    # -----------------------------
    def _decode_video(self, path: str) -> tuple[list, int, int, int]:
        """비디오를 한 번만 디코딩하여 프레임 리스트 반환"""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return [], 30, 0, 0

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()

        return frames, fps, width, height

    def _decode_b64_frames(self, frames_b64: list[str]) -> list[np.ndarray]:
        """Base64 프레임들을 디코딩"""
        decoded_frames = []
        for frame_b64 in frames_b64:
            frame_bytes, frame_rgb = self._decode_frame({"frame_b64": frame_b64})
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            decoded_frames.append(frame_bgr)
        return decoded_frames

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

    def _try_ingest_cctv_event(
        self,
        store_code: str,
        device_code: str,
        event_data: dict[str, Any],
        gcs_uri: str,
    ) -> None:
        """CCTV 이벤트를 Central API에 저장 시도"""
        try:
            cc = CentralClient()
            cc.ingest_cctv_event(
                store_code=store_code,
                device_code=device_code,
                event_type=event_data.get("event_type", "VIOLENCE"),
                confidence=event_data.get("confidence", 0.0),
                started_at=event_data.get("started_at"),
                ended_at=event_data.get("ended_at"),
                clip_gcs_uri=gcs_uri,
                clip_start_at=event_data.get("started_at"),
                clip_end_at=event_data.get("ended_at"),
                meta_json=event_data.get("meta_json"),
                timeout_s=3.0,
            )
        except Exception as e:
            logging.warning(f"Central API CCTV 이벤트 저장 실패: {e}")

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
