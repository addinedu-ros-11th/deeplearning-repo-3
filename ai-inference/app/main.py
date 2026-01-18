import logging
import sys

uvicorn_logger = logging.getLogger("uvicorn")

def setup_logging():
    if uvicorn_logger.handlers:
        handler = uvicorn_logger.handlers[0]
    else:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s - %(message)s"))

    for logger_name in ["scanner", "cctv", "udp_receiver", "stream_sender", "app"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            logger.addHandler(handler)
        logger.propagate = False  # 중복 방지

    # httpx 로거 비활성화
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


setup_logging()

print("=== AI Inference main.py 로드됨 ===", flush=True)
logging.getLogger("scanner").info("=== AI Inference 모듈 로드됨 ===")

from fastapi import FastAPI

from app.api import router, engine
from app.core.config import settings

def _start_worker_in_background() -> None:
    # lazy import to avoid cyclic imports
    import threading
    from app.worker import run_worker_loop

    t = threading.Thread(target=run_worker_loop, args=(engine,), name="central-job-worker", daemon=True)
    t.start()

def create_app() -> FastAPI:
    app = FastAPI(title="Bake Sight AI Inference", version="0.1.0")
    app.include_router(router)

    @app.on_event("startup")
    def _startup():
        engine.startup_load()
        if settings.AI_WORKER_MODE:
            _start_worker_in_background()

        if settings.UDP_RECEIVER_ENABLED:
            engine.startup_udp_receiver()

    @app.on_event("shutdown")
    def _shutdown():
        logging.info("AI Inference 서버 종료 중...")
        engine.shutdown_udp_receiver()

    return app

app = create_app()
