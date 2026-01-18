from __future__ import annotations

import logging
import socket
import struct
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

import cv2

logger = logging.getLogger("stream_sender")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

HEADER_SIZE = 52
MAX_CHUNK_SIZE = 60000
JPEG_QUALITY = 80


@dataclass
class StreamSession:
    """RTSP 스트리밍 세션 정보."""
    session_id: str
    rtsp_uri: str
    store_code: str
    device_code: str
    target_host: str
    target_port: int
    fps: int = 15
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _running: bool = field(default=False, repr=False)
    _frame_index: int = field(default=0, repr=False)
    _socket: Optional[socket.socket] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "rtsp_uri": self.rtsp_uri,
            "store_code": self.store_code,
            "device_code": self.device_code,
            "target_host": self.target_host,
            "target_port": self.target_port,
            "fps": self.fps,
            "running": self._running,
            "frame_index": self._frame_index,
        }


def _encode_header(
    store_code: str,
    device_code: str,
    frame_index: int,
    timestamp_ms: int,
    total_chunks: int,
    chunk_index: int,
    data_length: int,
) -> bytes:
    store_bytes = store_code.encode("utf-8")[:16].ljust(16, b"\x00")
    device_bytes = device_code.encode("utf-8")[:16].ljust(16, b"\x00")

    header = (
        store_bytes
        + device_bytes
        + struct.pack(">I", frame_index)
        + struct.pack(">Q", timestamp_ms)
        + struct.pack(">H", total_chunks)
        + struct.pack(">H", chunk_index)
        + struct.pack(">I", data_length)
    )
    return header


def _send_frame_udp(
    sock: socket.socket,
    target_host: str,
    target_port: int,
    store_code: str,
    device_code: str,
    frame_index: int,
    jpeg_data: bytes,
) -> bool:
    timestamp_ms = int(time.time() * 1000)
    total_length = len(jpeg_data)

    total_chunks = (total_length + MAX_CHUNK_SIZE - 1) // MAX_CHUNK_SIZE
    if total_chunks == 0:
        total_chunks = 1

    try:
        for chunk_idx in range(total_chunks):
            start = chunk_idx * MAX_CHUNK_SIZE
            end = min(start + MAX_CHUNK_SIZE, total_length)
            chunk_data = jpeg_data[start:end]

            header = _encode_header(
                store_code=store_code,
                device_code=device_code,
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                total_chunks=total_chunks,
                chunk_index=chunk_idx,
                data_length=len(chunk_data),
            )

            packet = header + chunk_data
            sock.sendto(packet, (target_host, target_port))

        return True
    except Exception as e:
        logger.warning(f"UDP 전송 실패: {e}")
        return False


def _stream_worker(session: StreamSession) -> None:
    print(f"[{session.session_id}] 스트리밍 워커 시작")
    logger.info(
        f"[{session.session_id}] 스트리밍 시작: "
        f"{session.store_code}/{session.device_code} -> "
        f"{session.target_host}:{session.target_port}"
    )
    print(
        f"[{session.session_id}] 스트리밍 시작: "
        f"{session.store_code}/{session.device_code} -> "
        f"{session.target_host}:{session.target_port}"
    )

    is_local_file = not session.rtsp_uri.startswith("rtsp://")

    if is_local_file:
        import os
        if not os.path.exists(session.rtsp_uri):
            logger.error(f"[{session.session_id}] 파일 없음: {session.rtsp_uri}")
            print(f"[{session.session_id}] 파일 없음: {session.rtsp_uri}")
            session._running = False
            return
        logger.info(f"[{session.session_id}] 로컬 파일 모드: {session.rtsp_uri}")
        print(f"[{session.session_id}] 로컬 파일 모드: {session.rtsp_uri}")
        
    cap = cv2.VideoCapture(session.rtsp_uri)
    if not cap.isOpened():
        logger.error(f"[{session.session_id}] 연결 실패: {session.rtsp_uri}")
        print(f"[{session.session_id}] 연결 실패: {session.rtsp_uri}")
        session._running = False
        return
    session._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    frame_interval = 1.0 / session.fps
    last_frame_time = 0.0

    try:
        while session._running:
            current_time = time.time()

            # 1. FPS 제어
            if current_time - last_frame_time < frame_interval:
                if is_local_file:
                    time.sleep(0.001)
                else:
                    ret, _ = cap.read()
                    if not ret:
                        logger.warning(f"[{session.session_id}] 프레임 읽기 실패, 재연결 시도...")
                        cap.release()
                        time.sleep(1)
                        cap = cv2.VideoCapture(session.rtsp_uri)
                        if not cap.isOpened():
                            logger.error(f"[{session.session_id}] RTSP 재연결 실패")
                            break
                continue

            ret, frame = cap.read()
            if not ret:
                if is_local_file:
                    logger.info(f"[{session.session_id}] 파일 끝 도달, 스트리밍 종료 (총 {session._frame_index} 프레임)")
                    print(f"[{session.session_id}] 파일 끝 도달, 스트리밍 종료 (총 {session._frame_index} 프레임)")
                    break
                else:
                    logger.warning(f"[{session.session_id}] 프레임 읽기 실패, 재연결 시도...")
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(session.rtsp_uri)
                    if not cap.isOpened():
                        logger.error(f"[{session.session_id}] RTSP 재연결 실패")
                        break
                    continue

            # 2. JPEG 인코딩
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            success, jpeg_buffer = cv2.imencode(".jpg", frame, encode_param)
            if not success:
                logger.warning(f"[{session.session_id}] JPEG 인코딩 실패")
                continue

            jpeg_data = jpeg_buffer.tobytes()

            # 3. UDP 전송
            _send_frame_udp(
                sock=session._socket,
                target_host=session.target_host,
                target_port=session.target_port,
                store_code=session.store_code,
                device_code=session.device_code,
                frame_index=session._frame_index,
                jpeg_data=jpeg_data,
            )

            session._frame_index += 1
            last_frame_time = current_time

            if session._frame_index % (session.fps * 5) == 0:
                print(f"[{session.session_id}] 프레임 전송 중: frame_index={session._frame_index}")
                logger.info(f"[{session.session_id}] 프레임 전송 중: frame_index={session._frame_index}")

    except Exception as e:
        logger.error(f"[{session.session_id}] 스트리밍 오류: {e}")

    finally:
        cap.release()
        if session._socket:
            session._socket.close()
            session._socket = None
        session._running = False
        logger.info(f"[{session.session_id}] 스트리밍 종료")


class StreamManager:
    """여러 RTSP 스트리밍 세션을 관리하는 매니저 클래스"""

    def __init__(self, default_target_host: str, default_target_port: int, default_fps: int = 15):
        self._sessions: Dict[str, StreamSession] = {}
        self._lock = threading.Lock()
        self._default_target_host = default_target_host
        self._default_target_port = default_target_port
        self._default_fps = default_fps

    def start_stream(
        self,
        store_code: str,
        device_code: str,
        rtsp_uri: str,
        target_host: Optional[str] = None,
        target_port: Optional[int] = None,
        fps: Optional[int] = None,
    ) -> str:
        device_key = f"{store_code}:{device_code}"

        with self._lock:
            # 기존 세션 확인
            for sid, sess in self._sessions.items():
                if sess.store_code == store_code and sess.device_code == device_code:
                    if sess._running:
                        raise ValueError(f"이미 활성화된 스트리밍 세션이 존재합니다: {device_key}")
                    else:
                        del self._sessions[sid]
                        break

            session_id = str(uuid.uuid4())[:8]
            session = StreamSession(
                session_id=session_id,
                rtsp_uri=rtsp_uri,
                store_code=store_code,
                device_code=device_code,
                target_host=target_host or self._default_target_host,
                target_port=target_port or self._default_target_port,
                fps=fps or self._default_fps,
            )

            session._running = True
            session._thread = threading.Thread(
                target=_stream_worker,
                args=(session,),
                daemon=True,
                name=f"stream-{session_id}",
            )
            session._thread.start()

            self._sessions[session_id] = session
            logger.info(f"스트리밍 세션 시작: {session_id} ({device_key})")

            return session_id

    def stop_stream(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"세션을 찾을 수 없음: {session_id}")
                return False

            session._running = False

            if session._thread and session._thread.is_alive():
                session._thread.join(timeout=5.0)

            del self._sessions[session_id]
            logger.info(f"스트리밍 세션 중지: {session_id}")

            return True

    def stop_stream_by_device(self, store_code: str, device_code: str) -> bool:
        with self._lock:
            target_session_id = None
            for sid, sess in self._sessions.items():
                if sess.store_code == store_code and sess.device_code == device_code:
                    target_session_id = sid
                    break

            if not target_session_id:
                logger.warning(f"세션을 찾을 수 없음: {store_code}/{device_code}")
                return False

        return self.stop_stream(target_session_id)

    def list_streams(self) -> list[dict]:
        with self._lock:
            return [sess.to_dict() for sess in self._sessions.values()]

    def get_stream(self, session_id: str) -> Optional[dict]:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.to_dict() if session else None

    def stop_all(self) -> int:
        with self._lock:
            session_ids = list(self._sessions.keys())

        count = 0
        for sid in session_ids:
            if self.stop_stream(sid):
                count += 1

        return count


_stream_manager: Optional[StreamManager] = None
_manager_lock = threading.Lock()


def get_stream_manager() -> StreamManager:
    """StreamManager 싱글톤 인스턴스를 반환"""
    global _stream_manager

    if _stream_manager is None:
        with _manager_lock:
            if _stream_manager is None:
                from app.core.config import settings
                _stream_manager = StreamManager(
                    default_target_host=settings.AI_INFERENCE_HOST or "127.0.0.1",
                    default_target_port=settings.AI_INFERENCE_UDP_PORT,
                    default_fps=settings.STREAM_FPS,
                )

    return _stream_manager
