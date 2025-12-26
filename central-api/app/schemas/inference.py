from pydantic import BaseModel, Field, model_validator
from typing import Any

class InferTrayRequest(BaseModel):
    """
    Central -> AI 요청 payload (Demo v2).
    트레이 감지 후 2초 안정화 뒤 단일 프레임 1장으로 판단.
    - frame_b64: base64-encoded image bytes (jpeg/png) 1장
    - frame_gcs_uri: AI가 GCS에서 직접 읽도록 URI 1개
    하위호환: frames_b64 / frames_gcs_uris 를 보내면 len==1일 때만 허용.
    """
    # v2 (권장)
    frame_b64: str | None = None
    frame_gcs_uri: str | None = None

    # legacy (하위호환)
    frames_b64: list[str] | None = None
    frames_gcs_uris: list[str] | None = None

    device_code: str | None = None
    store_code: str | None = None

    @model_validator(mode="after")
    def _validate_single_frame(self):
        # legacy -> v2로 승격
        if self.frame_b64 is None and self.frames_b64:
            if len(self.frames_b64) != 1:
                raise ValueError("frames_b64 must contain exactly 1 frame (single-frame mode)")
            self.frame_b64 = self.frames_b64[0]

        if self.frame_gcs_uri is None and self.frames_gcs_uris:
            if len(self.frames_gcs_uris) != 1:
                raise ValueError("frames_gcs_uris must contain exactly 1 uri (single-frame mode)")
            self.frame_gcs_uri = self.frames_gcs_uris[0]

        # 둘 중 하나는 있어야 함
        if not self.frame_b64 and not self.frame_gcs_uri:
            raise ValueError("Either frame_b64 or frame_gcs_uri is required")

        # 동시에 보내면 모호하니 금지(원하면 우선순위로 처리 가능)
        if self.frame_b64 and self.frame_gcs_uri:
            raise ValueError("Provide only one of frame_b64 or frame_gcs_uri")

        return self


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
