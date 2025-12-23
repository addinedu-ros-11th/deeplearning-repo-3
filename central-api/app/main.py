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

    @app.get("/")
    def root():
        return {
            "service": "bake-sight-central",
            "ok": True,
            "docs": "/docs",
            "api_base": "/api/v1",
        }

    # ✅ 헬스체크: 로드밸런서/모니터링/팀 디버깅용
    @app.get("/health")
    def health():
        return {"status": "healthy"}

    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()
