from __future__ import annotations

from typing import Any
import httpx
from app.core.config import settings

class AIClientError(RuntimeError):
    pass

class AIClient:
    def __init__(self) -> None:
        if not settings.AI_BASE_URL:
            raise AIClientError("AI_BASE_URL is not set")
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.ai_key = settings.AI_ADMIN_KEY

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.ai_key:
            h["X-AI-KEY"] = self.ai_key
        return h

    def infer_tray(self, payload: dict[str, Any], timeout_s: float = 10.0) -> dict[str, Any]:
        url = f"{self.base_url}/infer/tray"
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise AIClientError(f"AI infer_tray failed: {e}") from e

    def infer_cctv(self, payload: dict[str, Any], timeout_s: float = 20.0) -> dict[str, Any]:
        url = f"{self.base_url}/infer/cctv"
        try:
            with httpx.Client(timeout=timeout_s) as c:
                r = c.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise AIClientError(f"AI infer_cctv failed: {e}") from e
