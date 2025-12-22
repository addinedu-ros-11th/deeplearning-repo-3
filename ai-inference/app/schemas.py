from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any

class TrayInferRequest(BaseModel):
    session_uuid: str | None = None
    frames_b64: list[str] | None = None
    frames_gcs_uris: list[str] | None = None
    store_code: str | None = None
    device_code: str | None = None

class TrayInferResponse(BaseModel):
    overlap_score: float | None = None
    decision: str = Field(..., description="AUTO/REVIEW/UNKNOWN")
    result_json: dict[str, Any]

class CctvInferRequest(BaseModel):
    store_code: str | None = None
    device_code: str | None = None
    clip_gcs_uri: str | None = None
    frames_b64: list[str] | None = None

class CctvInferResponse(BaseModel):
    events: list[dict[str, Any]]
