"""
CCTV 추론 관련 함수.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np

from app.core.config import settings
from app.core.constants import CCTV_CONFIG
from app.services.video_processor import create_event_clip, ensure_dir


class EventType(Enum):
    """Types of detectable events."""
    VIOLENCE = "violence"
    FALL = "fall_down"
    AUXILIARY = "auxiliary"


@dataclass
class DetectionResult:
    """Result of event detection."""
    detected: bool
    confidence: float
    frame_idx: Optional[int]
    extra_meta: dict


@dataclass
class EventInferenceResult:
    """Result of event inference including clip path."""
    detected: bool
    confidence: float
    local_clip_path: Optional[str]
    extra_meta: dict

    def to_dict(self, result_key: str = "detected") -> dict[str, Any]:
        """Convert to dictionary with custom result key."""
        return {
            result_key: self.detected,
            "confidence": self.confidence,
            "local_clip_path": self.local_clip_path,
            "extra_meta": self.extra_meta,
        }


class BaseEventDetector(ABC):
    """Abstract base class for event detectors."""

    def __init__(
        self,
        event_type: EventType,
        clip_dir_name: str,
        skip_frames_multiplier: int = CCTV_CONFIG.SKIP_FRAMES_AFTER_DETECTION,
    ):
        self.event_type = event_type
        self.clip_dir_name = clip_dir_name
        self.skip_frames_multiplier = skip_frames_multiplier

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> dict[str, Any]:
        """Process a single frame and return detection result."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset detector state."""
        pass

    @abstractmethod
    def is_detected(self, result: dict[str, Any]) -> bool:
        """Check if detection occurred based on frame result."""
        pass

    @abstractmethod
    def get_confidence(self, result: dict[str, Any]) -> float:
        """Extract confidence from frame result."""
        pass


def run_event_inference(
    detector: BaseEventDetector,
    frames: list[np.ndarray],
    fps: int,
    width: int,
    height: int,
    now: datetime,
    frame_interval: int = 1,
    result_key: str = "detected",
) -> dict[str, Any]:
    """이벤트에 따른 영상 클립 생성"""
    detector.reset()

    detected = False
    detected_frame = None
    confidence = 0.0
    skip_frames = 0

    for i, frame in enumerate(frames):
        if skip_frames > 0:
            skip_frames -= 1
            continue

        if frame_interval > 1 and i % frame_interval != 0:
            continue

        result = detector.process_frame(frame)

        if detector.is_detected(result) and not detected:
            detected = True
            detected_frame = i
            confidence = detector.get_confidence(result)
            skip_frames = fps * detector.skip_frames_multiplier

    if not detected:
        return {
            result_key: False,
            "confidence": 0.0,
            "local_clip_path": None,
            "extra_meta": {},
        }

    # Create clip
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    local_clip_dir = os.path.join(settings.CACHE_DIR, f"{detector.clip_dir_name}_clips")
    ensure_dir(local_clip_dir)
    local_clip_path = os.path.join(
        local_clip_dir,
        f"cctv_{detector.clip_dir_name}_{timestamp}.mp4"
    )

    clip_path = create_event_clip(
        frames=frames,
        detection_frame_idx=detected_frame,
        fps=fps,
        width=width,
        height=height,
        output_path=local_clip_path,
    )

    return {
        result_key: True,
        "confidence": confidence,
        "local_clip_path": clip_path,
        "extra_meta": {"source": "shared_frames"},
    }


def run_violence_inference(
    classifier,
    frames: list[np.ndarray],
    fps: int,
    width: int,
    height: int,
    now: datetime,
) -> dict[str, Any]:
    """폭행 여부 감지"""
    classifier._reset()

    probabilities = []
    violence_detected = False
    violence_frame = None
    frame_interval = CCTV_CONFIG.VIOLENCE_FRAME_INTERVAL

    for i, frame in enumerate(frames):
        if i % frame_interval != 0:
            continue

        result = classifier.process_frame(frame)
        if result.get("ready"):
            prob = result.get("probability", 0.0)
            probabilities.append(prob)
            if prob >= classifier.threshold and not violence_detected:
                violence_detected = True
                violence_frame = i

    if not probabilities:
        return {
            "is_violence": False,
            "confidence": 0.0,
            "local_clip_path": None,
            "extra_meta": {},
        }

    if not violence_detected:
        return {
            "is_violence": False,
            "confidence": 0.0,
            "local_clip_path": None,
            "extra_meta": {},
        }

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    local_clip_dir = os.path.join(settings.CACHE_DIR, "violence_clips")
    ensure_dir(local_clip_dir)
    local_clip_path = os.path.join(local_clip_dir, f"cctv_violence_{timestamp}.mp4")

    clip_path = create_event_clip(
        frames=frames,
        detection_frame_idx=violence_frame,
        fps=fps,
        width=width,
        height=height,
        output_path=local_clip_path,
    )

    violence_count = sum(1 for p in probabilities if p >= classifier.threshold)
    return {
        "is_violence": True,
        "confidence": float(max(probabilities)),
        "local_clip_path": clip_path,
        "extra_meta": {
            "source": "shared_frames",
            "avg_probability": float(np.mean(probabilities)),
            "violence_ratio": float(violence_count / len(probabilities)),
        },
    }


def run_simple_inference(
    detector,
    frames: list[np.ndarray],
    fps: int,
    width: int,
    height: int,
    now: datetime,
    event_type: str,
    detection_key: str,
    result_key: str,
    confidence_key: str = "confidence",
    default_confidence: float = 1.0,
) -> dict[str, Any]:
    """낙상, 이동약자 감지"""
    detected = False
    detected_frame = None
    confidence = default_confidence
    skip_frames = 0

    for i, frame in enumerate(frames):
        if skip_frames > 0:
            skip_frames -= 1
            continue

        result = detector.process_frame(frame)

        if result.get(detection_key) and not detected:
            detected = True
            detected_frame = i
            confidence = result.get(confidence_key, default_confidence)
            skip_frames = fps * CCTV_CONFIG.SKIP_FRAMES_AFTER_DETECTION

    if not detected:
        return {
            result_key: False,
            "confidence": 0.0,
            "local_clip_path": None,
            "extra_meta": {},
        }

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    local_clip_dir = os.path.join(settings.CACHE_DIR, f"{event_type}_clips")
    ensure_dir(local_clip_dir)
    local_clip_path = os.path.join(local_clip_dir, f"cctv_{event_type}_{timestamp}.mp4")

    clip_path = create_event_clip(
        frames=frames,
        detection_frame_idx=detected_frame,
        fps=fps,
        width=width,
        height=height,
        output_path=local_clip_path,
    )

    return {
        result_key: True,
        "confidence": confidence,
        "local_clip_path": clip_path,
        "extra_meta": {"source": "shared_frames"},
    }
