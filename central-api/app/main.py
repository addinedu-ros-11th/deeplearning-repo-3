from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import api_router
from app.db.session import engine
from app.db.base import Base

def create_app() -> FastAPI:
    app = FastAPI(
        title="Bake-Sight API",
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def on_startup():
        # 데모 편의: 필요 시 테이블 자동 생성
        if settings.CREATE_TABLES:
            Base.metadata.create_all(bind=engine)

    return app

app = create_app()
