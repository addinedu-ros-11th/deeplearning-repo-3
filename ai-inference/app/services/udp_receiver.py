from __future__ import annotations

import io
import logging
import socket
import struct
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.constants import CCTV_CONFIG

logger = logging.getLogger("udp_receiver")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

HEADER_SIZE = 52  # 16 + 16 + 4 + 8 + 2 + 2 + 4 = 52 bytes


@dataclass
class FrameChunk:
    """프레임 청크 정보."""
    frame_index: int
    timestamp_ms: int
    total_chunks: int
    chunk_index: int
    data: bytes


@dataclass
class PendingFrame:
    """청크 조립 대기 중인 프레임."""
    frame_index: int
    timestamp_ms: int
    total_chunks: int
    chunks: Dict[int, bytes] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def is_complete(self) -> bool:
        return len(self.chunks) == self.total_chunks

    def assemble(self) -> bytes:
        """청크들을 조립하여 완전한 프레임 데이터를 반환합니다."""
        data = b""
        for i in range(self.total_chunks):
            data += self.chunks.get(i, b"")
        return data


@dataclass
class DeviceBuffer:
    """디바이스별 프레임 버퍼."""
    store_code: str
    device_code: str
    frames: deque = field(default_factory=lambda: deque(maxlen=150))  # 15fps * 10초
    pending_frames: Dict[int, PendingFrame] = field(default_factory=dict)
    last_frame_index: int = -1
    last_activity: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_chunk(self, chunk: FrameChunk) -> Optional[np.ndarray]:
        with self._lock:
            self.last_activity = time.time()

            # 단일 청크 프레임 (분할 없음)
            if chunk.total_chunks == 1:
                return self._decode_frame(chunk.data, chunk.frame_index)

            # 멀티 청크 프레임
            frame_key = chunk.frame_index

            if frame_key not in self.pending_frames:
                self.pending_frames[frame_key] = PendingFrame(
                    frame_index=chunk.frame_index,
                    timestamp_ms=chunk.timestamp_ms,
                    total_chunks=chunk.total_chunks,
                )

            pending = self.pending_frames[frame_key]
            pending.chunks[chunk.chunk_index] = chunk.data

            if pending.is_complete():
                frame_data = pending.assemble()
                del self.pending_frames[frame_key]
                self._cleanup_old_pending()
                return self._decode_frame(frame_data, chunk.frame_index)

            return None

    def _decode_frame(self, jpeg_data: bytes, frame_index: int) -> Optional[np.ndarray]:
        try:
            img = Image.open(io.BytesIO(jpeg_data)).convert("RGB")
            frame_rgb = np.array(img)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            self.frames.append((frame_index, frame_bgr))
            self.last_frame_index = frame_index

            return frame_bgr
        except Exception as e:
            logger.warning(f"프레임 디코딩 실패 [{self.store_code}/{self.device_code}]: {e}")
            return None

    def _cleanup_old_pending(self, max_age: float = 2.0) -> None:
        now = time.time()
        old_keys = [
            k for k, v in self.pending_frames.items()
            if now - v.created_at > max_age
        ]
        for k in old_keys:
            del self.pending_frames[k]

    def get_recent_frames(self, count: int = 30) -> list[np.ndarray]:
        with self._lock:
            frames = list(self.frames)[-count:]
            return [f[1] for f in frames]

    def get_frames_for_inference(self) -> Tuple[list[np.ndarray], int]:
        with self._lock:
            frames = list(self.frames)
            return [f[1] for f in frames], len(frames)


def _decode_header(data: bytes) -> Tuple[str, str, int, int, int, int, int]:
    if len(data) < HEADER_SIZE:
        raise ValueError(f"Invalid header size: {len(data)} < {HEADER_SIZE}")

    store_code = data[0:16].rstrip(b"\x00").decode("utf-8")
    device_code = data[16:32].rstrip(b"\x00").decode("utf-8")
    frame_index = struct.unpack(">I", data[32:36])[0]
    timestamp_ms = struct.unpack(">Q", data[36:44])[0]
    total_chunks = struct.unpack(">H", data[44:46])[0]
    chunk_index = struct.unpack(">H", data[46:48])[0]
    data_length = struct.unpack(">I", data[48:52])[0]

    return (store_code, device_code, frame_index, timestamp_ms,
            total_chunks, chunk_index, data_length)


class UDPFrameReceiver:

    def __init__(
        self,
        bind_host: str = "0.0.0.0",
        bind_port: int = 5005,
        buffer_size: int = 65535,
    ):
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.buffer_size = buffer_size

        self._socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._device_buffers: Dict[str, DeviceBuffer] = {}
        self._buffers_lock = threading.Lock()

        self._on_frame_callback: Optional[Callable[[str, str, np.ndarray], None]] = None

    def set_on_frame_callback(
        self,
        callback: Callable[[str, str, np.ndarray], None]
    ) -> None:
        """새 프레임 수신 시 호출될 콜백을 설정합니다"""
        self._on_frame_callback = callback

    def start(self) -> threading.Thread:
        if self._running:
            logger.warning("UDP 수신기가 이미 실행 중입니다.")
            return self._thread

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.bind_host, self.bind_port))
        self._socket.settimeout(1.0)

        self._running = True
        self._thread = threading.Thread(
            target=self._receive_loop,
            daemon=True,
            name="udp-receiver",
        )
        self._thread.start()

        logger.info(f"UDP 수신기 시작: {self.bind_host}:{self.bind_port}")
        return self._thread

    def stop(self) -> None:
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        if self._socket:
            self._socket.close()
            self._socket = None

        logger.info("UDP 수신기 종료")

    def _receive_loop(self) -> None:
        """UDP 패킷 수신 루프"""
        while self._running:
            try:
                data, addr = self._socket.recvfrom(self.buffer_size)
                self._process_packet(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"UDP 수신 오류: {e}")

    def _process_packet(self, data: bytes, addr: Tuple[str, int]) -> None:
        """수신된 UDP 패킷을 처리"""
        try:
            if len(data) < HEADER_SIZE:
                logger.warning(f"패킷 크기 부족: {len(data)} bytes from {addr}")
                return

            (store_code, device_code, frame_index, timestamp_ms,
             total_chunks, chunk_index, data_length) = _decode_header(data)

            chunk_data = data[HEADER_SIZE:HEADER_SIZE + data_length]

            chunk = FrameChunk(
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                total_chunks=total_chunks,
                chunk_index=chunk_index,
                data=chunk_data,
            )

            device_key = f"{store_code}:{device_code}"
            buffer = self._get_or_create_buffer(store_code, device_code, device_key)

            frame = buffer.add_chunk(chunk)

            if frame is not None and self._on_frame_callback:
                try:
                    self._on_frame_callback(store_code, device_code, frame)
                except Exception as e:
                    logger.error(f"프레임 콜백 오류 [{device_key}]: {e}")

        except Exception as e:
            logger.warning(f"패킷 처리 오류 from {addr}: {e}")

    def _get_or_create_buffer(
        self,
        store_code: str,
        device_code: str,
        device_key: str
    ) -> DeviceBuffer:
        with self._buffers_lock:
            if device_key not in self._device_buffers:
                self._device_buffers[device_key] = DeviceBuffer(
                    store_code=store_code,
                    device_code=device_code,
                )
                logger.info(f"새 디바이스 버퍼 생성: {device_key}")

            return self._device_buffers[device_key]

    def get_buffer(self, store_code: str, device_code: str) -> Optional[DeviceBuffer]:
        device_key = f"{store_code}:{device_code}"
        with self._buffers_lock:
            return self._device_buffers.get(device_key)

    def list_active_devices(self) -> list[dict]:
        with self._buffers_lock:
            result = []
            for key, buf in self._device_buffers.items():
                result.append({
                    "device_key": key,
                    "store_code": buf.store_code,
                    "device_code": buf.device_code,
                    "frame_count": len(buf.frames),
                    "last_frame_index": buf.last_frame_index,
                    "last_activity": buf.last_activity,
                })
            return result

    def cleanup_inactive_buffers(self, max_inactive_seconds: float = 60.0) -> int:
        now = time.time()
        with self._buffers_lock:
            inactive_keys = [
                k for k, v in self._device_buffers.items()
                if now - v.last_activity > max_inactive_seconds
            ]
            for k in inactive_keys:
                del self._device_buffers[k]
                logger.info(f"비활성 버퍼 정리: {k}")
            return len(inactive_keys)


class RealtimeCCTVProcessor:
    """
    UDP로 수신된 프레임을 주기적으로 모아서 추론을 수행
    """

    def __init__(
        self,
        cctv_engine,
        udp_receiver: UDPFrameReceiver,
        inference_interval: float = 2.0,
        min_frames_for_inference: int = 15,
    ):
        self.cctv_engine = cctv_engine
        self.udp_receiver = udp_receiver
        self.inference_interval = inference_interval
        self.min_frames_for_inference = min_frames_for_inference

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_inference_time: Dict[str, float] = {}

    def start(self) -> threading.Thread:
        if self._running:
            logger.warning("실시간 CCTV 처리기가 이미 실행 중")
            return self._thread

        self._running = True
        self._thread = threading.Thread(
            target=self._inference_loop,
            daemon=True,
            name="cctv-realtime-processor",
        )
        self._thread.start()

        logger.info("실시간 CCTV 처리기 시작")
        return self._thread

    def stop(self) -> None:
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        logger.info("실시간 CCTV 처리기 종료")

    def _inference_loop(self) -> None:
        while self._running:
            try:
                self._process_all_devices()
            except Exception as e:
                logger.error(f"추론 루프 오류: {e}")

            time.sleep(0.5)  # 0.5초마다 체크

    def _process_all_devices(self) -> None:
        active_devices = self.udp_receiver.list_active_devices()
        now = time.time()

        for device_info in active_devices:
            device_key = device_info["device_key"]
            store_code = device_info["store_code"]
            device_code = device_info["device_code"]
            frame_count = device_info.get("frame_count", 0)

            last_time = self._last_inference_time.get(device_key, 0)
            if now - last_time < self.inference_interval:
                continue

            buffer = self.udp_receiver.get_buffer(store_code, device_code)
            if not buffer:
                continue

            frames, count = buffer.get_frames_for_inference()
            if count < self.min_frames_for_inference:
                logger.info(f"[{device_key}] 프레임 부족: {count} < {self.min_frames_for_inference}")
                continue

            self._last_inference_time[device_key] = now
            logger.info(f"[{device_key}] 추론 시작: frames={count}")
            self._run_inference(store_code, device_code, frames)

    def _run_inference(
        self,
        store_code: str,
        device_code: str,
        frames: list[np.ndarray],
    ) -> None:
        try:
            if not self.cctv_engine:
                logger.warning("CCTV 엔진이 초기화되지 않음")
                return

            payload = {
                "store_code": store_code,
                "device_code": device_code,
                "frames_numpy": frames,
            }

            logger.info(
                f"실시간 추론 시작: {store_code}/{device_code}, "
                f"frames={len(frames)}"
            )

            result = self.cctv_engine.infer_realtime(payload)

            events = result.get("events", [])
            logger.info(
                f"실시간 추론 완료: {store_code}/{device_code}, "
                f"events={len(events)}개"
            )
            if events:
                logger.info(
                    f"이벤트 감지: {store_code}/{device_code}, "
                    f"events={[e.get('event_type') for e in events]}"
                )

        except Exception as e:
            logger.error(f"추론 실패 [{store_code}/{device_code}]: {e}")


_udp_receiver: Optional[UDPFrameReceiver] = None
_realtime_processor: Optional[RealtimeCCTVProcessor] = None
_init_lock = threading.Lock()


def get_udp_receiver() -> UDPFrameReceiver:
    """UDPFrameReceiver 싱글톤 인스턴스를 반환"""
    global _udp_receiver

    if _udp_receiver is None:
        with _init_lock:
            if _udp_receiver is None:
                _udp_receiver = UDPFrameReceiver(
                    bind_host="0.0.0.0",
                    bind_port=settings.UDP_RECEIVER_PORT,
                    buffer_size=settings.UDP_BUFFER_SIZE,
                )

    return _udp_receiver


def init_realtime_processor(cctv_engine) -> RealtimeCCTVProcessor:
    """RealtimeCCTVProcessor를 초기화하고 반환"""
    global _realtime_processor

    with _init_lock:
        receiver = get_udp_receiver()
        _realtime_processor = RealtimeCCTVProcessor(
            cctv_engine=cctv_engine,
            udp_receiver=receiver,
        )

    return _realtime_processor
