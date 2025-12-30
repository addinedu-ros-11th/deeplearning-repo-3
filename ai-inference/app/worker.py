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
    """gs://... URI를 로컬에 다운로드 후 base64로 변환."""
    _ensure_cache_dir()
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    local = f"{settings.CACHE_DIR}/tray_{ts}.jpg"
    download_to(frame_gcs_uri, local)
    with open(local, "rb") as f:
        raw = f.read()
    return base64.b64encode(raw).decode("utf-8")


def _download_frame_as_base64(frame_gcs_uri: str) -> str:
    """gs://... URI를 로컬에 다운로드 후 base64로 변환."""
    _ensure_cache_dir()
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    local = f"{settings.CACHE_DIR}/tray_{ts}.jpg"
    download_to(frame_gcs_uri, local)
    with open(local, "rb") as f:
        raw = f.read()
    return base64.b64encode(raw).decode("utf-8")


def _resolve_store_code(
    client: CentralClient,
    store_id: int | None,
    cache_store_id_to_code: dict[int, str],
) -> str | None:
    if store_id is None:
        return None

    if store_id in cache_store_id_to_code:
        return cache_store_id_to_code.get(store_id)

    try:
        rows = client.list_stores(timeout_s=5.0)
        for r in rows:
            try:
                sid = int(r.get("store_id"))
                sc = str(r.get("store_code") or "").strip()
                if sid and sc:
                    cache_store_id_to_code[sid] = sc
            except Exception:
                continue
    except Exception:
        return None

    return cache_store_id_to_code.get(store_id)


def _resolve_device_code(
    client: CentralClient,
    store_code: str | None,
    device_id: int | None,
    cache_device_id_to_code: dict[int, str],
) -> str | None:
    if device_id is None:
        return None

    if device_id in cache_device_id_to_code:
        return cache_device_id_to_code.get(device_id)

    if not store_code:
        return None

    try:
        rows = client.list_devices(store_code, timeout_s=5.0)
        for r in rows:
            try:
                did = int(r.get("device_id"))
                dc = str(r.get("device_code") or "").strip()
                if did and dc:
                    cache_device_id_to_code[did] = dc
            except Exception:
                continue
    except Exception:
        return None

    return cache_device_id_to_code.get(device_id)

    
def _best_session_uuid(job: dict[str, Any]) -> str:
    # Central job response에 session_uuid가 없을 수 있으므로 fallback을 둠
    s = str(job.get("session_uuid") or "").strip()
    if s:
        return s

    sid = job.get("session_id")
    if sid is not None:
        return f"session-{sid}"

    jid = job.get("job_id")
    return f"job-{jid}" if jid is not None else "unknown-session"


def run_worker_loop(engine, *, once: bool = False) -> None:
    """Central Inference Job polling 루프.

    - Central에서 job claim
    - GCS에서 프레임 다운로드
    - engine.infer_tray 수행
    - Central로 complete
    """
    client = CentralClient()
    worker_id = settings.WORKER_ID

    # store/device code 캐시(요청 비용 절감)
    store_id_to_code: dict[int, str] = {}
    device_id_to_code: dict[int, str] = {}

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

        job_id = int(job.get("job_id") or 0)
        try:
            frame_gcs_uri = str(job.get("frame_gcs_uri") or "").strip()
            if not frame_gcs_uri:
                raise ValueError("frame_gcs_uri is missing")

            # engine이 요구하는 필드(session_uuid/store_code/device_code)를 확보
            session_uuid = _best_session_uuid(job)

            store_id = job.get("store_id")
            device_id = job.get("device_id")
            store_code = _resolve_store_code(client, int(store_id) if store_id is not None else None, store_id_to_code)
            device_code = _resolve_device_code(
                client,
                store_code,
                int(device_id) if device_id is not None else None,
                device_id_to_code,
            )

            # 데모 안전망: 빈 문자열이면 engine에서 ValueError가 나므로 placeholder 사용
            store_code = (store_code or "UNKNOWN")
            device_code = (device_code or "UNKNOWN")

            attempt_no = int(job.get("attempt_no") or 1)

            frame_b64 = _download_frame_as_base64(frame_gcs_uri)
            payload: dict[str, Any] = {
                "session_uuid": session_uuid,
                "attempt_no": attempt_no,
                "store_code": store_code,
                "device_code": device_code,
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
                error=None,
            )
        except Exception as e:
            # 실패 시: job을 FAILED로 마킹하고 error 저장
            try:
                client.complete_tray_job(
                    job_id=job_id,
                    decision="UNKNOWN",
                    overlap_score=None,
                    result_json={"error": "worker_exception"},
                    error=str(e),
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
