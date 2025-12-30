from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Any


class TrayInferRequest(BaseModel):
    # Central 업로드 및 로컬 저장/추적에 필요
    session_uuid: str
    attempt_no: int = Field(ge=1, le=3)

    store_code: str
    device_code: str

    # 단일 프레임(1장)만 허용
    frame_b64: str

    @model_validator(mode="after")
    def _validate(self):
        # 빈 문자열 방지
        if not self.frame_b64 or not self.frame_b64.strip():
            raise ValueError("frame_b64 is required")
        return self


class TrayInferResponse(BaseModel):
    overlap_score: float | None = None
    decision: str = Field(..., description="AUTO/REVIEW/UNKNOWN")
    result_json: dict[str, Any]


class CctvInferRequest(BaseModel):
    store_code: str
    device_code: str

    # 데모에서는 둘 중 하나만 쓰도록(원하면 더 축소 가능)
    clip_gcs_uri: str | None = None
    frames_b64: list[str] | None = None

    @model_validator(mode="after")
    def _validate(self):
        if not self.clip_gcs_uri and not self.frames_b64:
            raise ValueError("Either clip_gcs_uri or frames_b64 is required")
        if self.clip_gcs_uri and self.frames_b64:
            raise ValueError("Provide only one of clip_gcs_uri or frames_b64")
        return self


class CctvInferResponse(BaseModel):
    events: list[dict[str, Any]]
