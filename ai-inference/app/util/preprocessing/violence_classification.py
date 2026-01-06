import cv2
import numpy as np
from collections import deque
import logging

from app.util.gcs_utils import load_latest_model

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# GCS 설정
GCS_BUCKET = 'gcs-bucket-models'
GCS_PREFIX = 'cctv_'

class ViolenceClassification:

    def __init__(self, buffer_size=10, threshold=0.4, vote_threshold=4):
        logging.info("GCS에서 최신 모델 로딩 중...")
        self.classifier = load_latest_model(GCS_BUCKET, GCS_PREFIX, 'violence_classifier')
        self.scaler = load_latest_model(GCS_BUCKET, GCS_PREFIX, 'violence_scaler')
        logging.info("모델 로딩 완료")

        self.buffer_size = buffer_size
        self.threshold = threshold
        self.vote_threshold = vote_threshold

        self.flow_history = deque(maxlen=buffer_size)
        self.diff_history = deque(maxlen=buffer_size)
        self.violence_history = deque(maxlen=10)

        self.prev_gray = None
        self.frame_size = (320, 240)

    def _reset(self):
        """버퍼 초기화"""
        self.flow_history.clear()
        self.diff_history.clear()
        self.violence_history.clear()
        self.prev_gray = None

    def _extract_features(self):
        """옵티컬 플로우 히스토리에서 특징 추출"""
        if len(self.flow_history) < 5:
            return None

        features = {}

        # 모든 프레임의 magnitude와 angle
        all_mags = np.concatenate([f[0].flatten() for f in self.flow_history])
        all_angles = np.concatenate([f[1].flatten() for f in self.flow_history])

        # 1. 옵티컬 플로우 크기 통계
        features['flow_mag_mean'] = np.mean(all_mags)
        features['flow_mag_std'] = np.std(all_mags)
        features['flow_mag_max'] = np.max(all_mags)
        features['flow_mag_median'] = np.median(all_mags)
        features['flow_mag_q75'] = np.percentile(all_mags, 75)
        features['flow_mag_q90'] = np.percentile(all_mags, 90)
        features['flow_mag_q95'] = np.percentile(all_mags, 95)

        # 2. 프레임별 움직임 통계
        frame_mean_mags = [np.mean(f[0]) for f in self.flow_history]
        features['frame_mag_mean'] = np.mean(frame_mean_mags)
        features['frame_mag_std'] = np.std(frame_mean_mags)
        features['frame_mag_max'] = np.max(frame_mean_mags)
        features['frame_mag_range'] = np.max(frame_mean_mags) - np.min(frame_mean_mags)

        # 3. 움직임 변화율
        if len(frame_mean_mags) > 1:
            mag_diff = np.diff(frame_mean_mags)
            features['mag_acc_mean'] = np.mean(np.abs(mag_diff))
            features['mag_acc_std'] = np.std(mag_diff)
            features['mag_acc_max'] = np.max(np.abs(mag_diff))
        else:
            features['mag_acc_mean'] = 0
            features['mag_acc_std'] = 0
            features['mag_acc_max'] = 0

        # 4. 높은 움직임 비율
        features['high_motion_ratio'] = np.mean(all_mags > 5.0)
        features['very_high_motion_ratio'] = np.mean(all_mags > 10.0)

        # 5. 프레임 차이 통계
        if self.diff_history:
            all_diffs = np.concatenate([d.flatten() for d in self.diff_history])
            features['diff_mean'] = np.mean(all_diffs)
            features['diff_std'] = np.std(all_diffs)
            features['diff_max'] = np.max(all_diffs)
        else:
            features['diff_mean'] = 0
            features['diff_std'] = 0
            features['diff_max'] = 0

        # 6. 영역별 움직임
        h, w = self.flow_history[0][0].shape
        regions = [
            (0, h//2, 0, w//2),
            (0, h//2, w//2, w),
            (h//2, h, 0, w//2),
            (h//2, h, w//2, w)
        ]
        region_names = ['top_left', 'top_right', 'bottom_left', 'bottom_right']

        for (y1, y2, x1, x2), name in zip(regions, region_names):
            region_mags = np.concatenate([f[0][y1:y2, x1:x2].flatten() for f in self.flow_history])
            features[f'{name}_mag_mean'] = np.mean(region_mags)
            features[f'{name}_mag_std'] = np.std(region_mags)

        # 7. 방향 히스토그램
        angle_hist, _ = np.histogram(all_angles, bins=8, range=(0, 2*np.pi))
        angle_hist = angle_hist / (np.sum(angle_hist) + 1e-6)
        for i, h in enumerate(angle_hist):
            features[f'angle_hist_{i}'] = h

        # 8. 움직임 엔트로피
        mag_hist, _ = np.histogram(all_mags, bins=20, range=(0, 20))
        mag_hist = mag_hist / (np.sum(mag_hist) + 1e-6)
        entropy = -np.sum(mag_hist * np.log(mag_hist + 1e-10))
        features['motion_entropy'] = entropy

        # 9. 움직임 피크
        if len(frame_mean_mags) >= 3:
            peaks = 0
            for i in range(1, len(frame_mean_mags) - 1):
                if frame_mean_mags[i] > frame_mean_mags[i-1] and frame_mean_mags[i] > frame_mean_mags[i+1]:
                    peaks += 1
            features['motion_peaks'] = peaks
            features['motion_peaks_ratio'] = peaks / len(frame_mean_mags)
        else:
            features['motion_peaks'] = 0
            features['motion_peaks_ratio'] = 0

        return features

    def process_frame(self, frame):
        """프레임 처리 및 폭력 여부 판정"""

        # 프레임 전처리
        frame_small = cv2.resize(frame, self.frame_size)
        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

        result = {
            'is_violence': False,
            'probability': 0.0,
            'votes': 0,
            'total_votes': len(self.violence_history),
            'ready': False
        }

        # 첫 프레임이면 저장만
        if self.prev_gray is None:
            self.prev_gray = gray.copy()
            return result

        # 옵티컬 플로우 계산
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )

        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        self.flow_history.append((mag, ang))

        # 프레임 차이
        diff = cv2.absdiff(gray, self.prev_gray)
        self.diff_history.append(diff)

        self.prev_gray = gray.copy()

        # 예측
        if len(self.flow_history) >= 5:
            result['ready'] = True
            features = self._extract_features()

            if features is not None:
                X = np.array(list(features.values())).reshape(1, -1)
                X_scaled = self.scaler.transform(X)
                prob = self.classifier.predict_proba(X_scaled)[0][1]

                self.violence_history.append(prob)
                result['probability'] = prob
                result['total_votes'] = len(self.violence_history)

                # Hard voting
                votes = sum(1 for p in self.violence_history if p >= self.threshold)
                result['votes'] = votes
                result['is_violence'] = votes >= self.vote_threshold

        return result

    def predict_video(self, video_path, frame_interval=3, save_clip=True, output_dir='./'):
        """비디오 파일 전체 분석"""
        from datetime import datetime
        import os

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        # 비디오 정보
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._reset()
        probabilities = []
        frames_buffer = []  # 클립 저장용 프레임 버퍼
        frame_count = 0
        violence_detected = False
        violence_frame = None  # 폭력 감지된 프레임 번호
        clip_seconds = 5  # 감지 시점 전후 초

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frames_buffer.append(frame.copy())
            frame_count += 1

            if frame_count % frame_interval != 0:
                continue

            result = self.process_frame(frame)
            if result['ready']:
                prob = result['probability']
                probabilities.append(prob)
                # 한 번이라도 threshold 넘으면 폭력 판정
                if prob >= self.threshold and not violence_detected:
                    violence_detected = True
                    violence_frame = frame_count
                    logging.warning(f"폭력 감지! 확률: {prob:.1%} (frame: {frame_count})")

        cap.release()

        if not probabilities:
            return None

        violence_count = sum(1 for p in probabilities if p >= self.threshold)

        result = {
            'is_violence': violence_detected,
            'max_probability': max(probabilities),
            'avg_probability': np.mean(probabilities),
            'violence_ratio': violence_count / len(probabilities),
            'clip_path': None
        }

        # 폭력 감지 시 클립 저장 (감지 시점 +-5초, 총 10초)
        if violence_detected and save_clip and frames_buffer and violence_frame:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clip_filename = f"cctv_violence_{timestamp}.mp4"
            clip_path = os.path.join(output_dir, clip_filename)

            # 감지 시점 기준 +-5초 범위 계산
            start_frame = max(0, violence_frame - clip_seconds * fps)
            end_frame = min(len(frames_buffer), violence_frame + clip_seconds * fps)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(clip_path, fourcc, fps, (width, height))

            for f in frames_buffer[start_frame:end_frame]:
                out.write(f)
            out.release()

            clip_duration = (end_frame - start_frame) / fps
            result['clip_path'] = clip_path
            logging.info(f"폭력 클립 저장 완료: {clip_path} ({clip_duration:.1f}초)")
            
        return result


if __name__ == '__main__':
    # 사용 예시
    model = ViolenceClassification()

    # 비디오 파일 분석
    result = model.predict_video(
        './data/fight_0095.mp4',
        save_clip=True,
        output_dir='./violence_clips'
    )
