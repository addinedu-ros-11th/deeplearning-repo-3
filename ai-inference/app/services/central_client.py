from __future__ import annotations

from typing import Any
import httpx
from app.core.config import settings


class CentralClientError(RuntimeError):
    pass


class CentralClient:
    """Central(Cloud Run) API 호출용 클라이언트.

    - JOB Claim/Complete: Central이 Orchestrator
    - 모든 요청은 ADMIN_KEY 헤더로 보호(데모 정책)
    """
    def __init__(self) -> None:
        if not settings.CENTRAL_BASE_URL:
            raise CentralClientError("CENTRAL_BASE_URL is not set")
        if not settings.CENTRAL_ADMIN_KEY:
            raise CentralClientError("CENTRAL_ADMIN_KEY is not set")

        self.base = settings.CENTRAL_BASE_URL.rstrip("/")
        self.key = settings.CENTRAL_ADMIN_KEY

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.key:
            h["X-ADMIN-KEY"] = self.key
        return h

    def claim_tray_job(self, worker_id: str, timeout_s: float = 10.0) -> dict[str, Any] | None:
        """PENDING -> CLAIMED 갱신 후 1건 반환.
        Central 응답 형태(권장):
          - {"job": {...}}  또는  {"job": null}
        
        반환:
          - job dict
          - 없으면 None (HTTP 204)
        """
        url = f"{self.base}/api/v1/inference/tray/jobs/claim"
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.post(url, headers=self._headers(), json={"worker_id": worker_id})
            if r.status_code == 204:
                return None
            r.raise_for_status()
            return r.json()

            # 표준: {"job": ...}
            if isinstance(data, dict) and "job" in data:
                job = data.get("job")
                return job if isinstance(job, dict) else None

            # 하위호환: job dict를 바로 반환하는 구현
            return data if isinstance(data, dict) else None            
        except Exception as e:
            raise CentralClientError(f"claim_tray_job failed: {e}") from e

    def complete_tray_job(
        self,
        job_id: int,
        decision: str,
        overlap_score: float | None,
        result_json: dict[str, Any],
        error: str | None = None,
        timeout_s: float = 15.0,
    ) -> dict[str, Any]:
        url = f"{self.base}/api/v1/inference/tray/jobs/{job_id}/complete"
        payload: dict[str, Any] = {
            "decision": decision,
            "overlap_score": overlap_score,
            "result_json": result_json,
            "error": error,
        }
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.post(url, headers=self._headers(), json=payload)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise CentralClientError(f"complete_tray_job failed: {e}") from e

    def get_active_prototype_set(self, timeout_s: float = 10.0) -> dict[str, Any]:
        """ACTIVE prototype_set 조회.

        Central 응답 예:
        {
          "prototype_set_id": 1,
          "status": "ACTIVE",
          "index_npy_gcs_uri": "gs://.../prototype_index.npy",
          "index_meta_gcs_uri": "gs://.../prototype_index.json",
          "notes": "...",
          "created_at": "..."
        }
        """
        url = f"{self.base}/api/v1/prototypes/active"
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.get(url, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, dict):
                raise CentralClientError("active prototype_set response is not a dict")
            return data
        except Exception as e:
            raise CentralClientError(f"get_active_prototype_set failed: {e}") from e


    def list_stores(self, timeout_s: float = 10.0) -> list[dict[str, Any]]:
        url = f"{self.base}/api/v1/stores"
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.get(url, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            raise CentralClientError(f"list_stores failed: {e}") from e

    def list_devices(self, store_code: str, *, type: str | None = None, timeout_s: float = 10.0) -> list[dict[str, Any]]:
        url = f"{self.base}/api/v1/stores/{store_code}/devices"
        params = {}
        if type:
            params["type"] = type
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.get(url, headers=self._headers(), params=params)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            raise CentralClientError(f"list_devices failed: {e}") from e