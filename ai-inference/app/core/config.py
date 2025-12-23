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

settings = Settings()
