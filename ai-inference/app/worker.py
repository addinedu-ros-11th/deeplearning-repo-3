from __future__ import annotations

import base64
import os
import time
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.central_client import CentralClient, CentralClientError
from app.services.gcs_utils import download_to


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ensure_cache_dir() -> None:
    os.makedirs(settings.CACHE_DIR, exist_ok=True)


def _strip_data_url_prefix(b64: str) -> str:
    if b64 and b64.strip().startswith("data:") and "," in b64:
        return b64.split(",", 1)[1]
    return b64


def _download_frame_as_base64(frame_gcs_uri: str) -> str:
    """gs://... URI를 로컬에 다운로드 후 base64로 변환."""
    _ensure_cache_dir()
    ts = datetime.now(timezone.utc).timestamp()
    local = f"{settings.CACHE_DIR}/tray_{ts}.jpg"
    download_to(frame_gcs_uri, local)
    raw = open(local, "rb").read()
    return base64.b64encode(raw).decode("utf-8")


def run_worker_loop(engine, *, once: bool = False) -> None:
    """Central Inference Job polling 루프.

    - Central에서 job claim
    - GCS에서 프레임 다운로드
    - engine.infer_tray 수행
    - Central로 complete
    """
    client = CentralClient()
    worker_id = settings.WORKER_ID

    while True:
        try:
            job = client.claim_tray_job(worker_id=worker_id)
        except CentralClientError:
            time.sleep(settings.POLL_INTERVAL_S)
            if once:
                return
            continue

        if not job:
            time.sleep(settings.POLL_INTERVAL_S)
            if once:
                return
            continue

        job_id = int(job["job_id"])
        try:
            frame_b64 = _download_frame_as_base64(job["frame_gcs_uri"])
            payload: dict[str, Any] = {
                "session_uuid": job.get("session_uuid"),
                "attempt_no": job.get("attempt_no"),
                "store_code": job.get("store_code"),
                "device_code": job.get("device_code"),
                "frame_b64": frame_b64,
            }

            ai_resp = engine.infer_tray(payload)
            decision = str(ai_resp.get("decision") or "UNKNOWN")
            overlap_score = ai_resp.get("overlap_score")
            result_json = ai_resp.get("result_json") or {}

            client.complete_tray_job(
                job_id=job_id,
                decision=decision,
                overlap_score=overlap_score,
                result_json=result_json,
                error_message=None,
            )
        except Exception as e:
            # 실패 시: job을 FAILED로 마킹하고 error 저장
            try:
                client.complete_tray_job(
                    job_id=job_id,
                    decision="UNKNOWN",
                    overlap_score=None,
                    result_json={"error": "worker_exception"},
                    error_message=str(e),
                )
            except Exception:
                pass

        if once:
            return


def main() -> None:
    # 별도 프로세스로 worker만 띄우는 용도
    from app.services.engine import InferenceEngine

    eng = InferenceEngine()
    eng.startup_load()
    run_worker_loop(eng)


if __name__ == "__main__":
    main()
