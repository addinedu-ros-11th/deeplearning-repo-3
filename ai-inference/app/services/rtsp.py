from __future__ import annotations
from typing import Iterator
import cv2

def iter_frames(rtsp_uri: str, max_frames: int = 5, stride: int = 5) -> Iterator:
    """RTSP 스트림에서 프레임 샘플링(스켈레톤)."""
    cap = cv2.VideoCapture(rtsp_uri)
    try:
        i = 0
        yielded = 0
        while yielded < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if i % stride == 0:
                yield frame
                yielded += 1
            i += 1
    finally:
        cap.release()
