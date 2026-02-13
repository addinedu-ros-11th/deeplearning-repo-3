"""
트레이 추론 모듈.
YOLO 세그멘테이션, 임베딩, kNN 매칭을 통한 트레이 추론을 담당합니다.
"""
from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any, Optional

import numpy as np
import torch
from PIL import Image

from app.core.config import settings
from app.core.constants import KNN_CONFIG, YOLO_CONFIG, EMBEDDING_CONFIG, API_TIMEOUT_CONFIG
from app.services.prototype_index import PrototypeIndex
from app.services.central_client import CentralClient
from app.services.video_processor import ensure_dir

scanner_logger = logging.getLogger("scanner")


def _env_int(name: str, default: int) -> int:
    """환경 변수에서 정수 값을 가져옵니다."""
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    """환경 변수에서 실수 값을 가져옵니다."""
    try:
        return float(os.getenv(name, str(default)).strip())
    except Exception:
        return default


class TrayInferenceEngine:
    """트레이 추론을 담당하는 엔진 클래스."""

    def __init__(
        self,
        yolo=None,
        encoder=None,
        emb_tfm=None,
        prototype_index: Optional[PrototypeIndex] = None,
        prototype_set_id: Optional[int] = None,
        mock: bool = False,
        use_job_queue: bool = True,
    ):
        self.yolo = yolo
        self.encoder = encoder
        self.emb_tfm = emb_tfm
        self.prototype_index = prototype_index
        self.prototype_set_id = prototype_set_id
        self.mock = mock
        self.use_job_queue = use_job_queue

        # KNN 설정
        self.knn_topk = _env_int("KNN_TOPK", KNN_CONFIG.TOP_K)
        self.unknown_dist_th = _env_float("UNKNOWN_DIST_TH", KNN_CONFIG.UNKNOWN_DISTANCE_THRESHOLD)
        self.margin_th = _env_float("MARGIN_TH", KNN_CONFIG.MARGIN_THRESHOLD)

        # YOLO 설정
        self.yolo_imgsz = _env_int("YOLO_IMGSZ", YOLO_CONFIG.IMAGE_SIZE)
        self.yolo_conf = _env_float("YOLO_CONF", YOLO_CONFIG.CONFIDENCE_THRESHOLD)
        self.yolo_iou = _env_float("YOLO_IOU", YOLO_CONFIG.IOU_THRESHOLD)
        self.ai_device = os.getenv("AI_DEVICE", "cpu").strip() or "cpu"

        # 임베딩 설정
        self.emb_device = os.getenv("EMB_DEVICE", self.ai_device).strip() or "cpu"

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        트레이 추론을 수행합니다.

        기대 payload:
          - session_uuid: str
          - attempt_no: int (1..3)
          - store_code: str
          - device_code: str
          - frame_b64: str (dataURL 포함 가능)
        """
        session_uuid = str(payload.get("session_uuid") or "").strip()
        store_code = str(payload.get("store_code") or "").strip()
        device_code = str(payload.get("device_code") or "").strip()
        attempt_no = int(payload.get("attempt_no") or 1)

        scanner_logger.info(
            "[scanner] 추론 요청 수신: session=%s, store=%s, device=%s, attempt=%d",
            session_uuid, store_code, device_code, attempt_no,
        )

        if not session_uuid or not store_code or not device_code:
            raise ValueError("session_uuid/store_code/device_code are required")

        # 1) 프레임 decode (+ 원본 bytes 확보)
        frame_bytes, img = self._decode_frame(payload)

        # 2) 로컬 저장 (PC#2 관리자 디버깅/리뷰용)
        local_path = self._save_tray_frame(session_uuid, attempt_no, frame_bytes)

        # 3) MOCK 모드
        if self.mock:
            res = self._create_mock_result(local_path)
            if not self.use_job_queue:
                self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # 4) prototype index 없으면 UNKNOWN
        if not self.prototype_index:
            scanner_logger.warning(
                "[scanner] 추론 실패: prototype_index가 로드되지 않음 (session=%s)",
                session_uuid,
            )
            res = self._create_unknown_result(local_path, "prototype index not loaded")
            if not self.use_job_queue:
                self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # 5) YOLO seg -> crop -> embedding -> kNN -> gating
        instances = self._infer_instances(img)

        if not instances:
            res = self._create_unknown_result(local_path, "no detections")
            scanner_logger.warning(
                "[scanner] 미감지: session=%s, reason=no detections",
                session_uuid,
            )
            if not self.use_job_queue:
                self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # decision 정책
        res = self._create_inference_result(img, instances, local_path, session_uuid)

        if not self.use_job_queue:
            self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
        return res

    def _create_mock_result(self, local_path: str) -> dict[str, Any]:
        """MOCK 결과를 생성합니다."""
        return {
            "overlap_score": 0.12,
            "decision": "REVIEW",
            "result_json": {
                "mode": "mock",
                "local_frame_path": local_path,
                "prototype_set_id": self.prototype_set_id,
                "instances": [
                    {
                        "instance_id": 1,
                        "confidence": 0.92,
                        "bbox": [120, 80, 260, 210],
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

    def _create_unknown_result(self, local_path: str, error: str) -> dict[str, Any]:
        """UNKNOWN 결과를 생성합니다."""
        return {
            "overlap_score": None,
            "decision": "UNKNOWN",
            "result_json": {
                "mode": "real",
                "error": error,
                "local_frame_path": local_path,
                "prototype_set_id": self.prototype_set_id,
                "instances": [],
                "items": [],
            },
        }

    def _create_inference_result(
        self,
        img: np.ndarray,
        instances: list[dict],
        local_path: str,
        session_uuid: str,
    ) -> dict[str, Any]:
        """추론 결과를 생성합니다."""
        states = [it["state"] for it in instances]
        if all(s == "UNKNOWN" for s in states):
            decision = "UNKNOWN"
        elif any(s != "AUTO" for s in states):
            decision = "REVIEW"
        else:
            decision = "AUTO"

        # items 집계
        item_map = {}
        for it in instances:
            iid = int(it["best_item_id"])
            item_map[iid] = item_map.get(iid, 0) + int(it.get("qty", 1))
        items = [{"item_id": k, "qty": v} for k, v in item_map.items()]

        # 겹침 점수 계산
        overlap_score = self._calculate_overlap_score(instances)
        scanner_logger.info(f"[scanner] 겹침 점수: {overlap_score:.4f}")

        h, w = int(img.shape[0]), int(img.shape[1])
        res = {
            "overlap_score": overlap_score,
            "decision": decision,
            "result_json": {
                "mode": "real",
                "local_frame_path": local_path,
                "prototype_set_id": self.prototype_set_id,
                "input": {"shape": [h, w, int(img.shape[2])]},
                "instances": instances,
                "items": items,
                "overlap_score": overlap_score,
            },
        }

        # 추론 결과 로깅
        self._log_inference_result(decision, instances, items, session_uuid)

        return res

    def _log_inference_result(
        self,
        decision: str,
        instances: list[dict],
        items: list[dict],
        session_uuid: str,
    ) -> None:
        """추론 결과를 로깅합니다."""
        if decision in ("AUTO", "REVIEW"):
            scanner_logger.info(
                "[scanner] 추론 성공: session=%s, decision=%s, instances=%d, items=%d",
                session_uuid, decision, len(instances), len(items),
            )
            for inst in instances:
                scanner_logger.info(
                    "[scanner] 추론 결과: instance_id=%d, item_id=%d, label=%s, "
                    "confidence=%.3f, distance=%.4f, margin=%.4f, state=%s",
                    inst["instance_id"],
                    inst["best_item_id"],
                    inst["label_text"],
                    inst["confidence"],
                    inst["match_distance"],
                    inst["match_margin"],
                    inst["state"],
                )
            scanner_logger.info(
                "[scanner] 최종 집계: session=%s, items=%s",
                session_uuid, items,
            )
        elif decision == "UNKNOWN":
            scanner_logger.warning(
                "[scanner] 미감지: session=%s, reason=all instances unknown, instances=%d",
                session_uuid, len(instances),
            )

    def _decode_frame(self, payload: dict[str, Any]) -> tuple[bytes, np.ndarray]:
        """프레임을 디코딩합니다."""
        frame_b64 = payload.get("frame_b64")
        if not frame_b64:
            raise ValueError("frame_b64 required")

        s = str(frame_b64).strip()
        if s.startswith("data:") and "," in s:
            s = s.split(",", 1)[1]

        raw = base64.b64decode(s)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return raw, np.array(img)

    def _save_tray_frame(self, session_uuid: str, attempt_no: int, frame_bytes: bytes) -> str:
        """트레이 프레임을 저장합니다."""
        base_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "tray", session_uuid)
        ensure_dir(base_dir)
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
        """Central 서버에 결과를 업로드합니다."""
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
                timeout_s=API_TIMEOUT_CONFIG.DEFAULT_TIMEOUT_SECONDS,
            )
        except Exception as e:
            scanner_logger.warning(f"[scanner] Central server과 통신이 실패했습니다: {e}")

    @staticmethod
    def _compute_iou(box1: list, box2: list) -> float:
        """두 bounding box의 IoU를 계산합니다."""
        x1_inter = max(box1[0], box2[0])
        y1_inter = max(box1[1], box2[1])
        x2_inter = min(box1[2], box2[2])
        y2_inter = min(box1[3], box2[3])

        inter_width = max(0, x2_inter - x1_inter)
        inter_height = max(0, y2_inter - y1_inter)
        inter_area = inter_width * inter_height

        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union_area = area1 + area2 - inter_area

        if union_area <= 0:
            return 0.0
        return inter_area / union_area

    def _calculate_overlap_score(self, instances: list[dict]) -> float:
        """모든 인스턴스 쌍의 IoU 중 최대값을 반환합니다."""
        if len(instances) < 2:
            return 0.0

        boxes = [inst["bbox"] for inst in instances if "bbox" in inst]
        if len(boxes) < 2:
            return 0.0

        max_iou = 0.0
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                iou = self._compute_iou(boxes[i], boxes[j])
                max_iou = max(max_iou, iou)

        return max_iou

    @torch.no_grad()
    def _embed_crop_resnet50(self, crop: np.ndarray, dim: int) -> np.ndarray:
        """ResNet50 임베딩으로 변환합니다."""
        if self.encoder is None or self.emb_tfm is None:
            return self._embed_crop_simple(crop, dim)

        if crop is None or crop.size == 0:
            return np.zeros((dim,), dtype=np.float32)

        im = Image.fromarray(crop.astype(np.uint8)).convert("RGB")
        x = self.emb_tfm(im).unsqueeze(0).to(self.emb_device)
        y = self.encoder(x)
        y = y / (y.norm(dim=1, keepdim=True) + 1e-12)

        v = y.squeeze(0).detach().cpu().numpy().astype(np.float32)

        if v.shape[0] != dim:
            return self._embed_crop_simple(crop, dim)

        return v

    def _embed_crop_simple(self, crop: np.ndarray, dim: int) -> np.ndarray:
        """간단한 임베딩을 생성합니다 (fallback)."""
        if dim <= 0:
            return np.zeros((0,), dtype=np.float32)

        if crop is None or crop.size == 0:
            return np.zeros((dim,), dtype=np.float32)

        try:
            im = Image.fromarray(crop.astype(np.uint8)).convert("RGB").resize((32, 32))
            arr = np.asarray(im).astype(np.float32) / 255.0
            flat = arr.reshape(-1)
        except Exception:
            return np.zeros((dim,), dtype=np.float32)

        seg = int(np.ceil(flat.size / dim)) if dim > 0 else 1
        if seg <= 0:
            seg = 1
        pad = dim * seg - flat.size
        if pad > 0:
            flat = np.pad(flat, (0, pad), mode="constant")
        v = flat.reshape(dim, seg).mean(axis=1).astype(np.float32)

        n = float(np.linalg.norm(v) + 1e-12)
        v = v / n
        return v

    def _infer_instances(self, img: np.ndarray) -> list[dict[str, Any]]:
        """YOLO seg -> crop -> embedding -> kNN -> gating을 수행합니다."""
        if not self.prototype_index:
            return []

        if self.yolo is None:
            return []

        H, W = int(img.shape[0]), int(img.shape[1])
        out: list[dict[str, Any]] = []

        try:
            results = self.yolo.predict(
                source=img,
                imgsz=self.yolo_imgsz,
                conf=self.yolo_conf,
                iou=self.yolo_iou,
                device=self.ai_device,
                verbose=False,
            )
        except Exception:
            return []

        if not results:
            return []

        inst_id = 1
        for r in results:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue

            xyxy = getattr(boxes, "xyxy", None)
            conf = getattr(boxes, "conf", None)

            if xyxy is None:
                continue

            xyxy_np = xyxy.detach().cpu().numpy() if hasattr(xyxy, "detach") else np.array(xyxy)
            conf_np = None
            if conf is not None:
                conf_np = conf.detach().cpu().numpy() if hasattr(conf, "detach") else np.array(conf)

            for i in range(xyxy_np.shape[0]):
                x1, y1, x2, y2 = xyxy_np[i].tolist()

                x1i = max(0, min(W - 1, int(x1)))
                y1i = max(0, min(H - 1, int(y1)))
                x2i = max(0, min(W, int(x2)))
                y2i = max(0, min(H, int(y2)))

                if x2i <= x1i or y2i <= y1i:
                    continue

                c = float(conf_np[i]) if conf_np is not None and i < len(conf_np) else 0.0

                crop = img[y1i:y2i, x1i:x2i]
                q = self._embed_crop_resnet50(crop, self.prototype_index.vectors.shape[1])

                topk = self.prototype_index.knn(q, k=self.knn_topk)
                if not topk:
                    continue

                best_item, d1 = topk[0]
                d2 = topk[1][1] if len(topk) > 1 else (d1 + 1.0)
                margin = float(d2 - d1)

                if float(d1) > float(self.unknown_dist_th):
                    state = "UNKNOWN"
                else:
                    state = "AUTO" if margin >= float(self.margin_th) else "REVIEW"

                out.append({
                    "instance_id": inst_id,
                    "confidence": float(c),
                    "bbox": [x1i, y1i, x2i, y2i],
                    "label_text": f"item-{int(best_item)}",
                    "top_k": [{"item_id": int(ii), "distance": float(dd)} for ii, dd in topk],
                    "best_item_id": int(best_item),
                    "match_distance": float(d1),
                    "match_margin": margin,
                    "state": state,
                    "qty": 1,
                })
                inst_id += 1

        return out
