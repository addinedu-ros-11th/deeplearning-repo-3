import cv2
import logging
import os
import time  # 쿨타임 계산을 위해 추가
from collections import deque
from datetime import datetime

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
    - 5프레임 연속 감지 및 3분 쿨타임 적용 버전
    """

    def __init__(self, fps=30, output_dir='./auxiliary_clips'):
        self.logger = logging.getLogger(__name__)
        self.logger.info("GCS에서 Auxiliary 모델 로딩 중...")

        pt_path = load_latest_model(GCS_BUCKET, GCS_AUXILIARY_PREFIX, ".pt")
        self.model = YOLO(pt_path)

        self.logger.info("Auxiliary 모델 로딩 완료")

        self.feature_name = "auxiliary"
        self.fps = fps
        self.output_dir = output_dir

        # --- 로직 제어 변수 ---
        self.conf_threshold = 0.8           # 신뢰도 임계값
        self.detection_counter = 0          # 연속 감지 카운터
        self.min_detection_threshold = 3     # 최소 연속 프레임 수
        self.last_alert_time = 0            # 마지막 알람 시각 (timestamp)
        self.alert_cooldown = 180           # 쿨타임 (3분 = 180초)
        # ---------------------

        # 이벤트 클립용 프레임 버퍼 (전후 5초)
        self.frame_buffer = deque(maxlen=fps * 10)
        self.last_clip_path = None

    # =====================================================
    # 공개 함수
    # =====================================================
    def process_frame(self, frame):
        """
        프레임 처리 및 객체 검출 여부 판정 (연속 감지 및 쿨타임 로직)
        """
        result = {
            "detected": False,
            "num_objects": 0,
            "clip_path": None
        }

        try:
            self.frame_buffer.append(frame)
            current_time = time.time()

            # 1. YOLO 예측 (임계값 0.8 적용)
            results = self.model.predict(
                frame,
                conf=self.conf_threshold,
                verbose=False
            )

            boxes = results[0].boxes
            is_detected_now = boxes is not None and len(boxes) > 0

            # 2. 연속 감지 카운팅
            if is_detected_now:
                self.detection_counter += 1
            else:
                self.detection_counter = 0

            # 3. 최종 감지 판정 (5프레임 연속 + 쿨타임 경과)
            if self.detection_counter >= self.min_detection_threshold:
                elapsed_time = current_time - self.last_alert_time
                
                if elapsed_time > self.alert_cooldown:
                    # 최종 감지 확정 및 알람 발생
                    self.logger.warning(f"Auxiliary 객체(휠체어 등) 최종 확정 감지! (연속 {self.detection_counter}프레임)")
                    
                    result["detected"] = True
                    result["num_objects"] = len(boxes)
                    
                    # 마지막 알람 시간 업데이트
                    self.last_alert_time = current_time
                    
                    # (선택 사항) 알람 발생 시점에 클립 저장을 원하시면 아래 주석 해제
                    # result["clip_path"] = self._save_clip()
                else:
                    # 감지는 되었으나 쿨타임 중일 때 (필요시 로그 출력)
                    pass

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
            cv2.VideoWriter_fourcc(*"mp4v"),
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
    # 파일 기반 테스트용
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

            # 쿨타임 로직이 적용된 최종 감지 결과
            if result["detected"]:
                detected = True
                # 첫 번째 감지 시점에 클립 저장 시도
                if save_clip and clip_path is None:
                    clip_path = self._save_clip()
                
                self.logger.info(f"비디오 내 감지 확인 시점: {frame_count} frame")
                # 테스트 용도라면 여기서 break를 하지 않고 전체 영상을 돌려 쿨타임 작동 여부를 볼 수도 있습니다.
                # break 

        cap.release()

        return {
            "detected": detected,
            "clip_path": clip_path
        }