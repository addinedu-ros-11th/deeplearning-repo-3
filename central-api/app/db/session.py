import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def _int_env(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default

# Cloud Run/서버리스에서 DB 커넥션 폭주를 막기 위해 보수적인 풀 기본값 사용
POOL_SIZE = _int_env("DB_POOL_SIZE", 5)
MAX_OVERFLOW = _int_env("DB_MAX_OVERFLOW", 2)
POOL_RECYCLE = _int_env("DB_POOL_RECYCLE", 1800)  # seconds

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
