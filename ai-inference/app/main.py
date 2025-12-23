from fastapi import FastAPI
from app.api import router, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Bake Sight AI Inference", version="0.1.0")
    app.include_router(router)

    @app.on_event("startup")
    def _startup():
        engine.startup_load()

    return app

app = create_app()
