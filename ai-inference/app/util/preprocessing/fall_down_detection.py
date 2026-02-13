import cv2
import logging
import os
import pickle
from collections import deque
from datetime import datetime

from app.util.gcs_utils import load_latest_model

# =========================
# GCS 설정
# =========================
GCS_BUCKET = "gcs-bucket-models"
GCS_FALL_DOWN_PREFIX = "cctv_fall_down_"


class FallDownDetection:
    """
    YOLO + LSTM + Rule + Soft-voting 기반 낙상 감지
    """

    def __init__(self, fps=30, output_dir="./fall_clips"):
        self.logger = logging.getLogger(__name__)
        self.logger.info("GCS에서 낙상 pipeline(pkl) 로딩 중...")

        pkl_path = load_latest_model(
            GCS_BUCKET,
            GCS_FALL_DOWN_PREFIX,
            ".pkl"
        )

        with open(pkl_path, "rb") as f:
            self.pipeline = pickle.load(f)

        self.logger.info("낙상 pipeline 로딩 완료")

        self.feature_name = "fall_down"
        self.fps = fps
        self.output_dir = output_dir

        self.frame_buffer = deque(maxlen=fps * 10)  # 전후 5초
        self.last_clip_path = None

    def process_frame(self, frame):
        """
        프레임 처리 및 낙상 여부 판정
        """
        result = {
            "is_fall": False,
            "clip_path": None,
        }

        try:
            self.frame_buffer.append(frame)

            inference = self.pipeline.process_frame(frame)

            if inference is None:
                return result

            if inference["label"] == "FALL":
                self.logger.warning(
                    f"낙상 감지됨 | prob={inference['final_prob']:.2f}"
                )

                clip_path = self._save_clip()
                result["is_fall"] = True
                result["clip_path"] = clip_path

            return result

        except Exception as e:
            self.logger.error(f"ERROR: {str(e)}")
            raise

    def _save_clip(self):
        """
        이벤트 발생 전후 영상 클립 저장
        """
        if not self.frame_buffer:
            return None

        os.makedirs(self.output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cctv_{self.feature_name}_{timestamp}.mp4"
        clip_path = os.path.join(self.output_dir, filename)

        h, w, _ = self.frame_buffer[0].shape
        out = cv2.VideoWriter(
            clip_path,
            cv2.VideoWriter_fourcc(*"avc1"),
            self.fps,
            (w, h)
        )

        for frame in self.frame_buffer:
            out.write(frame)

        out.release()
        self.last_clip_path = clip_path
        self.logger.info(f"Clip saved: {clip_path}")
        return clip_path
