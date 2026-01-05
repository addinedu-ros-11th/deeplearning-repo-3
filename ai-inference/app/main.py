from fastapi import FastAPI

from app.api import router, engine
from app.core.config import settings

def _start_worker_in_background() -> None:
    # lazy import to avoid cyclic imports
    import threading
    from app.worker import run_worker_loop

    t = threading.Thread(target=run_worker_loop, name="central-job-worker", daemon=True)
    t.start()

def create_app() -> FastAPI:
    app = FastAPI(title="Bake Sight AI Inference", version="0.1.0")
    app.include_router(router)

    @app.on_event("startup")
    def _startup():
        engine.startup_load()
        if settings.AI_WORKER_MODE:
            _start_worker_in_background()

    return app

app = create_app()
