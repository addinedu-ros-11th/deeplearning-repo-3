"""
키오스크 UI를 위한 중앙화된 설정 상수.
모든 매직 넘버와 설정 값은 여기에 정의되어야 합니다.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class TrayDetectionConfig:
    """트레이 감지 설정"""
    STABLE_THRESHOLD: int = 50
    ROI_RATIO: Tuple[float, float, float, float] = (0.3, 0.3, 0.7, 0.7)  # (x1, y1, x2, y2)
    OVERLAP_THRESHOLD: float = 0.05
    BRIGHTNESS_THRESHOLD: int = 170
    CAPTURE_DELAY_MS: int = 2000


@dataclass(frozen=True)
class CameraConfig:
    """카메라 설정"""
    FRAME_RATE_MS: int = 33  # ~30fps
    WORKER_WAIT_TIMEOUT_MS: int = 2000
    WORKER_TERMINATE_TIMEOUT_MS: int = 1000


@dataclass(frozen=True)
class UIStyleConfig:
    """UI 스타일 상수"""
    PRIMARY_COLOR: str = "#FF6D1F"
    SECONDARY_COLOR: str = "#E6DABD"
    BACKGROUND_COLOR: str = "#F5E7C6"
    DISABLED_COLOR: str = "#cccccc"
    DISABLED_TEXT_COLOR: str = "#666666"
    BORDER_RADIUS: int = 30
    FONT_SIZE_LARGE: int = 80
    FONT_SIZE_MEDIUM: int = 50
    FONT_SIZE_SMALL: int = 36


@dataclass(frozen=True)
class DetectionOverlayConfig:
    """감지 결과 오버레이 설정"""
    COLOR_AUTO: Tuple[int, int, int] = (0, 255, 0)      # 초록색
    COLOR_REVIEW: Tuple[int, int, int] = (255, 165, 0)  # 주황색
    COLOR_UNKNOWN: Tuple[int, int, int] = (255, 0, 0)   # 빨간색
    FONT_SIZE: int = 24
    BOX_LINE_WIDTH: int = 3
    ALPHA: int = 128


# 쉬운 import를 위한 기본 인스턴스
TRAY_DETECTION_CONFIG = TrayDetectionConfig()
CAMERA_CONFIG = CameraConfig()
UI_STYLE_CONFIG = UIStyleConfig()
DETECTION_OVERLAY_CONFIG = DetectionOverlayConfig()
