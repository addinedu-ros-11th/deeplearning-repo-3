from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from typing import Any

class TrayInferRequest(BaseModel):
    session_uuid: str | None = None
    attempt_no: int | None = Field(default=None, ge=1, le=3)

    store_code: str | None = None
    device_code: str | None = None

    frame_b64: str | None = None
    frame_gcs_uri: str | None = None

    @model_validator(mode="after")
    def _validate(self):
        if not self.frame_b64 and not self.frame_gcs_uri:
            raise ValueError("Either frame_b64 or frame_gcs_uri is required")
        if self.frame_b64 and self.frame_gcs_uri:
            raise ValueError("Provide only one of frame_b64 or frame_gcs_uri")
        return self
        
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
