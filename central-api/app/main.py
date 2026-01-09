from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import api_router
from app.db.session import engine
from sqlalchemy import text

def create_app() -> FastAPI:
    app = FastAPI(
        title="Bake-Sight API",
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS 설정 (dashboard 연결용)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root():
        return {
            "service": "bake-sight-central",
            "ok": True,
            "docs": "/docs",
            "api_base": "/api/v1",
        }

    @app.get("/health")
    def health():
        # 프로세스 살아있음(가벼운 체크)
        return {"status": "healthy"}

    @app.get("/ready")
    def ready():
        # 의존성 준비상태 체크(DB 최소 ping)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

        return {"ready": db_ok}

    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_app()
