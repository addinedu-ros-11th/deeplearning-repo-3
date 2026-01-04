# fall_model_wrapper.py
from ultralytics import YOLO
import logging
import hashlib
import os
import tempfile
from datetime import datetime
from app.services.gcs_utils import load_latest_model

# GCS 설정
GCS_BUCKET_NAME = "gcs-bucket-models"
GCS_FALL_DOWN_PREFIX = "cctv_fall_down_"
GCS_AUXILIARY_PREFIX = "cctv_auxiliary_"

class FallDownDetection:
    def __init__(self):
        # GCS에서 최신 모델 다운로드
        self.pt_path = load_latest_model(GCS_BUCKET_NAME, GCS_FALL_DOWN_PREFIX, ".pt")
        self.model = None
        self.logger = logging.getLogger(__name__)

        # 메타데이터
        self.metadata = {
            "pt_path": self.pt_path,
            "pt_hash": self._calc_file_hash(self.pt_path),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_type": "YOLOv8s-pose",
            "task": "fall_down_detection"
        }

    def _calc_file_hash(self, file_path):
        """pt 파일 SHA256 해시 계산"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def load(self):
        """YOLO 모델 로딩"""
        if self.model is None:
            logging.info(f"YOLO model loading from {self.pt_path}")
            self.model = YOLO(self.pt_path)

    def process_frame(self, frame, **kwargs):
        """프레임 기반 낙상 추론"""
        try:
            self.load()
            return self.model.predict(frame, **kwargs)
        except Exception as e:
            self.logger.error(f"ERROR: {str(e)}")
            raise

    def predict(self, frame, **kwargs):
        """YOLO predict 호출 (process_frame과 동일)"""
        return self.process_frame(frame, **kwargs)


class YOLOWrapper:
    """
    Auxiliary 감지용 YOLO 모델 래퍼
    joblib으로 저장된 pkl 파일 역직렬화를 위해 필요
    """

    def __init__(self):
        # GCS에서 최신 모델 다운로드
        self.pt_path = load_latest_model(GCS_BUCKET_NAME, GCS_AUXILIARY_PREFIX, ".pt")
        self.model = None
        self.logger = logging.getLogger(__name__)

    def load(self):
        """YOLO 모델 로딩"""
        if self.model is None:
            logging.info(f"YOLO model loading from {self.pt_path}")
            self.model = YOLO(self.pt_path)

    def predict(self, frame, **kwargs):
        """YOLO predict 호출"""
        self.load()
        return self.model.predict(frame, **kwargs)
