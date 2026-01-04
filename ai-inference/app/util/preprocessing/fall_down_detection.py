import cv2
import logging
import os
from collections import deque
from datetime import datetime

from ultralytics import YOLO
from app.util.gcs_utils import load_latest_model


# =========================
# GCS 설정
# =========================
GCS_BUCKET = "gcs-bucket-models"
GCS_FALL_DOWN_PREFIX = "cctv_fall_down_"


class FallDownDetection:
    """
    YOLOv8 Pose 기반 낙상 감지 전처리 클래스
    """

    def __init__(self, fps=30, output_dir='./fall_clips'):
        """
        fps: 입력 영상 FPS
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("GCS에서 낙상 모델 로딩 중...")

        pt_path = load_latest_model(GCS_BUCKET, GCS_FALL_DOWN_PREFIX, ".pt")
        self.model = YOLO(pt_path)

        self.logger.info("낙상 모델 로딩 완료")

        self.feature_name = "fall_down"
        self.fps = fps
        self.output_dir = output_dir

        self.frame_buffer = deque(maxlen=fps * 10)  # 전후 5초
        self.fall_counter = {}
        self.last_clip_path = None

        self.FALL_FRAME_THRESHOLD = 2
        self.ASPECT_RATIO_TH = 1.0

    def process_frame(self, frame):
        """
        프레임 처리 및 낙상 여부 판정
        """
        result = {
            "is_fall": False,
            "clip_path": None
        }

        try:
            self.frame_buffer.append(frame)

            results = self.model.predict(
                frame,
                imgsz=640,
                conf=0.5,
                verbose=False
            )

            is_fall = self._detect_fall(results)

            if is_fall:
                self.logger.info("낙상 감지됨")

            result["is_fall"] = is_fall
            return result

        except Exception as e:
            self.logger.error(f"ERROR: {str(e)}")
            raise

    def _detect_fall(self, results):
        """
        Skeleton rule 기반 낙상 판단
        """
        for result in results:
            if result.boxes is None or result.keypoints is None:
                continue

            for i in range(len(result.boxes)):
                x1, y1, x2, y2 = map(int, result.boxes.xyxy[i])
                kpts = result.keypoints.xy[i]

                head_y = kpts[0][1]
                hip_y = (kpts[11][1] + kpts[12][1]) / 2

                bbox_h = y2 - y1
                bbox_w = x2 - x1
                aspect_ratio = bbox_h / (bbox_w + 1e-6)

                pid = i
                rule_fall = head_y > hip_y and aspect_ratio < self.ASPECT_RATIO_TH

                if rule_fall:
                    self.fall_counter[pid] = self.fall_counter.get(pid, 0) + 1
                else:
                    self.fall_counter[pid] = 0

                if self.fall_counter[pid] >= self.FALL_FRAME_THRESHOLD:
                    return True

        return False

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

        for frame in self.frame_buffer:
            out.write(frame)

        out.release()
        self.last_clip_path = clip_path
        self.logger.info(f"Clip saved: {clip_path}")
        return clip_path

    def predict_video(self, video_path, save_clip=True):
        """
        비디오 파일 전체 분석
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error("비디오 파일을 열 수 없습니다.")
            return None

        is_fall_detected = False
        frame_count = 0
        clip_path = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            result = self.process_frame(frame)

            if result["is_fall"]:
                is_fall_detected = True
                clip_path = result.get("clip_path")
                self.logger.warning(
                    f"낙상 발생! (frame: {frame_count})"
                )
                break

        cap.release()

        return {
            "is_fall": is_fall_detected,
            "clip_path": clip_path
        }


# =========================
# 사용 예시 (violence와 동일)
# =========================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    model = FallDownDetection(fps=30)

    result = model.predict_video(
        "./data/fall_test.mp4"
    )

    print(result)
