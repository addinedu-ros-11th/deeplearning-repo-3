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
        self.base = settings.CENTRAL_BASE_URL.rstrip("/")
        self.key = settings.CENTRAL_ADMIN_KEY

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.key:
            h["X-ADMIN-KEY"] = self.key
        return h

    def fetch_active_prototypes(self, timeout_s: float = 10.0) -> list[dict[str, Any]]:
        url = f"{self.base}/api/v1/prototypes/active"
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise CentralClientError(f"fetch_active_prototypes failed: {e}") from e
