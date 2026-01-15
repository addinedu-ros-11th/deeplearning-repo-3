from __future__ import annotations

import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

from app.core.config import settings
from app.services.inference.loader import ModelLoader
from app.services.inference.tray import TrayInferenceEngine
from app.services.inference.cctv import CCTVInferenceEngine

from YOLOwrapper import FallDownDetection as FallDownDetectionWrapper, YOLOWrapper

# 로거 설정
scanner_logger = logging.getLogger("scanner")
cctv_logger = logging.getLogger("cctv")

sys.modules['__main__'].FallDownDetection = FallDownDetectionWrapper
sys.modules['__main__'].YOLOWrapper = YOLOWrapper

load_dotenv()


class InferenceEngine:
    """
    추론 엔진 파사드 클래스.

    ModelLoader, TrayInferenceEngine, CCTVInferenceEngine을 통합하여
    단일 인터페이스를 제공합니다.
    """

    def __init__(self) -> None:
        self.mock = bool(getattr(settings, "AI_MOCK_MODE", False))
        self.use_job_queue = os.getenv("AI_USE_JOB_QUEUE", "1").strip() == "1"

        # 디바이스 설정
        self.ai_device = os.getenv("AI_DEVICE", "cpu").strip() or "cpu"
        self.emb_device = os.getenv("EMB_DEVICE", self.ai_device).strip() or "cpu"

        # 모델 로더 초기화
        self._model_loader = ModelLoader(
            ai_device=self.ai_device,
            emb_device=self.emb_device,
        )

        # 초기 인코더 로드
        self._model_loader.load_encoder()

        # 서브 엔진들 (startup_load 후 초기화)
        self._tray_engine: TrayInferenceEngine | None = None
        self._cctv_engine: CCTVInferenceEngine | None = None

        # 하위 호환성을 위한 속성 노출
        self.prototype_index = None
        self.prototype_set_id = None
        self.yolo = None
        self.encoder = self._model_loader.encoder
        self.emb_tfm = self._model_loader.emb_tfm
        self.violence_classifier = None
        self.fall_detector = None
        self.auxiliary_detector = None

    def startup_load(self) -> None:
        """모델들을 로드하고 서브 엔진들을 초기화합니다."""
        if self.mock:
            scanner_logger.info("[scanner] MOCK 모드 - 모델 로드 스킵")
            self._init_engines()
            return

        # 프로토타입 인덱스 로드
        self._model_loader.load_prototype_index()
        self.prototype_index = self._model_loader.prototype_index
        self.prototype_set_id = self._model_loader.prototype_set_id

        # CCTV 감지 모델 로드
        self._model_loader.load_cctv_detectors()
        self.violence_classifier = self._model_loader.violence_classifier
        self.fall_detector = self._model_loader.fall_detector
        self.auxiliary_detector = self._model_loader.auxiliary_detector

        # YOLO 로드
        self._model_loader.load_yolo()
        self.yolo = self._model_loader.yolo

        # 서브 엔진 초기화
        self._init_engines()

    def _init_engines(self) -> None:
        """서브 엔진들을 초기화합니다."""
        self._tray_engine = TrayInferenceEngine(
            yolo=self._model_loader.yolo,
            encoder=self._model_loader.encoder,
            emb_tfm=self._model_loader.emb_tfm,
            prototype_index=self._model_loader.prototype_index,
            prototype_set_id=self._model_loader.prototype_set_id,
            mock=self.mock,
            use_job_queue=self.use_job_queue,
        )

        self._cctv_engine = CCTVInferenceEngine(
            violence_classifier=self._model_loader.violence_classifier,
            fall_detector=self._model_loader.fall_detector,
            auxiliary_detector=self._model_loader.auxiliary_detector,
            mock=self.mock,
        )

    def infer_tray(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        트레이 추론을 수행합니다.

        payload: 추론 요청 페이로드
            - session_uuid: str
            - attempt_no: int (1..3)
            - store_code: str
            - device_code: str
            - frame_b64: str (dataURL 포함 가능)
        """
        if self._tray_engine is None:
            self._init_engines()
        return self._tray_engine.infer(payload)

    def infer_cctv(self, payload: dict[str, Any]) -> dict[str, Any]:
        """CCTV 폭력/낙상 감지 추론"""
        if self._cctv_engine is None:
            self._init_engines()
        return self._cctv_engine.infer(payload)
