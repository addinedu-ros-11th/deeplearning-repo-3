from __future__ import annotations

import logging
import os
from typing import Optional, Tuple
from urllib.parse import urlparse

import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights

from app.core.config import settings
from app.core.constants import EMBEDDING_CONFIG, API_TIMEOUT_CONFIG
from app.services.prototype_index import PrototypeIndex, load_index
from app.services.central_client import CentralClient
from app.services.video_processor import ensure_dir
from app.util.gcs_utils import download_to

from app.util.preprocessing.violence_classification import ViolenceClassification
from app.util.preprocessing.fall_down_detection import FallDownDetection
from app.util.preprocessing.auxiliary_tools import AuxiliaryTools

scanner_logger = logging.getLogger("scanner")


class ModelLoader:
    """모델 로딩을 담당하는 클래스."""

    def __init__(self, ai_device: str = "cpu", emb_device: str = "cpu", emb_img_size: int = 224):
        self.ai_device = ai_device
        self.emb_device = emb_device
        self.emb_img_size = emb_img_size

        self.encoder = None
        self.emb_tfm = None
        self.yolo = None
        self.prototype_index: Optional[PrototypeIndex] = None
        self.prototype_set_id: Optional[int] = None

        self.violence_classifier: Optional[ViolenceClassification] = None
        self.fall_detector: Optional[FallDownDetection] = None
        self.auxiliary_detector: Optional[AuxiliaryTools] = None

    def load_encoder(self) -> bool:
        """ResNet50 인코더를 로드합니다."""
        try:
            w = ResNet50_Weights.IMAGENET1K_V2
            m = models.resnet50(weights=w)
            m.fc = nn.Identity()
            m.eval().to(self.emb_device)

            tf = transforms.Compose([
                transforms.Resize((self.emb_img_size, self.emb_img_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=EMBEDDING_CONFIG.NORMALIZE_MEAN,
                    std=EMBEDDING_CONFIG.NORMALIZE_STD
                ),
            ])

            self.encoder = m
            self.emb_tfm = tf
            scanner_logger.info("[scanner] ResNet50 encoder 로드 성공")
            return True
        except Exception as e:
            scanner_logger.warning(f"[scanner] ResNet50 encoder 로드 실패: {e}")
            self.encoder = None
            self.emb_tfm = None
            return False

    def load_yolo(self) -> bool:
        """YOLO 모델을 로드합니다."""
        try:
            yolo_local = self._resolve_yolo_seg_local_path()
            if yolo_local:
                from ultralytics import YOLO
                self.yolo = YOLO(yolo_local)
                scanner_logger.info(f"[scanner] YOLO 모델 로드 완료: {yolo_local}")
                return True
            return False
        except Exception as e:
            scanner_logger.error(f"[scanner] YOLO 모델 로드 실패: {e}")
            self.yolo = None
            return False

    def load_prototype_index(self) -> bool:
        """프로토타입 인덱스를 로드합니다."""
        try:
            scanner_logger.info("[scanner] prototype_index 로드 시작...")
            npy_uri, meta_uri, psid = self._resolve_active_prototype_index_uris()
            scanner_logger.info(f"[scanner] prototype URIs - npy: {npy_uri}, meta: {meta_uri}, psid: {psid}")

            if npy_uri and meta_uri:
                cache_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "prototype_index")
                ensure_dir(cache_dir)

                npy_local = self._fetch_uri_to_local(npy_uri, cache_dir)
                meta_local = self._fetch_uri_to_local(meta_uri, cache_dir)

                self.prototype_index = load_index(npy_local, meta_local)
                self.prototype_set_id = psid
                scanner_logger.info(
                    f"[scanner] prototype_index 로드 성공: psid={psid}, "
                    f"vectors={self.prototype_index.vectors.shape if self.prototype_index else 'None'}"
                )
                return True
            else:
                scanner_logger.warning("[scanner] prototype_index 로드 실패: npy_uri 또는 meta_uri가 없음")
                self.prototype_index = None
                self.prototype_set_id = None
                return False
        except Exception as e:
            scanner_logger.error(f"[scanner] prototype_index 로드 실패: {e}")
            self.prototype_index = None
            self.prototype_set_id = None
            return False

    def load_cctv_detectors(self) -> None:
        """CCTV 감지 모델들을 로드합니다."""
        try:
            self.violence_classifier = ViolenceClassification()
            scanner_logger.info("[scanner] ViolenceClassification 로드 성공")
        except Exception as e:
            logging.warning(f"ViolenceClassification 로드 실패: {e}")
            self.violence_classifier = None

        try:
            self.fall_detector = FallDownDetection()
            scanner_logger.info("[scanner] FallDownDetection 로드 성공")
        except Exception as e:
            logging.warning(f"FallDownDetection 로드 실패: {e}")
            self.fall_detector = None

        try:
            self.auxiliary_detector = AuxiliaryTools()
            scanner_logger.info("[scanner] AuxiliaryTools 로드 성공")
        except Exception as e:
            logging.warning(f"AuxiliaryTools 로드 실패: {e}")
            self.auxiliary_detector = None

    def _resolve_yolo_local_path(self) -> Optional[str]:
        """YOLO 모델 경로 결정: 로컬 우선, 없으면 GCS에서 다운로드"""
        yolo_path = (
            os.getenv("YOLO_MODEL_PATH", "").strip()
            or str(getattr(settings, "YOLO_MODEL_PATH", "") or "").strip()
        )
        if yolo_path and os.path.exists(yolo_path):
            return yolo_path

        yolo_uri = (
            os.getenv("YOLO_MODEL_URI", "").strip()
            or str(getattr(settings, "YOLO_MODEL_GCS_URI", "") or "").strip()
        )
        if not yolo_uri:
            return None

        cache_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "models")
        ensure_dir(cache_dir)

        parsed = urlparse(yolo_uri)
        filename = os.path.basename(parsed.path) or "yolo.pt"
        local_path = os.path.join(cache_dir, filename)

        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            scanner_logger.info(f"[scanner] YOLO 모델 캐시 사용: {local_path}")
            return local_path

        scanner_logger.info(f"[scanner] YOLO 모델 다운로드: {yolo_uri}")
        download_to(yolo_uri, local_path)
        return local_path

    def _resolve_yolo_seg_local_path(self) -> Optional[str]:
        """YOLO segmentation 모델 경로 결정."""
        yolo_uri = (
            os.getenv("YOLO_SEG_MODEL_URI", "").strip()
            or str(getattr(settings, "YOLO_SEG_MODEL_URI", "") or "").strip()
        )
        if not yolo_uri:
            return None

        cache_dir = os.path.join(getattr(settings, "CACHE_DIR", "/tmp"), "models")
        ensure_dir(cache_dir)

        parsed = urlparse(yolo_uri)
        filename = os.path.basename(parsed.path) or "yolo.pt"
        local_path = os.path.join(cache_dir, filename)

        force = os.getenv("YOLO_MODEL_FORCE_DOWNLOAD", "0").strip() == "1"
        if (not force) and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return local_path

        download_to(yolo_uri, local_path)
        return local_path

    def _resolve_active_prototype_index_uris(self) -> Tuple[str, str, Optional[int]]:
        """활성 프로토타입 인덱스 URI를 조회합니다."""
        try:
            cc = CentralClient()
            fn = getattr(cc, "get_active_prototype_set", None)
            if callable(fn):
                data = fn(timeout_s=API_TIMEOUT_CONFIG.PROTOTYPE_FETCH_TIMEOUT_SECONDS)
                npy_uri = str(data.get("index_npy_gcs_uri") or "").strip()
                meta_uri = str(data.get("index_meta_gcs_uri") or "").strip()
                psid = data.get("prototype_set_id")
                psid = int(psid) if psid is not None and str(psid).isdigit() else None
                if npy_uri and meta_uri:
                    return npy_uri, meta_uri, psid
        except Exception as e:
            scanner_logger.debug(f"[scanner] Central API prototype fetch에 실패했습니다: {e}")

        npy_uri = str(getattr(settings, "PROTOTYPE_INDEX_URI", "") or "").strip()
        meta_uri = str(getattr(settings, "PROTOTYPE_INDEX_META_URI", "") or "").strip()
        return npy_uri, meta_uri, None

    def _fetch_uri_to_local(self, uri: str, cache_dir: str) -> str:
        """URI에서 파일을 로컬로 다운로드합니다."""
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
