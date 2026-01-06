from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # DB
    DATABASE_URL: str

    # Admin auth for Central API
    ADMIN_KEY: str

    # Optional: Central -> AI Inference (Compute Engine VM)
    AI_BASE_URL: str | None = None          # 예: http://10.10.0.10:9000
    AI_ADMIN_KEY: str | None = None         # AI 서버 보호용 키 (X-AI-KEY)

    # Optional: GCS buckets (frames/clips/models)
    GCS_BUCKET_TRAY: str | None = None
    GCS_BUCKET_CCTV: str | None = None
    GCS_BUCKET_MODELS: str | None = None

    GOOGLE_APPLICATION_CREDENTIALS: str | None = None

    # Demo convenience
    CREATE_TABLES: int = 0  # 1이면 startup에서 create_all

settings = Settings()
