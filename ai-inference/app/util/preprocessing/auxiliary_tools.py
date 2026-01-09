# ai-inference/preprocessing/auxiliary_tools.py

import cv2
import logging
import os
from collections import deque
from datetime import datetime
import subprocess
from ultralytics import YOLO
from app.util.gcs_utils import load_latest_model


# =========================
# GCS 설정
# =========================
GCS_BUCKET = "gcs-bucket-models"
GCS_AUXILIARY_PREFIX = "cctv_auxiliary_"


class AuxiliaryTools:
    """
    YOLO 기반 Auxiliary Detection (Wheelchair 등)
    """

    def __init__(self, fps=30, output_dir='./auxiliary_clips'):
        """
        fps: 입력 영상 FPS
        output_dir: 클립 저장 디렉토리
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("GCS에서 Auxiliary 모델 로딩 중...")

        pt_path = load_latest_model(GCS_BUCKET, GCS_AUXILIARY_PREFIX, ".pt")
        self.model = YOLO(pt_path)

        self.logger.info("Auxiliary 모델 로딩 완료")

        self.feature_name = "auxiliary"
        self.fps = fps
        self.output_dir = output_dir

        # 이벤트 클립용 프레임 버퍼 (전후 5초)
        self.frame_buffer = deque(maxlen=fps * 10)
        self.last_clip_path = None

    # =====================================================
    # 공개 함수
    # =====================================================
    def process_frame(self, frame):
        """
        프레임 처리 및 객체 검출 여부 판정
        """
        result = {
            "detected": False,
            "confidence": 0.0,
            "num_objects": 0,
            "clip_path": None
        }

        try:
            self.frame_buffer.append(frame)

            results = self.model.predict(
                frame,
                conf=0.4,
                verbose=False
            )

            boxes = results[0].boxes
            detected = boxes is not None and len(boxes) > 0

            if detected:
                max_conf = float(boxes.conf.max()) if len(boxes.conf) > 0 else 0.0
                self.logger.info(f"Auxiliary 객체 감지 ({len(boxes)}개, conf={max_conf:.2f})")
                result["confidence"] = max_conf

            result["detected"] = detected
            result["num_objects"] = len(boxes) if detected else 0
            return result

        except Exception as e:
            self.logger.error(f"ERROR: {str(e)}")
            raise

    # =====================================================
    # 헬퍼 함수 (내부 전용)
    # =====================================================
    def _save_clip(self):
        """
        이벤트 발생 전후 5초 영상 클립 저장
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

        for f in self.frame_buffer:
            out.write(f)

        out.release()
        self.last_clip_path = clip_path
        self.logger.info(f"Clip saved: {clip_path}")
        return clip_path

    # =====================================================
    # 파일 기반 테스트용 (Fall / Violence와 동일)
    # =====================================================
    def predict_video(self, video_path, save_clip=True):
        """
        비디오 파일 전체 분석
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error("비디오 파일을 열 수 없습니다.")
            return None

        detected = False
        frame_count = 0
        clip_path = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            result = self.process_frame(frame)

            if result["detected"]:
                detected = True
                clip_path = result.get("clip_path")
                self.logger.warning(
                    f"Auxiliary 객체 감지! (frame: {frame_count})"
                )
                break

        cap.release()

        return {
            "detected": detected,
            "clip_path": clip_path
        }
