from __future__ import annotations

import base64
import io
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
from PIL import Image

from app.core.config import settings
from app.services.prototype_index import PrototypeIndex, load_index
from app.services.central_client import CentralClient
from app.services.gcs_utils import download_to


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)).strip())
    except Exception:
        return default


    def _resolve_yolo_local_path(self) -> str | None:
        # 1) 로컬 경로 우선
        yolo_path = (
            os.getenv("YOLO_MODEL_PATH", "").strip()
            or str(getattr(settings, "YOLO_MODEL_PATH", "") or "").strip()
        )
        if yolo_path:
            return yolo_path

        # 2) URI로 받으면 캐시에 내려받음
        yolo_uri = (
            os.getenv("YOLO_MODEL_URI", "").strip()
            or str(getattr(settings, "YOLO_MODEL_URI", "") or "").strip()
        )
        if not yolo_uri:
            return None

        cache_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "models")
        _ensure_dir(cache_dir)

        parsed = urlparse(yolo_uri)
        filename = os.path.basename(parsed.path) or "yolo.pt"
        local_path = os.path.join(cache_dir, filename)

        # 이미 있으면 재사용
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return local_path

        # gs:// 또는 https:// 등 다운로드
        download_to(yolo_uri, local_path)
        return local_path


class InferenceEngine:
    def __init__(self) -> None:
        self.mock = bool(getattr(settings, "AI_MOCK_MODE", False))

        self.prototype_index: PrototypeIndex | None = None
        self.prototype_set_id: int | None = None

        # YOLO model (lazy/optional)
        self.yolo = None

        # env 정책
        self.knn_topk = _env_int("KNN_TOPK", 5)
        self.unknown_dist_th = _env_float("UNKNOWN_DIST_TH", 0.35)
        self.margin_th = _env_float("MARGIN_TH", 0.03)

        self.yolo_imgsz = _env_int("YOLO_IMGSZ", 640)
        self.yolo_conf = _env_float("YOLO_CONF", 0.25)
        self.yolo_iou = _env_float("YOLO_IOU", 0.7)
        self.ai_device = os.getenv("AI_DEVICE", "cpu").strip() or "cpu"

        self.use_job_queue = os.getenv("AI_USE_JOB_QUEUE", "1").strip() == "1"


    def startup_load(self) -> None:
        if self.mock:
            return

        # 1) prototype_set 기반 통합 인덱스 로드
        try:
            npy_uri, meta_uri, psid = self._resolve_active_prototype_index_uris()
            if npy_uri and meta_uri:
                cache_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "prototype_index")
                _ensure_dir(cache_dir)

                npy_local = self._fetch_uri_to_local(npy_uri, cache_dir)
                meta_local = self._fetch_uri_to_local(meta_uri, cache_dir)

                self.prototype_index = load_index(npy_local, meta_local)
                self.prototype_set_id = psid
            else:
                self.prototype_index = None
                self.prototype_set_id = None
        except Exception:
            self.prototype_index = None
            self.prototype_set_id = None

        # 2) YOLO 로드(있으면)
        try:
            yolo_local = self._resolve_yolo_local_path()
            if yolo_local:
                from ultralytics import YOLO  # type: ignore
                self.yolo = YOLO(yolo_local)
        except Exception:
            self.yolo = None

    def infer_tray(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
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
                    "local_frame_path": local_path,
                    "prototype_set_id": self.prototype_set_id,
                    "instances": [
                        {
                            "instance_id": 1,
                            "confidence": 0.92,
                            "bbox": [120, 80, 260, 210],  # [x1,y1,x2,y2]
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
            if not self.use_job_queue:
                self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
            return res

        # 4) prototype index 없으면 UNKNOWN
        if not self.prototype_index:
            res = {
                "overlap_score": None,
                "decision": "UNKNOWN",
                "result_json": {
                    "mode": "real",
                    "error": "prototype index not loaded (ACTIVE prototype_set index URIs not resolved)",
                    "local_frame_path": local_path,
                    "prototype_set_id": self.prototype_set_id,
                    "instances": [],
                    "items": [],
                },
            }
            if not self.use_job_queue:
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
                    "prototype_set_id": self.prototype_set_id,
                    "instances": [],
                    "items": [],
                    "error": "no detections",
                },
            }
            if not self.use_job_queue:
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
                "prototype_set_id": self.prototype_set_id,
                "input": {"shape": [h, w, int(img.shape[2])]},
                "instances": instances,
                "items": items,
            },
        }
        if not self.use_job_queue:
            self._try_ingest_to_central(session_uuid, store_code, device_code, attempt_no, res)
        return res

    def infer_cctv(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        
        clip_gcs_uri = payload.get("clip_gcs_uri")
        frames_b64 = payload.get("frames_b64")
        
        # 입력 검증 (스키마에서 이미 검증되지만 추가 안전장치)
        if not clip_gcs_uri and not frames_b64:
            return {"events": []}
        
        # clip_gcs_uri가 제공된 경우 다운로드하여 처리
        local_clip_path = None
        if clip_gcs_uri:
            try:
                cache_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "cctv_clips")
                _ensure_dir(cache_dir)
                timestamp = int(now.timestamp() * 1000)
                local_clip_path = os.path.join(cache_dir, f"clip_{timestamp}.mp4")
                download_to(clip_gcs_uri, local_clip_path)
            except Exception as e:
                # 다운로드 실패 시 빈 결과 반환 (error 필드는 스키마에 없으므로 제거)
                return {"events": []}
        
        try:
            if self.mock:
                return {
                    "events": [
                        {
                            "event_type": "FALL",
                            "confidence": 0.88,
                            "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                            "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                            "meta_json": {"mode": "mock", "clip_gcs_uri": clip_gcs_uri},
                        }
                    ],
                }
            
            # TODO: 실제 비디오 처리 로직 구현
            # - clip_path_uri 또는 frames_b64를 사용하여 이벤트 감지
            # - OpenCV로 비디오 읽기 및 프레임 처리
            # - frames_b64가 제공된 경우 base64 디코딩하여 처리
            
            return {"events": []}
        finally:
            # 임시 파일 정리 (예외 발생 시에도 실행 보장)
            if local_clip_path and os.path.exists(local_clip_path):
                try:
                    os.remove(local_clip_path)
                except Exception:
                    pass

    # -----------------------------
    # YOLO seg -> crop -> embedding -> kNN -> gating
    # -----------------------------
    def _infer_instances(self, img: np.ndarray) -> list[dict[str, Any]]:
        """
        반환 instances 형식(예시):
        {
          "instance_id": 1,
          "confidence": 0.9,
          "bbox": [x1,y1,x2,y2],
          "label_text": "item-101",
          "top_k": [{"item_id": 101, "distance": 0.12}, ...],
          "best_item_id": 101,
          "match_distance": 0.12,
          "match_margin": 0.04,
          "state": "AUTO|REVIEW|UNKNOWN",
          "qty": 1
        }
        """
        if not self.prototype_index:
            return []

        if self.yolo is None:
            return []

        H, W = int(img.shape[0]), int(img.shape[1])
        out: list[dict[str, Any]] = []

        try:
            # ultralytics는 입력을 np.ndarray(BGR/RGB)로 받아도 동작하는 경우가 많지만,
            # 여기서는 PIL 경유 없이 그대로 전달합니다.
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

                # clamp + int
                x1i = max(0, min(W - 1, int(x1)))
                y1i = max(0, min(H - 1, int(y1)))
                x2i = max(0, min(W, int(x2)))
                y2i = max(0, min(H, int(y2)))

                if x2i <= x1i or y2i <= y1i:
                    continue

                c = float(conf_np[i]) if conf_np is not None and i < len(conf_np) else 0.0

                crop = img[y1i:y2i, x1i:x2i]
                q = self._embed_crop_simple(crop, self.prototype_index.vectors.shape[1])

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

                out.append(
                    {
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
                    }
                )
                inst_id += 1

        return out

    def _embed_crop_simple(self, crop: np.ndarray, dim: int) -> np.ndarray:
        """
        외부 임베딩 모델이 아직 없더라도 서버가 깨지지 않도록,
        numpy/PIL만으로 동작하는 간단한(결정론적) 임베딩을 생성합니다.
        - dim은 prototype_index의 vector dimension에 맞춥니다.
        """
        if dim <= 0:
            return np.zeros((0,), dtype=np.float32)

        if crop is None or crop.size == 0:
            v = np.zeros((dim,), dtype=np.float32)
            return v

        try:
            im = Image.fromarray(crop.astype(np.uint8)).convert("RGB").resize((32, 32))
            arr = np.asarray(im).astype(np.float32) / 255.0
            flat = arr.reshape(-1)  # 32*32*3 = 3072
        except Exception:
            v = np.zeros((dim,), dtype=np.float32)
            return v

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

    # -----------------------------
    # prototype_set 기반 로딩 helpers
    # -----------------------------
    def _resolve_active_prototype_index_uris(self) -> Tuple[str, str, Optional[int]]:
        """
        반환: (npy_uri, meta_uri, prototype_set_id)

        1) CentralClient에 get_active_prototype_set()가 구현되어 있으면 그걸 우선 사용
        2) 없으면 settings/env의 PROTOTYPE_INDEX_URI / PROTOTYPE_INDEX_META_URI 사용
        """
        # 1) Central 우선
        try:
            cc = CentralClient()
            fn = getattr(cc, "get_active_prototype_set", None)
            if callable(fn):
                data = fn(timeout_s=3.0)
                npy_uri = str(data.get("index_npy_gcs_uri") or "").strip()
                meta_uri = str(data.get("index_meta_gcs_uri") or "").strip()
                psid = data.get("prototype_set_id")
                psid = int(psid) if psid is not None and str(psid).isdigit() else None
                if npy_uri and meta_uri:
                    return npy_uri, meta_uri, psid
        except Exception:
            pass

        # 2) fallback
        npy_uri = str(getattr(settings, "PROTOTYPE_INDEX_URI", "") or "").strip()
        meta_uri = str(getattr(settings, "PROTOTYPE_INDEX_META_URI", "") or "").strip()
        return npy_uri, meta_uri, None

    def _fetch_uri_to_local(self, uri: str, cache_dir: str) -> str:
        """
        지원:
          - gs://bucket/path/file.ext
          - https://..., http://...
          - file:///abs/path/file.ext
          - /abs/path/file.ext 또는 상대경로 (scheme 없는 경우)

        다운로드/복사 후 로컬 경로 반환
        """
        u = str(uri).strip()
        if not u:
            raise ValueError("empty uri")

        parsed = urlparse(u)
        scheme = (parsed.scheme or "").lower()

        filename = os.path.basename(parsed.path) if parsed.path else "artifact.bin"
        local_path = os.path.join(cache_dir, filename)

        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return local_path

        if scheme in ("http", "https"):
            import requests
            r = requests.get(u, timeout=15)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            return local_path

        if scheme == "gs":
            try:
                from google.cloud import storage
            except Exception as e:
                raise RuntimeError("google-cloud-storage is required for gs:// uris") from e

            bucket = parsed.netloc
            blob_name = parsed.path.lstrip("/")
            client = storage.Client()
            b = client.bucket(bucket)
            blob = b.blob(blob_name)
            blob.download_to_filename(local_path)
            return local_path

        if scheme == "file":
            src = parsed.path
            if not os.path.exists(src):
                raise FileNotFoundError(src)
            with open(src, "rb") as rf, open(local_path, "wb") as wf:
                wf.write(rf.read())
            return local_path

        if scheme == "":
            src = u
            if not os.path.exists(src):
                raise FileNotFoundError(src)
            with open(src, "rb") as rf, open(local_path, "wb") as wf:
                wf.write(rf.read())
            return local_path

        raise ValueError(f"unsupported uri scheme: {scheme}")

    # -----------------------------
    # 기존 helpers
    # -----------------------------
    def _decode_frame(self, payload: dict[str, Any]) -> tuple[bytes, np.ndarray]:
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
        base_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "tray", session_uuid)
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
                timeout_s=3.0,
            )
        except Exception:
            pass
