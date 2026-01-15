"""
CCTV 추론을 위한 비디오 처리 유틸리티.
"""
from __future__ import annotations

import logging
import os
import subprocess
from typing import Any

import cv2
import numpy as np

from app.core.constants import CCTV_CONFIG, VIDEO_ENCODING_CONFIG


def ensure_dir(path: str) -> None:
    """디렉토리가 존재하지 않으면 생성합니다."""
    os.makedirs(path, exist_ok=True)


def create_event_clip(
    frames: list[np.ndarray],
    detection_frame_idx: int,
    fps: int,
    width: int,
    height: int,
    output_path: str,
    clip_seconds: int = CCTV_CONFIG.CLIP_DURATION_SECONDS,
) -> str | None:
    """
    감지 지점 주변의 비디오 클립을 생성합니다.

    Args:
        frames: 비디오 프레임 목록
        detection_frame_idx: 감지가 발생한 프레임 인덱스
        fps: 초당 프레임 수
        width: 프레임 너비
        height: 프레임 높이
        output_path: 클립의 출력 파일 경로
        clip_seconds: 감지 지점 전후 지속 시간

    Returns:
        생성된 클립의 경로, 실패 시 None
    """
    if not frames or detection_frame_idx is None:
        return None

    start_frame = max(0, detection_frame_idx - clip_seconds * fps)
    end_frame = min(len(frames), detection_frame_idx + clip_seconds * fps)

    if start_frame >= end_frame:
        return None

    # 출력 디렉토리 생성
    ensure_dir(os.path.dirname(output_path))

    # mp4v 코덱으로 임시 파일 작성
    temp_path = output_path.replace('.mp4', '_temp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*VIDEO_ENCODING_CONFIG.CODEC)
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

    for f in frames[start_frame:end_frame]:
        out.write(f)
    out.release()

    # 브라우저 호환성을 위해 ffmpeg로 H.264 변환
    result = subprocess.run([
        'ffmpeg', '-y', '-i', temp_path,
        '-c:v', 'libx264',
        '-preset', VIDEO_ENCODING_CONFIG.H264_PRESET,
        '-crf', str(VIDEO_ENCODING_CONFIG.H264_CRF),
        output_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"ffmpeg conversion failed: {result.stderr}")
        if os.path.exists(temp_path):
            os.rename(temp_path, output_path)
    else:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return output_path if os.path.exists(output_path) else None


def encode_clip_sync(
    frames: list[np.ndarray],
    fps: int,
    width: int,
    height: int,
    output_path: str,
) -> str:
    """
    프레임을 비디오 클립으로 동기 인코딩합니다.

    Args:
        frames: 비디오 프레임 목록
        fps: 초당 프레임 수
        width: 프레임 너비
        height: 프레임 높이
        output_path: 출력 파일 경로

    Returns:
        생성된 클립의 경로
    """
    ensure_dir(os.path.dirname(output_path))

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
        logging.error(f"ffmpeg conversion failed: {result.stderr}")
        if os.path.exists(temp_path):
            os.rename(temp_path, output_path)
    else:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return output_path


def get_video_info(path: str) -> tuple[int, int, int, int]:
    """
    비디오 메타데이터를 조회합니다.

    Args:
        path: 비디오 파일 경로

    Returns:
        (fps, width, height, total_frames) 튜플
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return CCTV_CONFIG.DEFAULT_FPS, 0, 0, 0

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or CCTV_CONFIG.DEFAULT_FPS
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    return fps, width, height, total_frames


def decode_video(path: str) -> tuple[list, int, int, int]:
    """
    전체 비디오를 프레임 목록으로 디코딩합니다.

    Args:
        path: 비디오 파일 경로

    Returns:
        (frames, fps, width, height) 튜플
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return [], CCTV_CONFIG.DEFAULT_FPS, 0, 0

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or CCTV_CONFIG.DEFAULT_FPS
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    return frames, fps, width, height


def iter_video_chunks(path: str, chunk_size: int = CCTV_CONFIG.CHUNK_SIZE):
    """
    메모리 사용량을 최소화하기 위해 비디오를 청크 단위로 스트리밍합니다.

    Args:
        path: 비디오 파일 경로
        chunk_size: 청크당 프레임 수

    Yields:
        (chunk_frames, start_index, fps, width, height) 튜플
    """
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
