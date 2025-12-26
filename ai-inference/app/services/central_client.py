from __future__ import annotations

from typing import Any
import httpx
from app.core.config import settings


class CentralClientError(RuntimeError):
    pass


class CentralClient:
    def __init__(self) -> None:
        if not settings.CENTRAL_BASE_URL:
            raise CentralClientError("CENTRAL_BASE_URL is not set")
        if not settings.CENTRAL_ADMIN_KEY:
            raise CentralClientError("CENTRAL_ADMIN_KEY is not set")

        self.base = settings.CENTRAL_BASE_URL.rstrip("/")
        self.key = settings.CENTRAL_ADMIN_KEY

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "X-ADMIN-KEY": self.key}

    def ensure_tray_session(
        self,
        *,
        session_uuid: str,
        store_id: int,
        checkout_device_id: int,
        attempt_limit: int = 3,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        """
        Central에 tray_session이 없으면 생성. 있으면 그대로 반환.
        전제: Central에 'GET /api/v1/tray-sessions/by-uuid/{uuid}' 같은 엔드포인트가 없으면,
              일단 create를 호출하고 409(중복)면 조회로 fallback 해야 함.
        현재 스켈레톤에서는 간단히:
          - POST로 생성 시도
          - 409면 다시 GET(별도 엔드포인트 필요) 대신, Central이 409일 때 기존 row를 반환하도록 구현하는 게 가장 깔끔함.
        """
        url = f"{self.base}/api/v1/tray-sessions"
        payload = {
            "session_uuid": session_uuid,
            "store_id": store_id,
            "checkout_device_id": checkout_device_id,
            "attempt_limit": attempt_limit,
        }
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.post(url, headers=self._headers(), json=payload)
            # Central이 409를 쓰면 여기서 처리
            if r.status_code == 409:
                # Central에 by-uuid 조회 엔드포인트가 있으면 그걸 호출하도록 바꾸는 게 정석
                # 지금은 명확히 에러를 내서 "Central API를 맞추자"로 진행
                raise CentralClientError("tray_session already exists (409): add GET by uuid or return existing on 409")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise CentralClientError(f"ensure_tray_session failed: {e}") from e

    def create_recognition_run(
        self,
        *,
        session_uuid: str,
        attempt_no: int,
        overlap_score: float | None,
        decision: str,
        result_json: dict[str, Any],
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        url = f"{self.base}/api/v1/tray-sessions/{session_uuid}/infer"
        payload = {
            # Central route는 InferTrayRequest 기반으로 받는 게 깔끔함
            # 여기서는 ai-inference -> central 업로드용 payload
            "store_code": None,
            "device_code": None,
            "frame_b64": None,      # 이미지는 Central에 올리지 않는 정책(로컬 저장)으로 간다
            "frame_gcs_uri": None,  # GCS 안씀
            # 실제 run 생성은 Central이 내부적으로 attempt_no 계산하는 구조였는데,
            # 지금은 ai 쪽이 attempt_no를 알고 있으므로 Central이 body로 attempt_no를 받도록 바꾸는 걸 권장.
            "attempt_no": attempt_no,
            "overlap_score": overlap_score,
            "decision": decision,
            "result_json": result_json,
        }
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.post(url, headers=self._headers(), json=payload)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise CentralClientError(f"create_recognition_run failed: {e}") from e

    def ensure_open_review(
        self,
        *,
        session_uuid: str,
        reason: str,
        top_k_json: Any | None,
        confirmed_items_json: Any | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        """
        Central이 'review 생성'을 infer route 안에서 이미 하고 있으면 이 함수는 필요 없음.
        지금 Central inference 라우터는 REVIEW/UNKNOWN이면 review 생성 로직이 있었음.
        따라서 Step 3에서는 Central inference 라우터를 그대로 쓰되,
        이미지 없이도 run 저장 가능하도록 Central을 약간 고쳐야 함.
        """
        # Central이 inference route에서 review 생성한다면 여기서는 no-op
        return
