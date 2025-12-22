from pydantic import BaseModel, Field
from typing import Any

class InferTrayRequest(BaseModel):
    """
    Central -> AI 요청 payload.
    frames_b64: base64-encoded image bytes (jpeg/png). 2~5장 권장.
    또는 frames_gcs_uris: AI가 GCS에서 직접 읽도록 URI 전달.
    """
    frames_b64: list[str] | None = None
    frames_gcs_uris: list[str] | None = None
    device_code: str | None = None
    store_code: str | None = None

class InferTrayResponse(BaseModel):
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
