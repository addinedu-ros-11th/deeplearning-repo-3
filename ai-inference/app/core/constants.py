"""
AI Inference engine에 사용하는 환경 변수
모든 매직 넘버와 설정 값은 여기에 정의되어야 합니다.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class KNNConfig:
    """K-Nearest Neighbors configuration"""
    TOP_K: int = 5
    UNKNOWN_DISTANCE_THRESHOLD: float = 0.5
    MARGIN_THRESHOLD: float = 0.04


@dataclass(frozen=True)
class YOLOConfig:
    """YOLO model configuration"""
    IMAGE_SIZE: int = 640
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.7


@dataclass(frozen=True)
class EmbeddingConfig:
    """Embedding model configuration"""
    IMAGE_SIZE: int = 224
    RESNET_OUTPUT_DIM: int = 2048
    NORMALIZE_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    NORMALIZE_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)


@dataclass(frozen=True)
class CCTVConfig:
    """CCTV inference configuration"""
    ROLLING_BUFFER_SECONDS: int = 10
    CLIP_DURATION_SECONDS: int = 5
    VIOLENCE_FRAME_INTERVAL: int = 3
    SKIP_FRAMES_AFTER_DETECTION: int = 10
    CHUNK_SIZE: int = 100
    DEFAULT_FPS: int = 30


@dataclass(frozen=True)
class VideoEncodingConfig:
    """Video encoding configuration"""
    CODEC: str = 'mp4v'
    H264_PRESET: str = 'fast'
    H264_CRF: int = 23
    MAX_UPLOAD_WAIT_SECONDS: int = 60


@dataclass(frozen=True)
class APITimeoutConfig:
    """API timeout configuration"""
    DEFAULT_TIMEOUT_SECONDS: float = 3.0
    PROTOTYPE_FETCH_TIMEOUT_SECONDS: float = 3.0
    HTTP_DOWNLOAD_TIMEOUT_SECONDS: int = 15

KNN_CONFIG = KNNConfig()
YOLO_CONFIG = YOLOConfig()
EMBEDDING_CONFIG = EmbeddingConfig()
CCTV_CONFIG = CCTVConfig()
VIDEO_ENCODING_CONFIG = VideoEncodingConfig()
API_TIMEOUT_CONFIG = APITimeoutConfig()