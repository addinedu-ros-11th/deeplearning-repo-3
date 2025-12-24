from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    AI_ADMIN_KEY: str
    AI_MOCK_MODE: int = 1

    CENTRAL_BASE_URL: str | None = None
    CENTRAL_ADMIN_KEY: str | None = None

    PROTOTYPE_INDEX_PATH: str | None = None
    PROTOTYPE_INDEX_GCS_URI: str | None = None

    CACHE_DIR: str = "/opt/ai-inference/cache"

    # Model artifacts
    YOLO_MODEL_PATH: str | None = None          # 예: /opt/models/yolo8s-seg.pt
    YOLO_MODEL_GCS_URI: str | None = None
    EMBED_MODEL_NAME: str = "resnet50"          # 일단 고정
    EMBED_DEVICE: str = "cuda"                  # cuda 또는 cpu

    # Thresholds
    YOLO_CONF_TH: float = 0.25
    YOLO_IOU_TH: float = 0.5
    TOPK: int = 5
    MARGIN_TH: float = 0.03                     # AUTO/REVIEW 경계
    UNKNOWN_DIST_TH: float = 0.35               # UNKNOWN 판단(예시는 임의, 데이터로 튜닝)
    OVERLAP_BLOCK_TH: float = 0.25              # 인스턴스 overlap 차단

settings = Settings()
