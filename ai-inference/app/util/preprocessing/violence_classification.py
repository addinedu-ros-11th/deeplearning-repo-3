import cv2
import numpy as np
from collections import deque
import logging
import threading

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

        # Thread safety lock
        self._lock = threading.Lock()

    def _reset(self):
        """버퍼 초기화 (thread-safe)"""
        with self._lock:
            self.flow_history.clear()
            self.diff_history.clear()
            self.violence_history.clear()
            self.prev_gray = None

    def _extract_features(self):
        """옵티컬 플로우 히스토리에서 특징 추출 (최적화된 버전)"""
        if len(self.flow_history) < 5:
            return None

        features = {}
        n_frames = len(self.flow_history)

        # 프레임별 통계를 먼저 계산 (메모리 효율적)
        frame_mag_means = np.empty(n_frames, dtype=np.float32)
        frame_mag_maxs = np.empty(n_frames, dtype=np.float32)
        frame_mag_stds = np.empty(n_frames, dtype=np.float32)

        # 전체 통계를 위한 누적 변수
        total_sum = 0.0
        total_sq_sum = 0.0
        total_count = 0
        global_max = -np.inf
        high_motion_count = 0
        very_high_motion_count = 0

        # 히스토그램용 버퍼 (pre-allocated)
        angle_hist = np.zeros(8, dtype=np.float64)
        mag_hist = np.zeros(20, dtype=np.float64)

        h, w = self.flow_history[0][0].shape

        # 영역별 통계용 버퍼
        region_sums = {name: 0.0 for name in ['top_left', 'top_right', 'bottom_left', 'bottom_right']}
        region_sq_sums = {name: 0.0 for name in ['top_left', 'top_right', 'bottom_left', 'bottom_right']}
        region_counts = {name: 0 for name in ['top_left', 'top_right', 'bottom_left', 'bottom_right']}

        regions = {
            'top_left': (0, h//2, 0, w//2),
            'top_right': (0, h//2, w//2, w),
            'bottom_left': (h//2, h, 0, w//2),
            'bottom_right': (h//2, h, w//2, w)
        }

        # 프레임별로 처리 (한 번에 하나씩 - 메모리 효율적)
        for idx, (mag, ang) in enumerate(self.flow_history):
            # 프레임별 통계
            frame_mag_means[idx] = np.mean(mag)
            frame_mag_maxs[idx] = np.max(mag)
            frame_mag_stds[idx] = np.std(mag)

            # 전체 통계 누적
            flat_mag = mag.ravel()
            total_sum += np.sum(flat_mag)
            total_sq_sum += np.sum(flat_mag ** 2)
            total_count += flat_mag.size
            frame_max = np.max(flat_mag)
            if frame_max > global_max:
                global_max = frame_max

            # 고움직임 비율
            high_motion_count += np.sum(flat_mag > 5.0)
            very_high_motion_count += np.sum(flat_mag > 10.0)

            # 히스토그램 누적
            ang_bins = np.clip((ang.ravel() / (2 * np.pi) * 8).astype(int), 0, 7)
            np.add.at(angle_hist, ang_bins, 1)

            mag_bins = np.clip((flat_mag / 20 * 20).astype(int), 0, 19)
            np.add.at(mag_hist, mag_bins, 1)

            # 영역별 통계 누적
            for name, (y1, y2, x1, x2) in regions.items():
                region_mag = mag[y1:y2, x1:x2].ravel()
                region_sums[name] += np.sum(region_mag)
                region_sq_sums[name] += np.sum(region_mag ** 2)
                region_counts[name] += region_mag.size

        # 1. 옵티컬 플로우 크기 통계
        global_mean = total_sum / total_count
        global_var = (total_sq_sum / total_count) - (global_mean ** 2)
        global_std = np.sqrt(max(0, global_var))

        features['flow_mag_mean'] = float(global_mean)
        features['flow_mag_std'] = float(global_std)
        features['flow_mag_max'] = float(global_max)

        # 근사 백분위수 (정확한 계산 대신 프레임별 통계 사용)
        sorted_means = np.sort(frame_mag_means)
        features['flow_mag_median'] = float(np.median(frame_mag_means))
        features['flow_mag_q75'] = float(np.percentile(frame_mag_means, 75))
        features['flow_mag_q90'] = float(np.percentile(frame_mag_means, 90))
        features['flow_mag_q95'] = float(np.percentile(frame_mag_means, 95))

        # 2. 프레임별 움직임 통계
        features['frame_mag_mean'] = float(np.mean(frame_mag_means))
        features['frame_mag_std'] = float(np.std(frame_mag_means))
        features['frame_mag_max'] = float(np.max(frame_mag_means))
        features['frame_mag_range'] = float(np.max(frame_mag_means) - np.min(frame_mag_means))

        # 3. 움직임 변화율
        if n_frames > 1:
            mag_diff = np.diff(frame_mag_means)
            features['mag_acc_mean'] = float(np.mean(np.abs(mag_diff)))
            features['mag_acc_std'] = float(np.std(mag_diff))
            features['mag_acc_max'] = float(np.max(np.abs(mag_diff)))
        else:
            features['mag_acc_mean'] = 0.0
            features['mag_acc_std'] = 0.0
            features['mag_acc_max'] = 0.0

        # 4. 높은 움직임 비율
        features['high_motion_ratio'] = float(high_motion_count / total_count)
        features['very_high_motion_ratio'] = float(very_high_motion_count / total_count)

        # 5. 프레임 차이 통계
        if self.diff_history:
            diff_sum = 0.0
            diff_sq_sum = 0.0
            diff_count = 0
            diff_max = 0.0
            for d in self.diff_history:
                flat_d = d.ravel().astype(np.float32)
                diff_sum += np.sum(flat_d)
                diff_sq_sum += np.sum(flat_d ** 2)
                diff_count += flat_d.size
                d_max = np.max(flat_d)
                if d_max > diff_max:
                    diff_max = d_max

            diff_mean = diff_sum / diff_count
            diff_var = (diff_sq_sum / diff_count) - (diff_mean ** 2)
            features['diff_mean'] = float(diff_mean)
            features['diff_std'] = float(np.sqrt(max(0, diff_var)))
            features['diff_max'] = float(diff_max)
        else:
            features['diff_mean'] = 0.0
            features['diff_std'] = 0.0
            features['diff_max'] = 0.0

        # 6. 영역별 움직임
        for name in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
            r_mean = region_sums[name] / region_counts[name]
            r_var = (region_sq_sums[name] / region_counts[name]) - (r_mean ** 2)
            features[f'{name}_mag_mean'] = float(r_mean)
            features[f'{name}_mag_std'] = float(np.sqrt(max(0, r_var)))

        # 7. 방향 히스토그램
        angle_hist = angle_hist / (np.sum(angle_hist) + 1e-6)
        for i, val in enumerate(angle_hist):
            features[f'angle_hist_{i}'] = float(val)

        # 8. 움직임 엔트로피
        mag_hist = mag_hist / (np.sum(mag_hist) + 1e-6)
        entropy = -np.sum(mag_hist * np.log(mag_hist + 1e-10))
        features['motion_entropy'] = float(entropy)

        # 9. 움직임 피크
        if n_frames >= 3:
            peaks = 0
            for i in range(1, n_frames - 1):
                if frame_mag_means[i] > frame_mag_means[i-1] and frame_mag_means[i] > frame_mag_means[i+1]:
                    peaks += 1
            features['motion_peaks'] = peaks
            features['motion_peaks_ratio'] = float(peaks / n_frames)
        else:
            features['motion_peaks'] = 0
            features['motion_peaks_ratio'] = 0.0

        return features

    def process_frame(self, frame):
        """프레임 처리 및 폭력 여부 판정"""

        # 프레임 전처리
        frame_small = cv2.resize(frame, self.frame_size)
        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

        with self._lock:
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

            fourcc = cv2.VideoWriter_fourcc(*'avc1')
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
