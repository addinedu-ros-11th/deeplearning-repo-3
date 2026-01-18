from __future__ import annotations

import base64
import io
import logging
import os
import subprocess
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.constants import CCTV_CONFIG, VIDEO_ENCODING_CONFIG
from app.services.central_client import CentralClient
from app.services.video_processor import ensure_dir
from app.util.gcs_utils import upload_to_gcs

cctv_logger = logging.getLogger("cctv")
if not cctv_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(message)s', datefmt='%H:%M:%S'))
    cctv_logger.addHandler(handler)
    cctv_logger.setLevel(logging.INFO)

_encoding_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ffmpeg-")
_upload_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="gcs-upload-")


class CCTVInferenceEngine:
    """CCTV 추론을 담당하는 엔진 클래스."""

    def __init__(
        self,
        violence_classifier=None,
        fall_detector=None,
        auxiliary_detector=None,
        mock: bool = False,
    ):
        self.violence_classifier = violence_classifier
        self.fall_detector = fall_detector
        self.auxiliary_detector = auxiliary_detector
        self.mock = mock

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        """CCTV 폭력/낙상 감지 추론을 수행합니다."""
        now = datetime.now(timezone.utc)

        if self.mock:
            return self._create_mock_result(now)

        store_code = payload.get("store_code", "")
        device_code = payload.get("device_code", "")
        clip_local_path = payload.get("clip_local_path")
        frames_b64 = payload.get("frames_b64")
        gcs_bucket = os.getenv("GCS_BUCKET_CCTV")

        if clip_local_path:
            return self._infer_streaming(
                clip_local_path, store_code, device_code, gcs_bucket, now
            )

        if frames_b64:
            frames = self._decode_b64_frames(frames_b64)
            fps = 15
            if frames:
                height, width = frames[0].shape[:2]
            else:
                height, width = 0, 0
        else:
            frames, fps, width, height = [], 30, 0, 0

        if not frames:
            return {"events": []}

        return self._infer_batch(
            frames, fps, width, height, store_code, device_code, gcs_bucket, now
        )

    def infer_realtime(self, payload: dict[str, Any]) -> dict[str, Any]:
        """실시간 CCTV 추론을 수행"""
        now = datetime.now(timezone.utc)

        if self.mock:
            return self._create_mock_result(now)

        store_code = payload.get("store_code", "")
        device_code = payload.get("device_code", "")
        frames = payload.get("frames_numpy", [])
        gcs_bucket = os.getenv("GCS_BUCKET_CCTV")

        if not frames:
            return {"events": []}

        fps = 15  # UDP 스트리밍 기본 FPS
        if frames:
            height, width = frames[0].shape[:2]
        else:
            height, width = 0, 0

        cctv_logger.debug(
            f"실시간 추론: {store_code}/{device_code}, "
            f"frames={len(frames)}, size={width}x{height}"
        )

        return self._infer_batch(
            frames, fps, width, height, store_code, device_code, gcs_bucket, now
        )

    def _create_mock_result(self, now: datetime) -> dict[str, Any]:
        """MOCK 결과를 생성합니다."""
        return {
            "events": [
                {
                    "event_type": "VIOLENCE",
                    "confidence": 0.88,
                    "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                    "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                    "meta_json": {"mode": "mock"},
                },
                {
                    "event_type": "FALL",
                    "confidence": 0.92,
                    "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                    "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                    "meta_json": {"mode": "mock"},
                },
                {
                    "event_type": "AUXILIARY",
                    "confidence": 0.90,
                    "started_at": (now - timedelta(seconds=2)).replace(tzinfo=None).isoformat(sep=" "),
                    "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                    "meta_json": {"mode": "mock"},
                }
            ]
        }

    def _infer_streaming(
        self,
        video_path: str,
        store_code: str,
        device_code: str,
        gcs_bucket: str,
        now: datetime,
    ) -> dict[str, Any]:
        """스트리밍 방식 CCTV 추론을 수행합니다."""
        fps, width, height, total_frames = self._get_video_info(video_path)
        if total_frames == 0:
            return {"events": []}

        buffer_size = fps * CCTV_CONFIG.ROLLING_BUFFER_SECONDS
        clip_buffer = deque(maxlen=buffer_size)

        events = []
        detection_state = {
            "violence": {"detected": False, "frame_idx": None, "confidence": 0.0},
            "fall": {"detected": False, "frame_idx": None, "confidence": 0.0},
            "auxiliary": {"detected": False, "frame_idx": None, "confidence": 0.0},
        }

        if self.violence_classifier:
            self.violence_classifier._reset()

        frame_interval = CCTV_CONFIG.VIOLENCE_FRAME_INTERVAL
        probabilities = []
        global_frame_idx = 0

        for chunk, start_idx, chunk_fps, chunk_width, chunk_height in self._iter_video_chunks(video_path, chunk_size=100):
            for local_idx, frame in enumerate(chunk):
                frame_idx = start_idx + local_idx
                global_frame_idx = frame_idx

                clip_buffer.append((frame_idx, frame.copy()))

                # Violence 감지
                if self.violence_classifier and not detection_state["violence"]["detected"]:
                    if frame_idx % frame_interval == 0:
                        result = self.violence_classifier.process_frame(frame)
                        if result.get("ready"):
                            prob = result.get("probability", 0.0)
                            probabilities.append(prob)
                            if prob >= self.violence_classifier.threshold:
                                detection_state["violence"]["detected"] = True
                                detection_state["violence"]["frame_idx"] = frame_idx
                                detection_state["violence"]["confidence"] = prob

                # Fall 감지
                if self.fall_detector and not detection_state["fall"]["detected"]:
                    result = self.fall_detector.process_frame(frame)
                    if result.get("is_fall"):
                        detection_state["fall"]["detected"] = True
                        detection_state["fall"]["frame_idx"] = frame_idx
                        detection_state["fall"]["confidence"] = result.get("confidence", 0.0)

                # Auxiliary 감지
                if self.auxiliary_detector and not detection_state["auxiliary"]["detected"]:
                    result = self.auxiliary_detector.process_frame(frame)
                    if result.get("detected"):
                        detection_state["auxiliary"]["detected"] = True
                        detection_state["auxiliary"]["frame_idx"] = frame_idx
                        detection_state["auxiliary"]["confidence"] = result.get("confidence", 0.0)

        # 감지된 이벤트 처리
        for event_type, state in [
            ("VIOLENCE", detection_state["violence"]),
            ("FALL", detection_state["fall"]),
            ("WHEELCHAIR", detection_state["auxiliary"]),
        ]:
            if not state["detected"]:
                continue

            clip_frames = self._extract_clip_frames_from_buffer(
                clip_buffer, state["frame_idx"], fps, clip_seconds=5
            )

            if clip_frames:
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                event_name = "fall_down" if event_type == "FALL" else event_type.lower()
                local_clip_dir = os.path.join(settings.CACHE_DIR, f"{event_name}_clips")
                ensure_dir(local_clip_dir)
                local_clip_path = os.path.join(local_clip_dir, f"cctv_{event_name}_{timestamp}.mp4")

                self._encode_clip_background(clip_frames, fps, width, height, local_clip_path)

                event_data = {
                    "event_type": event_type,
                    "confidence": state["confidence"],
                    "started_at": now.replace(tzinfo=None).isoformat(sep=" "),
                    "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
                    "meta_json": {
                        "mode": "streaming",
                        "clip_path": local_clip_path,
                        "clip_pending": True,
                    },
                }
                events.append(event_data)

                if gcs_bucket and store_code and device_code:
                    blob_name = f"cctv_{event_name}_{timestamp}.mp4"
                    self._upload_clip_background(local_clip_path, gcs_bucket, blob_name)

        return {"events": events}

    def _extract_clip_frames_from_buffer(
        self,
        clip_buffer: deque,
        detection_frame_idx: int,
        fps: int,
        clip_seconds: int = 5,
    ) -> list:
        """롤링 버퍼에서 감지 시점 전후 프레임을 추출합니다."""
        if not clip_buffer:
            return []

        start_target = detection_frame_idx - (clip_seconds * fps)
        end_target = detection_frame_idx + (clip_seconds * fps)

        clip_frames = []
        for frame_idx, frame in clip_buffer:
            if start_target <= frame_idx <= end_target:
                clip_frames.append(frame)

        return clip_frames

    def _infer_batch(
        self,
        frames: list,
        fps: int,
        width: int,
        height: int,
        store_code: str,
        device_code: str,
        gcs_bucket: str,
        now: datetime,
    ) -> dict[str, Any]:
        """배치 방식 CCTV 추론을 수행합니다."""
        events = []
        tasks = []
        cctv_logger.info(f"[MODELS] violence={self.violence_classifier is not None}, fall={self.fall_detector is not None}, auxiliary={self.auxiliary_detector is not None}")

        if self.violence_classifier:
            tasks.append(("VIOLENCE", self._run_violence_inference))

        if self.fall_detector:
            tasks.append(("FALL", self._run_fall_inference))

        if self.auxiliary_detector:
            tasks.append(("WHEELCHAIR", self._run_auxiliary_inference))

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_type = {
                executor.submit(func, frames, fps, width, height, now): event_type
                for event_type, func in tasks
            }

            for future in as_completed(future_to_type):
                event_type = future_to_type[future]
                try:
                    result = future.result()

                    if event_type == "VIOLENCE":
                        detected = result.get("is_violence", False)
                        cctv_logger.info(f"[RESULT] VIOLENCE: is_violence={detected}, confidence={result.get('confidence', 0):.3f}")
                    elif event_type == "FALL":
                        detected = result.get("is_fall", False)
                        cctv_logger.info(f"[RESULT] FALL: is_fall={detected}, confidence={result.get('confidence', 0):.3f}")
                    elif event_type == "WHEELCHAIR":
                        detected = result.get("detected", False)
                        cctv_logger.info(f"[RESULT] WHEELCHAIR: detected={detected}, confidence={result.get('confidence', 0):.3f}")
                    else:
                        detected = False

                    if detected:
                        cctv_logger.info(f"[DETECTED] {event_type} 감지됨! -> _process_event 호출")
                        event = self._process_event(
                            event_type=event_type,
                            inference_result=result,
                            now=now,
                            store_code=store_code,
                            device_code=device_code,
                            gcs_bucket=gcs_bucket,
                        )
                        if event:
                            events.append(event)
                except Exception as e:
                    cctv_logger.error(f"{event_type} 추론 실패: {e}")

        return {"events": events}

    def _process_event(
        self,
        event_type: str,
        inference_result: dict[str, Any],
        now: datetime,
        store_code: str,
        device_code: str,
        gcs_bucket: str,
    ) -> dict[str, Any] | None:
        """CCTV 이벤트를 처리합니다."""
        local_clip_path = inference_result.get("local_clip_path")
        confidence = inference_result.get("confidence", 0.0)
        extra_meta = inference_result.get("extra_meta", {})

        gcs_uri = None

        if not gcs_bucket:
            cctv_logger.warning(f"[GCS] GCS_BUCKET_CCTV 환경변수 미설정, 클립 업로드 스킵")

        if local_clip_path and os.path.exists(local_clip_path):
            cctv_logger.info(f"[GCS] 클립 업로드 시도: {local_clip_path} -> {gcs_bucket}")
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            event_name = "fall_down" if event_type == "FALL" else event_type.lower()
            blob_name = f"cctv_{event_name}_{timestamp}.mp4"
            try:
                gcs_uri = upload_to_gcs(local_clip_path, gcs_bucket, blob_name)
                cctv_logger.info(f"[GCS] 업로드 성공: {gcs_uri}")
            except Exception as e:
                cctv_logger.error(f"[GCS] 업로드 실패 ({event_type}): {e}")
        else:
            cctv_logger.warning(f"[GCS] 클립 파일 없음: {local_clip_path}")

        event_data = {
            "event_type": event_type,
            "confidence": confidence,
            "started_at": now.replace(tzinfo=None).isoformat(sep=" "),
            "ended_at": now.replace(tzinfo=None).isoformat(sep=" "),
            "meta_json": {
                "mode": "real",
                "clip_path": local_clip_path,
                "gcs_uri": gcs_uri,
                **extra_meta,
            },
        }

        cctv_logger.info(f"[EVENT] type={event_type}, clip={local_clip_path}, gcs_uri={gcs_uri}, bucket={gcs_bucket}")

        if gcs_uri and store_code and device_code:
            self._try_ingest_event(
                store_code=store_code,
                device_code=device_code,
                event_data=event_data,
                gcs_uri=gcs_uri,
            )
        else:
            cctv_logger.warning(f"[EVENT] DB 저장 스킵: gcs_uri={gcs_uri}, store={store_code}, device={device_code}")

        return event_data

    def _run_violence_inference(
        self,
        frames: list[np.ndarray],
        fps: int,
        width: int,
        height: int,
        now: datetime,
    ) -> dict[str, Any]:
        """폭력 감지 추론을 수행합니다."""
        self.violence_classifier._reset()

        probabilities = []
        violence_detected = False
        violence_frame = None
        frame_interval = CCTV_CONFIG.VIOLENCE_FRAME_INTERVAL

        for i, frame in enumerate(frames):
            if i % frame_interval != 0:
                continue

            result = self.violence_classifier.process_frame(frame)
            if result.get("ready"):
                prob = result.get("probability", 0.0)
                probabilities.append(prob)
                if prob >= self.violence_classifier.threshold and not violence_detected:
                    violence_detected = True
                    violence_frame = i

        if probabilities:
            max_prob = max(probabilities)
            avg_prob = sum(probabilities) / len(probabilities)
            cctv_logger.info(f"[VIOLENCE] 추론 완료: frames={len(frames)}, max_prob={max_prob:.3f}, avg_prob={avg_prob:.3f}, threshold={self.violence_classifier.threshold}, detected={violence_detected}")
        else:
            cctv_logger.info(f"[VIOLENCE] 추론 완료: frames={len(frames)}, probabilities 없음")

        if not probabilities:
            return {"is_violence": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

        if violence_detected:
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            local_clip_dir = os.path.join(settings.CACHE_DIR, "violence_clips")
            ensure_dir(local_clip_dir)
            local_clip_path = os.path.join(local_clip_dir, f"cctv_violence_{timestamp}.mp4")

            clip_seconds = CCTV_CONFIG.CLIP_DURATION_SECONDS
            start_frame = max(0, violence_frame - clip_seconds * fps)
            end_frame = min(len(frames), violence_frame + clip_seconds * fps)

            self._encode_clip_sync(frames[start_frame:end_frame], fps, width, height, local_clip_path)

            violence_count = sum(1 for p in probabilities if p >= self.violence_classifier.threshold)
            return {
                "is_violence": True,
                "confidence": float(max(probabilities)),
                "local_clip_path": local_clip_path,
                "extra_meta": {
                    "source": "shared_frames",
                    "avg_probability": float(np.mean(probabilities)),
                    "violence_ratio": float(violence_count / len(probabilities)),
                },
            }

        return {"is_violence": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

    def _run_fall_inference(
        self,
        frames: list[np.ndarray],
        fps: int,
        width: int,
        height: int,
        now: datetime,
    ) -> dict[str, Any]:
        """낙상 감지 추론을 수행합니다."""
        fall_detected = False
        fall_frame = None
        fall_confidence = 0.0
        skip_frames = 0

        for i, frame in enumerate(frames):
            if skip_frames > 0:
                skip_frames -= 1
                continue

            result = self.fall_detector.process_frame(frame)

            if result.get("is_fall") and not fall_detected:
                fall_detected = True
                fall_frame = i
                fall_confidence = result.get("confidence", 0.0)
                skip_frames = fps * CCTV_CONFIG.SKIP_AFTER_DETECTION_SECONDS

        cctv_logger.info(f"[FALL] 추론 완료: frames={len(frames)}, detected={fall_detected}, confidence={fall_confidence:.3f}")

        if not fall_detected:
            return {"is_fall": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        local_clip_dir = os.path.join(settings.CACHE_DIR, "fall_clips")
        ensure_dir(local_clip_dir)
        local_clip_path = os.path.join(local_clip_dir, f"cctv_fall_down_{timestamp}.mp4")

        clip_seconds = CCTV_CONFIG.CLIP_DURATION_SECONDS
        start_frame = max(0, fall_frame - clip_seconds * fps)
        end_frame = min(len(frames), fall_frame + clip_seconds * fps)

        self._encode_clip_sync(frames[start_frame:end_frame], fps, width, height, local_clip_path)

        return {
            "is_fall": True,
            "confidence": fall_confidence,
            "local_clip_path": local_clip_path,
            "extra_meta": {"source": "shared_frames"},
        }

    def _run_auxiliary_inference(
        self,
        frames: list[np.ndarray],
        fps: int,
        width: int,
        height: int,
        now: datetime,
    ) -> dict[str, Any]:
        """Auxiliary 감지 추론을 수행합니다."""
        detected = False
        detected_frame = None
        skip_frames = 0
        detection_count = 0

        for i, frame in enumerate(frames):
            if skip_frames > 0:
                skip_frames -= 1
                continue

            result = self.auxiliary_detector.process_frame(frame)

            if result.get("num_objects", 0) > 0:
                detection_count += 1
                cctv_logger.info(
                    f"[AUXILIARY] 프레임 {i}: 객체 감지됨 (num_objects={result.get('num_objects')})"
                )

            if result.get("detected") and not detected:
                detected = True
                detected_frame = i
                skip_frames = fps * CCTV_CONFIG.SKIP_AFTER_DETECTION_SECONDS
                cctv_logger.info(f"[AUXILIARY] 최종 감지 확정! frame={i}")

        cctv_logger.info(f"[AUXILIARY] 추론 완료: frames={len(frames)}, 객체감지횟수={detection_count}, 최종감지={detected}")

        if not detected:
            return {"detected": False, "confidence": 0.0, "local_clip_path": None, "extra_meta": {}}

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        local_clip_dir = os.path.join(settings.CACHE_DIR, "auxiliary_clips")
        ensure_dir(local_clip_dir)
        local_clip_path = os.path.join(local_clip_dir, f"cctv_auxiliary_{timestamp}.mp4")

        clip_seconds = CCTV_CONFIG.CLIP_DURATION_SECONDS
        start_frame = max(0, detected_frame - clip_seconds * fps)
        end_frame = min(len(frames), detected_frame + clip_seconds * fps)

        cctv_logger.info(f"[AUXILIARY] 클립 저장 시작: {local_clip_path}, frames={end_frame - start_frame}")
        self._encode_clip_sync(frames[start_frame:end_frame], fps, width, height, local_clip_path)
        cctv_logger.info(f"[AUXILIARY] 클립 저장 완료: {local_clip_path}")

        return {
            "detected": True,
            "confidence": 1.0,
            "local_clip_path": local_clip_path,
            "extra_meta": {"source": "shared_frames"},
        }

    def _get_video_info(self, path: str) -> tuple[int, int, int, int]:
        """비디오 메타데이터를 조회합니다."""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return CCTV_CONFIG.DEFAULT_FPS, 0, 0, 0

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or CCTV_CONFIG.DEFAULT_FPS
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        return fps, width, height, total_frames

    def _iter_video_chunks(self, path: str, chunk_size: int = 100):
        """비디오를 청크 단위로 스트리밍합니다."""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or CCTV_CONFIG.DEFAULT_FPS
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        chunk = []
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                if chunk:
                    yield chunk, frame_idx - len(chunk), fps, width, height
                break
            chunk.append(frame)
            frame_idx += 1
            if len(chunk) >= chunk_size:
                yield chunk, frame_idx - len(chunk), fps, width, height
                chunk = []
        cap.release()

    def _encode_clip_sync(
        self,
        frames: list,
        fps: int,
        width: int,
        height: int,
        output_path: str
    ) -> str:
        """동기 방식 클립 인코딩을 수행합니다."""
        temp_path = output_path.replace('.mp4', '_temp.mp4')
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_ENCODING_CONFIG.CODEC)
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        for f in frames:
            out.write(f)
        out.release()

        result = subprocess.run([
            'ffmpeg', '-y', '-i', temp_path,
            '-c:v', 'libx264',
            '-preset', VIDEO_ENCODING_CONFIG.H264_PRESET,
            '-crf', str(VIDEO_ENCODING_CONFIG.H264_CRF),
            output_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"ffmpeg 변환 실패: {result.stderr}")
            if os.path.exists(temp_path):
                os.rename(temp_path, output_path)
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return output_path

    def _encode_clip_background(
        self,
        frames: list,
        fps: int,
        width: int,
        height: int,
        output_path: str
    ):
        """비동기 방식 클립 인코딩을 수행합니다."""
        frames_copy = [f.copy() for f in frames]

        def _encode():
            try:
                return self._encode_clip_sync(frames_copy, fps, width, height, output_path)
            except Exception as e:
                logging.error(f"Background encoding failed: {e}")
                return None

        return _encoding_executor.submit(_encode)

    def _upload_clip_background(self, local_path: str, bucket: str, blob_name: str):
        """비동기 방식 GCS 업로드를 수행합니다."""
        def _upload():
            try:
                for _ in range(60):
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        break
                    import time
                    time.sleep(1)

                if not os.path.exists(local_path):
                    logging.warning(f"GCS upload skipped - file not found: {local_path}")
                    return None

                return upload_to_gcs(local_path, bucket, blob_name)
            except Exception as e:
                logging.warning(f"GCS upload failed: {e}")
                return None

        return _upload_executor.submit(_upload)

    def _decode_b64_frames(self, frames_b64: list[str]) -> list[np.ndarray]:
        """Base64 프레임들을 디코딩합니다."""
        decoded_frames = []
        for frame_b64 in frames_b64:
            frame_bytes, frame_rgb = self._decode_frame({"frame_b64": frame_b64})
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            decoded_frames.append(frame_bgr)
        return decoded_frames

    def _decode_frame(self, payload: dict[str, Any]) -> tuple[bytes, np.ndarray]:
        """프레임을 디코딩합니다."""
        frame_b64 = payload.get("frame_b64")
        if not frame_b64:
            raise ValueError("frame_b64 required")

        s = str(frame_b64).strip()
        if s.startswith("data:") and "," in s:
            s = s.split(",", 1)[1]

        raw = base64.b64decode(s)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return raw, np.array(img)

    def _try_ingest_event(
        self,
        store_code: str,
        device_code: str,
        event_data: dict[str, Any],
        gcs_uri: str,
    ) -> None:
        """CCTV 이벤트를 Central API에 저장합니다."""
        cctv_logger.info(f"[DB저장] 시도: store={store_code}, device={device_code}, type={event_data.get('event_type')}, gcs_uri={gcs_uri}")
        try:
            cc = CentralClient()
            result = cc.ingest_cctv_event(
                store_code=store_code,
                device_code=device_code,
                event_type=event_data.get("event_type", "VIOLENCE"),
                confidence=event_data.get("confidence", 0.0),
                started_at=event_data.get("started_at"),
                ended_at=event_data.get("ended_at"),
                clip_gcs_uri=gcs_uri,
                clip_start_at=event_data.get("started_at"),
                clip_end_at=event_data.get("ended_at"),
                meta_json=event_data.get("meta_json"),
                timeout_s=3.0,
            )
            cctv_logger.info(f"[DB저장] 성공: event_id={result.get('event_id')}")
        except Exception as e:
            cctv_logger.error(f"[DB저장] 실패: {e}")
